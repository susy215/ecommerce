"""
Middleware personalizado para autenticación JWT en WebSocket.
Versión simplificada y robusta.
"""
import logging
from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware

logger = logging.getLogger(__name__)

class JWTAuthMiddleware(BaseMiddleware):
    """
    Middleware para autenticar WebSocket usando JWT tokens desde la URL.
    Versión simplificada y robusta.
    """

    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        try:
            # Imports dentro del método para evitar problemas de inicialización
            from django.contrib.auth import get_user_model
            from django.contrib.auth.models import AnonymousUser
            from rest_framework_simplejwt.tokens import AccessToken
            from channels.auth import get_user

            # Intentar autenticación JWT desde query parameters
            query_string = scope.get('query_string', b'').decode()
            query_params = parse_qs(query_string)

            token = query_params.get('token', [None])[0]

            if token:
                try:
                    # Validar token JWT
                    access_token = AccessToken(token)
                    user_id = access_token.payload.get('user_id')

                    if user_id:
                        try:
                            User = get_user_model()
                            user = await User.objects.aget(pk=user_id)
                            scope['user'] = user
                            logger.info(f'✅ WS JWT auth success: {user.username}')
                            return await self.inner(scope, receive, send)
                        except User.DoesNotExist:
                            logger.warning(f'❌ WS JWT user not found: {user_id}')
                except Exception as e:
                    logger.warning(f'❌ WS JWT token error: {str(e)[:50]}')
            else:
                # No hay token JWT, usar autenticación normal
                scope['user'] = await get_user(scope)

        except Exception as e:
            logger.error(f'❌ WS middleware error: {str(e)[:100]}')
            # Import aquí también por si acaso
            from django.contrib.auth.models import AnonymousUser
            scope['user'] = AnonymousUser()

        return await self.inner(scope, receive, send)
