from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from compra.models import Compra, CompraItem
from productos.models import Producto
from clientes.models import Cliente
from django.db.models import F, Value, Case, When, IntegerField
from django.db.models.functions import Coalesce


class SummaryReportView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		ventas_count = Compra.objects.count()
		productos_count = Producto.objects.count()
		clientes_count = Cliente.objects.count()
		total_ventas = Compra.objects.aggregate(total=Sum('total'))['total'] or 0
		ultimas_ventas = (
			Compra.objects.select_related('cliente')
			.order_by('-fecha')[:5]
			.values('id', 'cliente__nombre', 'fecha', 'total')
		)
		return Response({
			'ventas_count': ventas_count,
			'productos_count': productos_count,
			'clientes_count': clientes_count,
			'total_ventas': str(total_ventas),
			'ultimas_ventas': list(ultimas_ventas),
		})


class KPIReportView(APIView):
	"""KPIs rápidos para dashboard administrativo."""
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		hoy = timezone.now().date()
		hace_30 = hoy - timedelta(days=30)

		total_ventas = Compra.objects.aggregate(total=Sum('total'))['total'] or 0
		ventas_30d = Compra.objects.filter(fecha__date__gte=hace_30).aggregate(total=Sum('total'))['total'] or 0
		ordenes_30d = Compra.objects.filter(fecha__date__gte=hace_30).count()

		return Response({
			'kpis': {
				'total_ventas_historico': float(total_ventas),
				'total_ventas_30d': float(ventas_30d),
				'ordenes_30d': ordenes_30d,
				'ticket_promedio_30d': float(ventas_30d) / max(1, ordenes_30d),
			}
		})


class VentasPorDiaView(APIView):
	"""Serie temporal: ventas por día (completa con ceros)."""
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		# Parámetros
		dias = int(request.query_params.get('dias', 30))
		hoy = timezone.now().date()
		inicio = hoy - timedelta(days=dias)

		qs = (
			Compra.objects.filter(fecha__date__gte=inicio)
			.annotate(dia=TruncDate('fecha'))
			.values('dia')
			.annotate(total=Sum('total'), cantidad=Count('id'))
			.order_by('dia')
		)

		mapa = {r['dia']: r for r in qs}
		serie = []
		for i in range(dias + 1):
			d = inicio + timedelta(days=i)
			r = mapa.get(d, None)
			serie.append({
				'fecha': d.isoformat(),
				'total': float((r or {}).get('total') or 0),
				'cantidad': (r or {}).get('cantidad') or 0
			})

		return Response({'serie': serie})


class VentasPorCategoriaView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		dias = int(request.query_params.get('dias', 30))
		hoy = timezone.now().date()
		inicio = hoy - timedelta(days=dias)

		qs = (
			Compra.objects.filter(fecha__date__gte=inicio)
			.values('items__producto__categoria__nombre')
			.annotate(total=Sum('items__subtotal'), cantidad=Count('items'))
			.order_by('-total')
		)

		data = [
			{
				'categoria': r['items__producto__categoria__nombre'] or 'Sin categoría',
				'total': float(r['total'] or 0),
				'cantidad': r['cantidad']
			}
			for r in qs
		]

		return Response({'categorias': data})


class VentasPorProductoView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		dias = int(request.query_params.get('dias', 30))
		limit = int(request.query_params.get('limit', 10))
		hoy = timezone.now().date()
		inicio = hoy - timedelta(days=dias)

		qs = (
			Compra.objects.filter(fecha__date__gte=inicio)
			.values('items__producto__nombre', 'items__producto__sku')
			.annotate(total=Sum('items__subtotal'), cantidad=Sum('items__cantidad'))
			.order_by('-total')[:limit]
		)

		data = [
			{
				'producto': r['items__producto__nombre'],
				'sku': r['items__producto__sku'],
				'total': float(r['total'] or 0),
				'cantidad': int(r['cantidad'] or 0)
			}
			for r in qs
		]

		return Response({'productos': data})


class TopClientesView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		dias = int(request.query_params.get('dias', 30))
		limit = int(request.query_params.get('limit', 10))
		hoy = timezone.now().date()
		inicio = hoy - timedelta(days=dias)

		qs = (
			Compra.objects.filter(fecha__date__gte=inicio)
			.values('cliente__nombre')
			.annotate(total=Sum('total'), ordenes=Count('id'))
			.order_by('-total')[:limit]
		)

		data = [
			{
				'cliente': r['cliente__nombre'] or 'Sin nombre',
				'total': float(r['total'] or 0),
				'ordenes': r['ordenes']
			}
			for r in qs
		]

		return Response({'clientes': data})


class RankingsPerformanceView(APIView):
	"""
	Rankings de rendimiento para dashboard administrativo.
	Proporciona métricas de rendimiento de productos, clientes y categorías.
	"""
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		dias = int(request.query_params.get('dias', 30))
		limit = int(request.query_params.get('limit', 10))
		hoy = timezone.now().date()
		inicio = hoy - timedelta(days=dias)

		# Ranking de productos más vendidos
		productos_ranking = (
			CompraItem.objects.filter(
				compra__fecha__date__gte=inicio
			).values(
				'producto__nombre',
				'producto__sku',
				'producto__categoria__nombre'
			).annotate(
				total_vendido=Sum('cantidad'),
				ingresos_totales=Sum(F('precio_unitario') * F('cantidad')),
				precio_promedio=Sum(F('precio_unitario') * F('cantidad')) / Sum('cantidad')
			).order_by('-total_vendido')[:limit]
		)

		# Ranking de clientes más activos
		clientes_ranking = (
			Compra.objects.filter(fecha__date__gte=inicio)
			.values('cliente__nombre', 'cliente__email')
			.annotate(
				total_compras=Sum('total'),
				numero_ordenes=Count('id'),
				promedio_compra=Sum('total') / Count('id')
			).order_by('-total_compras')[:limit]
		)

		# Ranking de categorías más rentables
		categorias_ranking = (
			CompraItem.objects.filter(
				compra__fecha__date__gte=inicio
			).values('producto__categoria__nombre')
			.annotate(
				total_vendido=Sum('cantidad'),
				ingresos_totales=Sum(F('precio_unitario') * F('cantidad')),
				numero_productos=Count('producto', distinct=True)
			).order_by('-ingresos_totales')[:limit]
		)

		# Métricas de rendimiento generales
		total_ventas = Compra.objects.filter(fecha__date__gte=inicio).aggregate(
			total=Sum('total'), count=Count('id')
		)
		total_productos_vendidos = CompraItem.objects.filter(
			compra__fecha__date__gte=inicio
		).aggregate(total=Sum('cantidad'))['total'] or 0

		# Producto estrella (más vendido)
		producto_estrella = productos_ranking.first()
		producto_estrella_data = None
		if producto_estrella:
			producto_estrella_data = {
				'nombre': producto_estrella['producto__nombre'],
				'sku': producto_estrella['producto__sku'],
				'categoria': producto_estrella['producto__categoria__nombre'],
				'unidades_vendidas': producto_estrella['total_vendido'],
				'ingresos_generados': float(producto_estrella['ingresos_totales'])
			}

		# Cliente estrella (más compras)
		cliente_estrella = clientes_ranking.first()
		cliente_estrella_data = None
		if cliente_estrella:
			cliente_estrella_data = {
				'nombre': cliente_estrella['cliente__nombre'],
				'email': cliente_estrella['cliente__email'],
				'total_compras': float(cliente_estrella['total_compras']),
				'numero_ordenes': cliente_estrella['numero_ordenes']
			}

		return Response({
			'periodo_dias': dias,
			'fecha_inicio': inicio.isoformat(),
			'fecha_fin': hoy.isoformat(),

			# Rankings principales
			'productos_mas_vendidos': [
				{
					'ranking': i + 1,
					'nombre': p['producto__nombre'],
					'sku': p['producto__sku'],
					'categoria': p['producto__categoria__nombre'],
					'unidades_vendidas': p['total_vendido'],
					'ingresos_totales': float(p['ingresos_totales']),
					'precio_promedio': float(p['precio_promedio'])
				}
				for i, p in enumerate(productos_ranking)
			],

			'clientes_mas_activos': [
				{
					'ranking': i + 1,
					'nombre': c['cliente__nombre'],
					'email': c['cliente__email'],
					'total_compras': float(c['total_compras']),
					'numero_ordenes': c['numero_ordenes'],
					'promedio_por_orden': float(c['promedio_compra'])
				}
				for i, c in enumerate(clientes_ranking)
			],

			'categorias_mas_rentables': [
				{
					'ranking': i + 1,
					'nombre': c['producto__categoria__nombre'],
					'unidades_vendidas': c['total_vendido'],
					'ingresos_totales': float(c['ingresos_totales']),
					'productos_en_categoria': c['numero_productos']
				}
				for i, c in enumerate(categorias_ranking)
			],

			# Métricas destacadas
			'metricas_generales': {
				'total_ventas': float(total_ventas['total'] or 0),
				'total_ordenes': total_ventas['count'] or 0,
				'total_productos_vendidos': total_productos_vendidos,
				'promedio_por_orden': float(total_ventas['total'] or 0) / max(total_ventas['count'] or 1, 1)
			},

			# Estrellas del período
			'producto_estrella': producto_estrella_data,
			'cliente_estrella': cliente_estrella_data
		})


class HealthReportView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		return Response({'status': 'ok'})
