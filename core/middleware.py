"""
Middleware personalizado para autenticación JWT en WebSocket.
"""
import logging
from urllib.parse import parse_qs
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from channels.middleware import BaseMiddleware
from channels.auth import get_user

logger = logging.getLogger(__name__)
User = get_user_model()

class JWTAuthMiddleware(BaseMiddleware):
    """
    Middleware para autenticar WebSocket usando JWT tokens desde la URL.
    Si no hay token JWT, usa la autenticación normal de Django.
    """

    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
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
                        user = await self.get_user(user_id)
                        scope['user'] = user
                        logger.info(f'✅ WebSocket autenticado con JWT: {user.username}')
                        return await self.inner(scope, receive, send)
                    except User.DoesNotExist:
                        logger.warning(f'❌ Usuario JWT no encontrado: {user_id}')
                        scope['user'] = AnonymousUser()
                else:
                    logger.warning('❌ Token JWT sin user_id')
                    scope['user'] = AnonymousUser()

            except (InvalidToken, TokenError) as e:
                logger.warning(f'❌ Token JWT inválido: {e}')
                scope['user'] = AnonymousUser()
        else:
            # No hay token JWT, usar autenticación normal de Django
            scope['user'] = await get_user(scope)

        return await self.inner(scope, receive, send)

    @staticmethod
    async def get_user(user_id):
        """Obtener usuario de forma async"""
        return User.objects.aget(pk=user_id)
