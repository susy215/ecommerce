from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Venta, VentaItem
from .serializers import VentaSerializer, VentaItemSerializer


class IsOwnerOrAdmin(permissions.BasePermission):
	def has_object_permission(self, request, view, obj):
		if request.user and request.user.is_staff:
			return True
		# obj can be Venta or VentaItem
		if isinstance(obj, Venta):
			return getattr(obj.cliente, 'usuario_id', None) == request.user.id
		if isinstance(obj, VentaItem):
			return getattr(obj.venta.cliente, 'usuario_id', None) == request.user.id
		return False


class VentaViewSet(viewsets.ModelViewSet):
	queryset = Venta.objects.select_related('cliente', 'vendedor').all()
	serializer_class = VentaSerializer
	permission_classes = [permissions.IsAuthenticated]
	filter_backends = [filters.SearchFilter, filters.OrderingFilter]
	search_fields = ['cliente__nombre', 'observaciones']
	ordering_fields = ['fecha', 'total']

	def perform_create(self, serializer):
		# Para clientes: vincular/crear perfil Cliente y no asignar vendedor
		user = self.request.user
		cliente = getattr(user, 'perfil_cliente', None)
		if cliente is None:
			from clientes.models import Cliente
			cliente = Cliente.objects.create(usuario=user, nombre=user.get_full_name() or user.username, email=user.email or '')
		serializer.save(vendedor=None, cliente=cliente)

	def get_queryset(self):
		qs = super().get_queryset()
		if self.request.user.is_staff:
			return qs
		return qs.filter(cliente__usuario=self.request.user)

	def get_permissions(self):
		if self.action in ['list', 'create']:
			return [permissions.IsAuthenticated()]
		# object-level checks for retrieve/update/destroy
		return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]

	@action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsOwnerOrAdmin])
	def items(self, request, pk=None):
		venta = self.get_object()
		ser = VentaItemSerializer(venta.items.select_related('producto'), many=True)
		return Response(ser.data)

	@action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsOwnerOrAdmin])
	def pay(self, request, pk=None):
		"""Marca la venta como pagada, guarda referencia y fecha de pago.
		Espera body: { "referencia": "..." }
		"""
		venta = self.get_object()
		if venta.total <= 0:
			return Response({'detail': 'El total debe ser mayor a 0'}, status=status.HTTP_400_BAD_REQUEST)
		if venta.pago_estado == 'pagado':
			return Response({'detail': 'La venta ya está pagada'}, status=status.HTTP_400_BAD_REQUEST)
		ref = (request.data.get('referencia') or '').strip()
		if not ref:
			return Response({'detail': 'Referencia de pago requerida'}, status=status.HTTP_400_BAD_REQUEST)
		venta.pago_estado = 'pagado'
		venta.estado = 'pagado'
		venta.pago_referencia = ref
		from django.utils import timezone
		venta.pagado_en = timezone.now()
		venta.save(update_fields=['pago_estado', 'estado', 'pago_referencia', 'pagado_en'])
		return Response(VentaSerializer(venta).data)


class VentaItemViewSet(viewsets.ModelViewSet):
	queryset = VentaItem.objects.select_related('venta', 'producto').all()
	serializer_class = VentaItemSerializer
	permission_classes = [permissions.IsAuthenticated]

	def perform_create(self, serializer):
		venta = serializer.validated_data.get('venta')
		user = self.request.user
		if not (user.is_staff or getattr(venta.cliente, 'usuario_id', None) == user.id):
			return Response({'detail': 'No puedes modificar esta venta'}, status=status.HTTP_403_FORBIDDEN)
		if venta.pago_estado == 'pagado':
			return Response({'detail': 'No puedes modificar items de una venta pagada'}, status=status.HTTP_400_BAD_REQUEST)
		cantidad = serializer.validated_data['cantidad']
		precio = serializer.validated_data['precio_unitario']
		obj = serializer.save(subtotal=cantidad * precio)
		venta.recalc_total()
		return obj

	def get_queryset(self):
		qs = super().get_queryset()
		if self.request.user.is_staff:
			return qs
		return qs.filter(venta__cliente__usuario=self.request.user)

	def update(self, request, *args, **kwargs):
		instance = self.get_object()
		venta = instance.venta
		if not (request.user.is_staff or getattr(venta.cliente, 'usuario_id', None) == request.user.id):
			return Response({'detail': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)
		if venta.pago_estado == 'pagado':
			return Response({'detail': 'No puedes modificar items de una venta pagada'}, status=status.HTTP_400_BAD_REQUEST)
		response = super().update(request, *args, **kwargs)
		# Recalcular subtotal si cambió cantidad/precio
		instance.refresh_from_db()
		instance.subtotal = instance.cantidad * instance.precio_unitario
		instance.save(update_fields=['subtotal'])
		venta.recalc_total()
		return response

	def destroy(self, request, *args, **kwargs):
		instance = self.get_object()
		venta = instance.venta
		if not (request.user.is_staff or getattr(venta.cliente, 'usuario_id', None) == request.user.id):
			return Response({'detail': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)
		if venta.pago_estado == 'pagado':
			return Response({'detail': 'No puedes modificar items de una venta pagada'}, status=status.HTTP_400_BAD_REQUEST)
		response = super().destroy(request, *args, **kwargs)
		venta.recalc_total()
		return response
