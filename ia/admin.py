from django.contrib import admin
from django.template.response import TemplateResponse
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta, date
from django.utils.html import format_html
import time

from .models import PrediccionAdminEntry, ConsultaIA, ReporteGenerado
from compra.models import Compra
from .interprete import InterpretadorPrompt, GeneradorConsultas
from .generador_reportes import GeneradorReportes


@admin.register(PrediccionAdminEntry)
class PrediccionAdmin(admin.ModelAdmin):
	change_list_template = 'admin/ia/prediccion.html'
	# Evitar agregar/borrar/editar
	def has_add_permission(self, request):
		return False

	def has_change_permission(self, request, obj=None):
		return request.user.is_staff

	def has_delete_permission(self, request, obj=None):
		return False

	def changelist_view(self, request, extra_context=None):
		# Parámetros
		dias_hist = int(request.GET.get('dias_hist', 30) or 30)
		dias_forecast = int(request.GET.get('dias_forecast', 7) or 7)
		ventana = int(request.GET.get('ventana', 7) or 7)  # para media móvil

		hoy = timezone.now().date()
		inicio = hoy - timedelta(days=dias_hist)
		qs = (
			Compra.objects.filter(fecha__date__gte=inicio)
			.values('fecha__date')
			.annotate(total=Sum('total'))
		)
		# Series diarias completas (relleno con 0)
		historico = []
		tot_map = {r['fecha__date']: r['total'] or 0 for r in qs}
		for i in range(dias_hist + 1):
			d = inicio + timedelta(days=i)
			historico.append({'fecha': d, 'total': float(tot_map.get(d, 0))})

		# Predicción simple: media móvil de 'ventana' días
		forecast = []
		serie = [p['total'] for p in historico]
		for i in range(1, dias_forecast + 1):
			ventana_vals = serie[-ventana:] if len(serie) >= ventana else serie
			prom = sum(ventana_vals) / max(1, len(ventana_vals))
			forecast.append({'fecha': hoy + timedelta(days=i), 'total': round(prom, 2)})
			serie.append(prom)

		# KPIs rápidos
		historico_total = round(sum(p['total'] for p in historico), 2)
		historico_promedio = round((historico_total / max(1, len(historico))), 2)
		historico_ultimo_dia = round(historico[-1]['total'] if historico else 0, 2)
		forecast_total = round(sum(f['total'] for f in forecast), 2)
		forecast_promedio = round((forecast_total / max(1, len(forecast))), 2)

		# ¿Descarga CSV?
		if request.GET.get('download') == 'csv':
			import csv
			response = HttpResponse(content_type='text/csv; charset=utf-8')
			response['Content-Disposition'] = 'attachment; filename="prediccion_ventas.csv"'
			writer = csv.writer(response)
			writer.writerow(['tipo', 'fecha', 'total'])
			for p in historico:
				writer.writerow(['historico', p['fecha'].isoformat(), p['total']])
			for f in forecast:
				writer.writerow(['forecast', f['fecha'].isoformat(), f['total']])
			return response

		context = {
			'title': '',
			'historico': historico,
			'forecast': forecast,
			'historico_total': historico_total,
			'historico_promedio': historico_promedio,
			'historico_ultimo_dia': historico_ultimo_dia,
			'forecast_total': forecast_total,
			'forecast_promedio': forecast_promedio,
			'dias_hist': dias_hist,
			'dias_forecast': dias_forecast,
			'ventana': ventana,
			'opts': self.model._meta,
			'app_label': self.model._meta.app_label,
		}
		context.update(extra_context or {})
		return TemplateResponse(request, self.change_list_template, context)


@admin.register(ConsultaIA)
class ConsultaIAAdmin(admin.ModelAdmin):
	list_display = ['id', 'usuario', 'prompt_corto', 'formato_badge', 'resultado_badge', 'fecha_consulta', 'tiempo_ejecucion']
	list_filter = ['formato_salida', 'fecha_consulta', 'usuario']
	search_fields = ['prompt', 'sql_generado']
	readonly_fields = ['usuario', 'prompt', 'prompt_interpretado', 'sql_generado', 'resultado', 'error', 'fecha_consulta', 'tiempo_ejecucion']
	date_hierarchy = 'fecha_consulta'
	
	def has_add_permission(self, request):
		return False
	
	def prompt_corto(self, obj):
		return obj.prompt[:80] + '...' if len(obj.prompt) > 80 else obj.prompt
	prompt_corto.short_description = 'Consulta'
	
	def formato_badge(self, obj):
		colores = {
			'pantalla': '#3498db',
			'pdf': '#e74c3c',
			'excel': '#27ae60',
			'csv': '#f39c12',
		}
		return format_html(
			'<span style="background:{}; color:white; padding:3px 8px; border-radius:3px; font-size:11px;">{}</span>',
			colores.get(obj.formato_salida, '#95a5a6'),
			obj.formato_salida.upper()
		)
	formato_badge.short_description = 'Formato'
	
	def resultado_badge(self, obj):
		if obj.error:
			return format_html('<span style="color:#e74c3c;">✗ Error</span>')
		elif obj.resultado:
			cantidad = len(obj.resultado.get('datos', []))
			return format_html('<span style="color:#27ae60;">✓ {} registros</span>', cantidad)
		return format_html('<span style="color:#95a5a6;">-</span>')
	resultado_badge.short_description = 'Estado'


@admin.register(ReporteGenerado)
class ReporteGeneradoAdmin(admin.ModelAdmin):
	change_list_template = 'admin/ia/generar_reporte.html'
	
	def has_add_permission(self, request):
		return False
	
	def has_change_permission(self, request, obj=None):
		return request.user.is_staff
	
	def has_delete_permission(self, request, obj=None):
		return False
	
	def changelist_view(self, request, extra_context=None):
		"""Vista para generar reportes con IA"""
		
		if request.method == 'POST':
			prompt = request.POST.get('prompt', '').strip()
			
			# Validación básica
			if not prompt:
				context = {
					'error': '⚠️ Por favor ingrese una consulta',
					'title': 'Generar Reporte con IA',
					'opts': self.model._meta,
					'app_label': self.model._meta.app_label,
				}
				return TemplateResponse(request, self.change_list_template, context)
			
			# Validación de longitud
			if len(prompt) < 10:
				context = {
					'error': '⚠️ La consulta es muy corta. Sé más específico. Ejemplo: "Ventas del mes de octubre en PDF"',
					'prompt': prompt,
					'title': 'Generar Reporte con IA',
					'opts': self.model._meta,
					'app_label': self.model._meta.app_label,
				}
				return TemplateResponse(request, self.change_list_template, context)
			
			# Medir tiempo de ejecución
			inicio = time.time()
			
			try:
				# 1. Interpretar prompt
				interprete = InterpretadorPrompt(prompt)
				interpretacion = interprete.interpretar()
				
				# Validar que se detectó el tipo de reporte
				if not interpretacion.get('tipo_reporte'):
					context = {
						'error': '⚠️ No entendí qué tipo de reporte quieres. Usa palabras como: ventas, productos, clientes, inventario',
						'prompt': prompt,
						'title': 'Generar Reporte con IA',
						'opts': self.model._meta,
						'app_label': self.model._meta.app_label,
					}
					return TemplateResponse(request, self.change_list_template, context)
				
				# 2. Generar consulta
				generador = GeneradorConsultas(interpretacion)
				resultado = generador.generar_consulta()
				
				# Validar que hay resultados
				if not resultado or not resultado.get('datos'):
					context = {
						'error': '📭 No se encontraron datos para tu consulta. Intenta con otras fechas o filtros.',
						'prompt': prompt,
						'title': 'Generar Reporte con IA',
						'opts': self.model._meta,
						'app_label': self.model._meta.app_label,
					}
					return TemplateResponse(request, self.change_list_template, context)
				
				# 3. Convertir interpretacion y resultado para JSON serialization
				from .interprete import convert_decimal_to_float
				interpretacion_serializable = convert_decimal_to_float(interpretacion)
				resultado_serializable = convert_decimal_to_float(resultado)
				
				# 4. Guardar en historial
				consulta = ConsultaIA.objects.create(
					usuario=request.user,
					prompt=prompt,
					prompt_interpretado=interpretacion_serializable,
					formato_salida=interpretacion['formato'],
					resultado=resultado_serializable,
					tiempo_ejecucion=time.time() - inicio
				)
				
				# 4. Generar reporte en el formato solicitado
				formato = interpretacion['formato']
				
				if formato == 'pantalla':
					# Mostrar en pantalla
					context = {
						'title': 'Resultado del Reporte',
						'prompt': prompt,
						'interpretacion': interpretacion,
						'resultado': resultado,
						'tiempo': round(time.time() - inicio, 2),
						'consulta_id': consulta.id,
						'opts': self.model._meta,
						'app_label': self.model._meta.app_label,
					}
					return TemplateResponse(request, 'admin/ia/resultado_reporte.html', context)
				
				else:
					# Generar archivo para descarga
					generador_reporte = GeneradorReportes(resultado, interpretacion)
					buffer = generador_reporte.generar(formato)
					
					# Preparar respuesta HTTP
					if formato == 'pdf':
						content_type = 'application/pdf'
						extension = 'pdf'
					elif formato == 'excel':
						content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
						extension = 'xlsx'
					elif formato == 'csv':
						content_type = 'text/csv'
						extension = 'csv'
					
					response = HttpResponse(buffer.read(), content_type=content_type)
					filename = f"reporte_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
					response['Content-Disposition'] = f'attachment; filename="{filename}"'
					
					return response
			
			except Exception as e:
				# Guardar error en historial con stack trace
				import traceback
				error_detallado = traceback.format_exc()
				
				ConsultaIA.objects.create(
					usuario=request.user,
					prompt=prompt,
					error=error_detallado,
					tiempo_ejecucion=time.time() - inicio
				)
				
				# Mensaje de error amigable para el usuario
				mensaje_error = self._generar_mensaje_error_amigable(e)
				
				context = {
					'error': mensaje_error,
					'prompt': prompt,
					'title': 'Generar Reporte con IA',
					'opts': self.model._meta,
					'app_label': self.model._meta.app_label,
				}
				return TemplateResponse(request, self.change_list_template, context)
		
		# GET - Mostrar formulario
		ejemplos = [
			"Ventas de octubre en PDF",
			"Top 10 productos más vendidos en Excel",
			"Clientes activos del último mes",
			"Inventario actual en CSV",
			"Compras de los últimos 30 días en pantalla",
			"Ventas del 01-12-2024 al 15-12-2024 en PDF",
		]
		
		# Obtener historial reciente del usuario
		historial = ConsultaIA.objects.filter(
			usuario=request.user
		).order_by('-fecha_consulta')[:10]
		
		context = {
			'title': 'Generar Reporte con IA',
			'ejemplos': ejemplos,
			'historial': historial,
			'opts': self.model._meta,
			'app_label': self.model._meta.app_label,
		}
		
		return TemplateResponse(request, self.change_list_template, context)
	
	def _generar_mensaje_error_amigable(self, excepcion):
		"""Convierte excepciones técnicas en mensajes amigables"""
		error_str = str(excepcion).lower()
		
		if 'does not exist' in error_str or 'no existe' in error_str:
			return "⚠️ No se encontraron datos para tu consulta. Verifica las fechas o los filtros."
		elif 'connection' in error_str or 'database' in error_str:
			return "❌ Error de conexión con la base de datos. Por favor, intenta nuevamente."
		elif 'timeout' in error_str:
			return "⏱️ La consulta tardó demasiado. Intenta con un rango de fechas más específico o usa 'top 50'."
		elif 'permission' in error_str or 'denied' in error_str:
			return "🔒 No tienes permisos para realizar esta consulta."
		elif 'json' in error_str or 'serializ' in error_str:
			return "⚠️ Error al procesar los datos. Por favor, contacta al administrador."
		else:
			return f"❌ Error al procesar consulta: {str(excepcion)}"
