from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
import time

from .interprete import InterpretadorPrompt, GeneradorConsultas
from .generador_reportes import GeneradorReportes
from .models import ConsultaIA
from .modelo_ml import ModeloPrediccionVentas
from compra.models import Compra


class HealthView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		return Response({'status': 'ok'})


class ConsultaIAView(APIView):
	"""
	API para procesar consultas en lenguaje natural y generar reportes dinámicos.
	
	Permite generar reportes mediante prompts de texto o comandos de voz (convertidos a texto).
	El sistema interpreta el prompt, construye dinámicamente la consulta SQL y genera
	el reporte en el formato solicitado (PDF, Excel, CSV o pantalla).
	"""
	permission_classes = [permissions.IsAuthenticated]
	
	@extend_schema(
		summary='Generar reporte dinámico desde prompt',
		description='''
		Procesa un prompt en lenguaje natural y genera un reporte dinámico.
		
		Ejemplos de prompts válidos:
		- "Quiero un reporte de ventas del mes de septiembre, agrupado por producto, en PDF"
		- "Quiero un reporte en Excel que muestre las ventas del periodo del 01/10/2024 al 01/01/2025"
		- "Ventas del último mes agrupadas por cliente"
		
		El sistema detecta automáticamente:
		- Tipo de reporte (ventas, productos, clientes, inventario)
		- Rangos de fechas (meses, fechas específicas, períodos relativos)
		- Formato de salida (PDF, Excel, CSV, pantalla)
		- Agrupaciones (por producto, cliente, categoría, fecha)
		- Filtros y métricas
		''',
		request={
			'application/json': {
				'type': 'object',
				'properties': {
					'prompt': {
						'type': 'string',
						'description': 'Consulta en lenguaje natural',
						'examples': [
							'Quiero un reporte de ventas del mes de septiembre en PDF',
							'Ventas del 01/10/2024 al 01/01/2025 agrupadas por cliente en Excel',
							'Top 10 productos más vendidos'
						]
					},
					'formato': {
						'type': 'string',
						'enum': ['pdf', 'excel', 'csv', 'pantalla'],
						'description': 'Formato de salida (opcional, se puede inferir del prompt)'
					}
				},
				'required': ['prompt']
			}
		},
		responses={
			200: {
				'description': 'Reporte generado exitosamente',
				'content': {
					'application/json': {
						'examples': [
							{
								'name': 'Reporte en pantalla',
								'value': {
									'consulta_id': 1,
									'interpretacion': {
										'tipo_reporte': 'ventas',
										'fecha_inicio': '2024-09-01T00:00:00Z',
										'fecha_fin': '2024-09-30T23:59:59Z',
										'formato': 'pantalla',
										'agrupar_por': ['producto']
									},
									'resultado': {
										'tipo': 'por_producto',
										'columnas': ['producto', 'sku', 'cantidad_vendida', 'total_vendido'],
										'datos': [
											{'producto': 'Producto A', 'sku': 'SKU001', 'cantidad_vendida': 50, 'total_vendido': 5000.00}
										]
									},
									'tiempo_ejecucion': 0.45
								}
							}
						]
					},
					'application/pdf': {},
					'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': {},
					'text/csv': {}
				}
			},
			400: {'description': 'Prompt inválido o faltante'},
			500: {'description': 'Error al procesar la consulta'}
		},
		tags=['IA - Reportes Dinámicos']
	)
	def post(self, request):
		"""
		Procesa un prompt y devuelve los datos o genera un archivo
		
		Body:
		{
			"prompt": "Quiero un reporte de ventas del mes de septiembre en PDF",
			"formato": "pdf"  // opcional, se puede inferir del prompt
		}
		"""
		prompt = request.data.get('prompt', '').strip()
		
		if not prompt:
			return Response(
				{'detail': 'Se requiere un prompt'},
				status=status.HTTP_400_BAD_REQUEST
			)
		
		# Medir tiempo
		inicio = time.time()
		
		try:
			# 1. Interpretar prompt
			interprete = InterpretadorPrompt(prompt)
			interpretacion = interprete.interpretar()
			
			# Override formato si se especifica
			if 'formato' in request.data:
				interpretacion['formato'] = request.data['formato']
			
			# 2. Generar consulta
			generador = GeneradorConsultas(interpretacion)
			resultado = generador.generar_consulta()
			
			# 3. Convertir para JSON serialization
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
			
			# 5. Responder según formato
			formato = interpretacion['formato']
			
			if formato == 'pantalla':
				# Devolver JSON con los datos
				return Response({
					'consulta_id': consulta.id,
					'interpretacion': interpretacion_serializable,
					'resultado': resultado_serializable,
					'tiempo_ejecucion': round(time.time() - inicio, 2)
				})
			else:
				# Generar archivo
				generador_reporte = GeneradorReportes(resultado, interpretacion)
				buffer = generador_reporte.generar(formato)
				
				# Preparar respuesta
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
			# Guardar error
			ConsultaIA.objects.create(
				usuario=request.user,
				prompt=prompt,
				error=str(e),
				tiempo_ejecucion=time.time() - inicio
			)
			
			return Response(
				{'detail': f'Error al procesar consulta: {str(e)}'},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)


class DashboardPrediccionesView(APIView):
	"""
	API para obtener datos del dashboard: ventas históricas y predicciones.
	
	Endpoint para dashboard con:
	- Ventas históricas (por período, producto, cliente)
	- Predicciones de ventas futuras usando RandomForestRegressor
	- Gráficas dinámicas (líneas, barras, comparativas)
	"""
	permission_classes = [permissions.IsAuthenticated]
	
	@extend_schema(
		summary='Obtener datos del dashboard de predicciones',
		description='''
		Retorna datos históricos y predicciones de ventas para visualización en dashboard.
		
		Incluye:
		- Ventas históricas diarias (completas con días sin ventas = 0)
		- Predicciones usando RandomForestRegressor (o media móvil como fallback)
		- KPIs (totales, promedios)
		- Top 5 categorías y clientes
		
		El modelo se entrena automáticamente si no existe o si se solicita explícitamente.
		''',
		parameters=[
			OpenApiParameter(
				'dias_hist',
				OpenApiTypes.INT,
				description='Días históricos a mostrar (default: 30)',
				default=30
			),
			OpenApiParameter(
				'dias_pred',
				OpenApiTypes.INT,
				description='Días futuros a predecir (default: 7)',
				default=7
			),
			OpenApiParameter(
				'categoria',
				OpenApiTypes.STR,
				description='Filtrar por categoría (opcional)',
				required=False
			),
			OpenApiParameter(
				'entrenar',
				OpenApiTypes.BOOL,
				description='Si es true, reentrena el modelo antes de predecir (default: false)',
				default=False
			),
		],
		responses={
			200: {
				'description': 'Datos del dashboard',
				'examples': [
					{
						'name': 'Dashboard completo',
						'value': {
							'historico': [
								{'fecha': '2024-12-01', 'total': 1500.00, 'cantidad': 5, 'tipo': 'historico'}
							],
							'predicciones': [
								{'fecha': '2024-12-08', 'total_predicho': 1600.00, 'tipo': 'prediccion'}
							],
							'modelo_info': {
								'modelo': 'RandomForestRegressor',
								'metricas': {'test_r2': 0.85, 'test_mae': 120.5, 'test_rmse': 180.3},
								'fecha_entrenamiento': '2024-12-07T10:30:00Z'
							},
							'kpis': {
								'historico': {'total': 45000.00, 'promedio_diario': 1500.00, 'dias': 30},
								'prediccion': {'total': 11200.00, 'promedio_diario': 1600.00, 'dias': 7}
							},
							'ventas_por_categoria': [
								{'categoria': 'Electrónica', 'total': 25000.00, 'cantidad': 100}
							],
							'ventas_por_cliente': [
								{'cliente': 'Cliente A', 'total': 5000.00, 'cantidad': 10}
							]
						}
					}
				]
			}
		},
		tags=['IA - Dashboard']
	)
	def get(self, request):
		"""
		Retorna datos históricos y predicciones para el dashboard.
		
		Query params:
		- dias_hist: Días históricos a mostrar (default: 30)
		- dias_pred: Días futuros a predecir (default: 7)
		- categoria: Filtrar por categoría (opcional)
		- entrenar: Si es 'true', reentrena el modelo antes de predecir
		"""
		dias_hist = int(request.query_params.get('dias_hist', 30))
		dias_pred = int(request.query_params.get('dias_pred', 7))
		categoria = request.query_params.get('categoria', None)
		entrenar = request.query_params.get('entrenar', 'false').lower() == 'true'
		
		hoy = timezone.now().date()
		inicio = hoy - timedelta(days=dias_hist)
		
		# 1. Obtener ventas históricas diarias
		queryset = Compra.objects.filter(fecha__date__gte=inicio)
		
		# Filtrar por categoría si se especifica
		if categoria:
			queryset = queryset.filter(items__producto__categoria__nombre=categoria).distinct()
		
		historico_diario = queryset.values('fecha__date').annotate(
			total=Sum('total'),
			cantidad=Count('id')
		).order_by('fecha__date')
		
		# Completar días faltantes con 0
		historico_completo = []
		tot_map = {r['fecha__date']: r['total'] or 0 for r in historico_diario}
		cant_map = {r['fecha__date']: r['cantidad'] for r in historico_diario}
		
		for i in range(dias_hist + 1):
			d = inicio + timedelta(days=i)
			historico_completo.append({
				'fecha': d.isoformat(),
				'total': float(tot_map.get(d, 0)),
				'cantidad': cant_map.get(d, 0),
				'tipo': 'historico'
			})
		
		# 2. Obtener predicciones usando RandomForestRegressor
		modelo = ModeloPrediccionVentas()
		
		# Entrenar si se solicita o si no hay modelo entrenado
		if entrenar or not modelo.cargar_modelo():
			# Entrenar con más días históricos para mejor precisión
			metricas = modelo.entrenar(dias_historico=min(90, dias_hist * 3))
			if not metricas.get('success'):
				# Si falla el entrenamiento, usar media móvil simple como fallback
				predicciones = self._prediccion_simple(historico_completo, dias_pred)
				modelo_info = {
					'modelo': 'Media Móvil (fallback)',
					'error': metricas.get('error', 'Error desconocido')
				}
			else:
				predicciones_result = modelo.predecir(dias_futuros=dias_pred)
				if predicciones_result.get('success'):
					predicciones = predicciones_result['predicciones']
					modelo_info = {
						'modelo': 'RandomForestRegressor',
						'metricas': {
							'test_r2': metricas.get('test_r2', 0),
							'test_mae': metricas.get('test_mae', 0),
							'test_rmse': metricas.get('test_rmse', 0)
						},
						'fecha_entrenamiento': metricas.get('fecha_entrenamiento')
					}
				else:
					predicciones = self._prediccion_simple(historico_completo, dias_pred)
					modelo_info = {
						'modelo': 'Media Móvil (fallback)',
						'error': predicciones_result.get('error', 'Error al predecir')
					}
		else:
			# Usar modelo existente
			predicciones_result = modelo.predecir(dias_futuros=dias_pred)
			if predicciones_result.get('success'):
				predicciones = predicciones_result['predicciones']
				modelo_info = {
					'modelo': 'RandomForestRegressor',
					'fecha_entrenamiento': modelo.get_fecha_entrenamiento().isoformat() if modelo.get_fecha_entrenamiento() else None
				}
			else:
				predicciones = self._prediccion_simple(historico_completo, dias_pred)
				modelo_info = {
					'modelo': 'Media Móvil (fallback)',
					'error': predicciones_result.get('error', 'Error al predecir')
				}
		
		# 3. KPIs
		total_historico = sum(p['total'] for p in historico_completo)
		promedio_historico = total_historico / max(1, len(historico_completo))
		total_prediccion = sum(p['total_predicho'] for p in predicciones)
		promedio_prediccion = total_prediccion / max(1, len(predicciones))
		
		# 4. Ventas por categoría (top 5)
		ventas_categoria = Compra.objects.filter(
			fecha__date__gte=inicio
		).values(
			'items__producto__categoria__nombre'
		).annotate(
			total=Sum('items__subtotal'),
			cantidad=Count('items', distinct=True)
		).order_by('-total')[:5]
		
		categorias_data = [
			{
				'categoria': item['items__producto__categoria__nombre'] or 'Sin categoría',
				'total': float(item['total'] or 0),
				'cantidad': item['cantidad']
			}
			for item in ventas_categoria
		]
		
		# 5. Ventas por cliente (top 5)
		ventas_cliente = Compra.objects.filter(
			fecha__date__gte=inicio
		).values(
			'cliente__nombre'
		).annotate(
			total=Sum('total'),
			cantidad=Count('id')
		).order_by('-total')[:5]
		
		clientes_data = [
			{
				'cliente': item['cliente__nombre'],
				'total': float(item['total'] or 0),
				'cantidad': item['cantidad']
			}
			for item in ventas_cliente
		]
		
		return Response({
			'historico': historico_completo,
			'predicciones': predicciones,
			'modelo_info': modelo_info,
			'kpis': {
				'historico': {
					'total': round(total_historico, 2),
					'promedio_diario': round(promedio_historico, 2),
					'dias': len(historico_completo)
				},
				'prediccion': {
					'total': round(total_prediccion, 2),
					'promedio_diario': round(promedio_prediccion, 2),
					'dias': len(predicciones)
				}
			},
			'ventas_por_categoria': categorias_data,
			'ventas_por_cliente': clientes_data,
			'periodo': {
				'inicio': inicio.isoformat(),
				'fin': hoy.isoformat(),
				'dias_hist': dias_hist,
				'dias_pred': dias_pred
			}
		})
	
	def _prediccion_simple(self, historico, dias_futuros):
		"""Predicción simple usando media móvil como fallback."""
		ventana = 7
		serie = [p['total'] for p in historico]
		predicciones = []
		hoy = timezone.now().date()
		
		for i in range(1, dias_futuros + 1):
			ventana_vals = serie[-ventana:] if len(serie) >= ventana else serie
			prom = sum(ventana_vals) / max(1, len(ventana_vals))
			predicciones.append({
				'fecha': (hoy + timedelta(days=i)).isoformat(),
				'total_predicho': round(prom, 2),
				'tipo': 'prediccion'
			})
		
		return predicciones


class EntrenarModeloView(APIView):
	"""
	API para entrenar/reentrenar el modelo de predicción RandomForestRegressor.
	
	Requiere permisos de administrador. El modelo se guarda automáticamente después del entrenamiento.
	"""
	permission_classes = [permissions.IsAuthenticated]
	
	@extend_schema(
		summary='Entrenar modelo de predicción',
		description='''
		Entrena o reentrena el modelo RandomForestRegressor para predicción de ventas.
		
		Características del modelo:
		- Usa RandomForestRegressor de scikit-learn
		- Features: día de semana, día del mes, mes, día del año, media móvil, desviación estándar, cantidad, promedio
		- Se serializa con joblib para reutilización
		- Retorna métricas de evaluación (R², MAE, RMSE)
		
		Solo administradores pueden entrenar modelos.
		''',
		request={
			'application/json': {
				'type': 'object',
				'properties': {
					'dias_historico': {
						'type': 'integer',
						'description': 'Días históricos a usar para entrenamiento (default: 90)',
						'default': 90,
						'minimum': 7
					}
				}
			}
		},
		responses={
			200: {
				'description': 'Modelo entrenado exitosamente',
				'examples': [
					{
						'name': 'Entrenamiento exitoso',
						'value': {
							'success': True,
							'message': 'Modelo entrenado exitosamente',
							'metricas': {
								'train_samples': 70,
								'test_samples': 18,
								'train_r2': 0.92,
								'test_r2': 0.85,
								'test_mae': 120.5,
								'test_rmse': 180.3,
								'feature_importance': {
									'media_movil_7': 0.35,
									'dia_semana': 0.15,
									'cantidad': 0.20
								}
							}
						}
					}
				]
			},
			400: {'description': 'Error al entrenar (datos insuficientes u otro error)'},
			403: {'description': 'Solo administradores pueden entrenar modelos'}
		},
		tags=['IA - Modelo ML']
	)
	def post(self, request):
		"""
		Entrena el modelo RandomForestRegressor.
		
		Body opcional:
		{
			"dias_historico": 90  // Días históricos a usar (default: 90)
		}
		"""
		# Solo staff puede entrenar modelos
		if not request.user.is_staff:
			return Response(
				{'detail': 'Solo administradores pueden entrenar modelos'},
				status=status.HTTP_403_FORBIDDEN
			)
		
		dias_historico = int(request.data.get('dias_historico', 90))
		
		modelo = ModeloPrediccionVentas()
		metricas = modelo.entrenar(dias_historico=dias_historico)
		
		if metricas.get('success'):
			return Response({
				'success': True,
				'message': 'Modelo entrenado exitosamente',
				'metricas': metricas
			})
		else:
			return Response(
				{
					'success': False,
					'error': metricas.get('error', 'Error desconocido')
				},
				status=status.HTTP_400_BAD_REQUEST
			)

