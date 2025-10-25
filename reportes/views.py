from django.db.models import Sum, Count
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
