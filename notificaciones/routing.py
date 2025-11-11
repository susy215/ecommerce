"""
Rutas WebSocket para notificaciones.
"""
from django.urls import path
from . import consumers

# Definir las rutas WebSocket
websocket_urlpatterns = [
    # Notificaciones para administradores
    path('ws/admin/notifications/', consumers.AdminNotificationConsumer.as_asgi()),

    # Versión alternativa con mejor funcionalidad
    path('ws/admin/notifications/v2/', consumers.AdminNotificationConsumerV2.as_asgi()),
]
