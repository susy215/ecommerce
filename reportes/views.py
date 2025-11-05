from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from compra.models import Compra
from productos.models import Producto
from clientes.models import Cliente


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


class HealthReportView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		return Response({'status': 'ok'})
