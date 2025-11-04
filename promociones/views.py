from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Promocion, DevolucionProducto
from .serializers import PromocionSerializer, DevolucionProductoSerializer, DevolucionCreateSerializer
import logging

logger = logging.getLogger('promociones')


class PromocionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para que los clientes vean promociones disponibles.
    """
    queryset = Promocion.objects.filter(activa=True)
    serializer_class = PromocionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['tipo_descuento', 'activa']
    search_fields = ['codigo', 'nombre', 'descripcion']
    ordering_fields = ['fecha_inicio', 'valor_descuento']
    
    def get_queryset(self):
        """Solo devolver promociones vigentes"""
        queryset = super().get_queryset()
        # Filtro adicional para mostrar solo vigentes
        vigentes = self.request.query_params.get('vigentes', None)
        if vigentes == 'true':
            # Filtrar manualmente las vigentes
            return [p for p in queryset if p.esta_vigente()]
        return queryset
    
    @action(detail=False, methods=['post'])
    def validar(self, request):
        """
        Valida un código de promoción y calcula el descuento.
        Body: { "codigo": "VERANO2025", "monto": 100.00 }
        """
        codigo = request.data.get('codigo')
        monto = request.data.get('monto')
        
        if not codigo or not monto:
            return Response(
                {'detail': 'Se requiere código y monto'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            promocion = Promocion.objects.get(codigo=codigo.upper())
        except Promocion.DoesNotExist:
            return Response(
                {'detail': 'Código de promoción inválido'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not promocion.esta_vigente():
            return Response(
                {'detail': 'La promoción no está vigente o ha alcanzado el límite de usos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from decimal import Decimal
            monto_decimal = Decimal(str(monto))
        except (ValueError, TypeError):
            return Response(
                {'detail': 'Monto inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        descuento, total_final = promocion.calcular_descuento(monto_decimal)
        
        return Response({
            'valido': True,
            'promocion': PromocionSerializer(promocion).data,
            'monto_original': str(monto_decimal),
            'descuento': str(descuento),
            'total_final': str(total_final),
        })


class DevolucionProductoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de devoluciones.
    Clientes pueden crear y ver sus devoluciones.
    """
    serializer_class = DevolucionProductoSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['estado', 'tipo']
    search_fields = ['motivo', 'descripcion']
    ordering_fields = ['fecha_solicitud']
    ordering = ['-fecha_solicitud']
    
    def get_queryset(self):
        """
        Los clientes solo ven sus propias devoluciones.
        Los admin/staff ven todas.
        """
        user = self.request.user
        if user.is_staff:
            return DevolucionProducto.objects.all()
        
        # Obtener el cliente del usuario
        from clientes.models import Cliente
        try:
            cliente = Cliente.objects.get(usuario=user)
            return DevolucionProducto.objects.filter(cliente=cliente)
        except Cliente.DoesNotExist:
            return DevolucionProducto.objects.none()
    
    def get_serializer_class(self):
        """Usar serializer simplificado para creación"""
        if self.action == 'create':
            return DevolucionCreateSerializer
        return DevolucionProductoSerializer
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Crear solicitud de devolución"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Validar que el compra_item pertenezca al cliente
        compra_item = serializer.validated_data['compra_item']
        
        from clientes.models import Cliente
        try:
            cliente = Cliente.objects.get(usuario=request.user)
        except Cliente.DoesNotExist:
            return Response(
                {'detail': 'Usuario no tiene un perfil de cliente'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if compra_item.compra.cliente != cliente:
            return Response(
                {'detail': 'No tienes permiso para devolver este producto'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validar que la compra esté pagada
        if not compra_item.compra.esta_pagada:
            return Response(
                {'detail': 'Solo se pueden devolver productos de compras pagadas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        devolucion = serializer.save()
        
        logger.info(f"Devolución {devolucion.id} creada por cliente {cliente.id}")
        
        return Response(
            DevolucionProductoSerializer(devolucion).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """
        Permite al cliente cancelar su solicitud (solo si está pendiente).
        """
        devolucion = self.get_object()
        
        if devolucion.estado != 'pendiente':
            return Response(
                {'detail': 'Solo se pueden cancelar solicitudes pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cambiar estado a rechazada (auto-cancelación)
        devolucion.estado = 'rechazada'
        devolucion.respuesta_admin = 'Cancelada por el cliente'
        devolucion.save()
        
        logger.info(f"Devolución {devolucion.id} cancelada por cliente")
        
        return Response({
            'detail': 'Solicitud cancelada exitosamente',
            'devolucion': DevolucionProductoSerializer(devolucion).data
        })
