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

# Log para confirmar que ASGI se carga
import logging
logger = logging.getLogger(__name__)
logger.info('🚀 ASGI application loaded with JWT middleware')

class LoggingProtocolTypeRouter:
    """ProtocolTypeRouter con logs para debug"""
    def __init__(self, application_mapping):
        self.application_mapping = application_mapping
        self.logger = logging.getLogger(__name__)

    async def __call__(self, scope, receive, send):
        protocol = scope.get('type')
        self.logger.info(f'📡 ProtocolTypeRouter called for: {protocol}')

        application = self.application_mapping.get(protocol)
        if application:
            self.logger.info(f'✅ Found application for {protocol}')
            return await application(scope, receive, send)
        else:
            self.logger.error(f'❌ No application found for {protocol}')
            # Fallback to HTTP app
            return await self.application_mapping['http'](scope, receive, send)

# Usar el router con logs
application = LoggingProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(  # Usar JWT middleware en lugar de AuthMiddlewareStack
        URLRouter(websocket_urlpatterns)
    ),
})
