from django.contrib import admin
from django.template.response import TemplateResponse
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta, date

from .models import PrediccionAdminEntry
from compra.models import Compra


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
