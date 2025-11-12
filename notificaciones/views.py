"""
Views para gestión de suscripciones push y notificaciones.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import PushSubscription, NotificacionEnviada, NotificacionAdmin
from .serializers import PushSubscriptionSerializer, NotificacionEnviadaSerializer, NotificacionAdminSerializer


class PushSubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar suscripciones push del usuario autenticado.
    """
    serializer_class = PushSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Solo retorna las suscripciones del usuario autenticado"""
        return PushSubscription.objects.filter(usuario=self.request.user)
    
    def perform_create(self, serializer):
        """Asocia la suscripción al usuario autenticado"""
        # Verificar si ya existe una suscripción con el mismo endpoint
        endpoint = serializer.validated_data['endpoint']
        existing = PushSubscription.objects.filter(
            usuario=self.request.user,
            endpoint=endpoint
        ).first()
        
        if existing:
            # Actualizar la existente
            existing.p256dh = serializer.validated_data['p256dh']
            existing.auth = serializer.validated_data['auth']
            existing.user_agent = serializer.validated_data.get('user_agent', '')
            existing.activa = True
            existing.save()
            self.instance = existing
        else:
            # Crear nueva
            serializer.save(usuario=self.request.user)
    
    @extend_schema(
        summary='Desactivar suscripción',
        description='Desactiva una suscripción push específica',
        responses={200: {'description': 'Suscripción desactivada'}}
    )
    @action(detail=True, methods=['post'])
    def desactivar(self, request, pk=None):
        """Desactiva una suscripción push"""
        subscription = self.get_object()
        subscription.activa = False
        subscription.save(update_fields=['activa'])
        return Response({'status': 'Suscripción desactivada'})
    
    @extend_schema(
        summary='Activar suscripción',
        description='Reactiva una suscripción push previamente desactivada',
        responses={200: {'description': 'Suscripción activada'}}
    )
    @action(detail=True, methods=['post'])
    def activar(self, request, pk=None):
        """Activa una suscripción push"""
        subscription = self.get_object()
        subscription.activa = True
        subscription.save(update_fields=['activa'])
        return Response({'status': 'Suscripción activada'})


class VAPIDPublicKeyView(APIView):
    """
    Retorna la clave pública VAPID necesaria para que el frontend pueda suscribirse.
    Este endpoint NO requiere autenticación ya que la clave pública es... pública.
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        summary='Obtener clave pública VAPID',
        description='''
        Retorna la clave pública VAPID necesaria para que el frontend se suscriba a notificaciones push.
        Esta clave es segura de exponer públicamente.
        ''',
        responses={
            200: {
                'description': 'Clave pública VAPID',
                'examples': [
                    {
                        'name': 'Clave VAPID',
                        'value': {
                            'public_key': 'BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtmSJnSKawqXdmUfvO0lqVpF4qfX3...'
                        }
                    }
                ]
            }
        },
        tags=['Notificaciones Push']
    )
    def get(self, request):
        """Retorna la clave pública VAPID"""
        public_key = getattr(settings, 'VAPID_PUBLIC_KEY', None)
        
        if not public_key:
            return Response(
                {'error': 'VAPID keys no configuradas en el servidor'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        return Response({'public_key': public_key})


class NotificacionHistorialViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para ver el historial de notificaciones del usuario.
    """
    serializer_class = NotificacionEnviadaSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Solo retorna las notificaciones del usuario autenticado"""
        return NotificacionEnviada.objects.filter(usuario=self.request.user)
    
    @extend_schema(
        summary='Marcar todas como leídas',
        description='Marca todas las notificaciones del usuario como leídas (opcional, para futuras mejoras)',
        responses={200: {'description': 'Notificaciones marcadas como leídas'}}
    )
    @action(detail=False, methods=['post'])
    def marcar_todas_leidas(self, request):
        """
        Endpoint opcional para marcar notificaciones como leídas.
        Por ahora solo retorna confirmación.
        """
        return Response({'status': 'Marcadas como leídas'})


class NotificacionAdminViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar notificaciones de administradores.
    Solo administradores y vendedores pueden acceder.
    """
    serializer_class = NotificacionAdminSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Solo retorna notificaciones del usuario autenticado"""
        user = self.request.user
        if user.rol not in ['admin', 'vendedor']:
            return NotificacionAdmin.objects.none()
        return NotificacionAdmin.objects.filter(usuario=user)

    def get_permissions(self):
        """Verificar permisos de admin/vendedor"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Solo admins pueden crear/modificar notificaciones
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Solo admins pueden crear notificaciones"""
        user = self.request.user
        if user.rol != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Solo administradores pueden crear notificaciones")
        serializer.save()


class AdminNotificationPollingView(APIView):
    """
    Endpoint simple para polling de notificaciones de admin.
    Retorna notificaciones recientes y conteo de no leídas.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Obtener notificaciones del admin (polling)',
        description='Retorna las notificaciones recientes del administrador con conteo de no leídas',
        responses={
            200: {
                'description': 'Notificaciones del admin',
                'examples': [
                    {
                        'name': 'Respuesta exitosa',
                        'value': {
                            'notifications': [
                                {
                                    'id': 1,
                                    'tipo': 'nueva_compra',
                                    'titulo': '🛒 Nueva Compra Realizada',
                                    'mensaje': 'Juan Pérez realizó una compra de $899.99',
                                    'url': '/admin/ventas/123',
                                    'datos': {'compra_id': 123, 'cliente_id': 456},
                                    'creada': '2025-11-12T22:30:00Z',
                                    'leida': False
                                }
                            ],
                            'unread_count': 3,
                            'total_count': 15
                        }
                    }
                ]
            }
        },
        tags=['Notificaciones Admin']
    )
    def get(self, request):
        """Retorna notificaciones del admin para polling"""
        user = request.user

        # Verificar permisos de admin/vendedor
        if user.rol not in ['admin', 'vendedor']:
            return Response(
                {'error': 'No autorizado'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Obtener notificaciones recientes (últimas 20)
        notifications = NotificacionAdmin.objects.filter(
            usuario=user
        ).order_by('-creada')[:20]

        # Para polling simple, todas las notificaciones recientes se consideran "no leídas"
        # El frontend maneja el estado de lectura localmente
        unread_count = len(notifications)

        # Serializar notificaciones
        serializer = NotificacionAdminSerializer(notifications, many=True)

        return Response({
            'notifications': serializer.data,
            'unread_count': unread_count,
            'total_count': len(serializer.data)
        })


