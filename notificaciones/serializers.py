"""
Serializers para notificaciones push.
"""
from rest_framework import serializers
from .models import PushSubscription, NotificacionEnviada, NotificacionAdmin


class PushSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer para crear/actualizar suscripciones push.
    El usuario se toma del request.user automáticamente.
    """
    class Meta:
        model = PushSubscription
        fields = ['id', 'endpoint', 'p256dh', 'auth', 'user_agent', 'activa', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion']
    
    def validate_endpoint(self, value):
        """Valida que el endpoint sea una URL válida"""
        if not value.startswith('http'):
            raise serializers.ValidationError('El endpoint debe ser una URL válida')
        return value


class NotificacionEnviadaSerializer(serializers.ModelSerializer):
    """
    Serializer para historial de notificaciones (solo lectura).
    """
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = NotificacionEnviada
        fields = [
            'id', 'tipo', 'tipo_display', 'titulo', 'mensaje',
            'datos_extra', 'estado', 'estado_display', 'error', 'fecha_envio'
        ]
        read_only_fields = fields


class NotificacionAdminSerializer(serializers.ModelSerializer):
    """
    Serializer para notificaciones de administradores.
    """
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    usuario_display = serializers.CharField(source='usuario.get_full_name', read_only=True)

    class Meta:
        model = NotificacionAdmin
        fields = [
            'id', 'tipo', 'tipo_display', 'titulo', 'mensaje',
            'url', 'datos', 'creada', 'usuario_display'
        ]
        read_only_fields = ['id', 'creada', 'usuario_display']

    def create(self, validated_data):
        """Asignar usuario automáticamente"""
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)

