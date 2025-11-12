"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Importar rutas de WebSocket después de configurar Django
django_asgi_app = get_asgi_application()

# Importar rutas de WebSocket y middleware personalizado
from notificaciones.routing import websocket_urlpatterns
from .middleware import JWTAuthMiddleware

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(  # Usar JWT middleware en lugar de AuthMiddlewareStack
        URLRouter(websocket_urlpatterns)
    ),
})
