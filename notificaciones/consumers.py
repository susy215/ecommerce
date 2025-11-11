"""
Consumers WebSocket para notificaciones en tiempo real a administradores.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import NotificacionAdmin

logger = logging.getLogger(__name__)
User = get_user_model()


class AdminNotificationConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket para notificaciones en tiempo real a administradores.
    Maneja conexiones de admin y envía notificaciones automáticamente.
    """

    async def connect(self):
        """Conectar usuario administrador"""
        self.user = self.scope['user']

        # Verificar que sea admin o vendedor
        if not self.user or not self.user.is_authenticated:
            logger.warning(f'Intento de conexión WebSocket sin autenticación: {self.scope}')
            await self.close(code=4001)  # Código personalizado para no autenticado
            return

        if self.user.rol not in ['admin', 'vendedor']:
            logger.warning(f'Usuario {self.user.username} con rol {self.user.rol} intentó conectarse a WS admin')
            await self.close(code=4002)  # Código personalizado para permisos insuficientes
            return

        # Unirse al grupo de notificaciones del usuario
        self.group_name = f'admin_notifications_{self.user.id}'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f'✅ Admin {self.user.username} conectado a WebSocket')

        # Enviar confirmación de conexión
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Conectado a notificaciones administrativas',
            'user': self.user.username,
            'timestamp': timezone.now().isoformat()
        }))

        # Enviar notificaciones no leídas pendientes
        await self.send_pending_notifications()

    async def disconnect(self, close_code):
        """Desconectar usuario"""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f'🔌 Admin {self.user.username} desconectado (código: {close_code})')

    async def receive(self, text_data):
        """Recibir mensajes del frontend"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'ping':
                # Responder a pings para mantener conexión viva
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
            elif message_type == 'mark_read':
                # Marcar notificación como leída
                notification_id = data.get('notification_id')
                if notification_id:
                    await self.mark_notification_read(notification_id)
            elif message_type == 'get_unread_count':
                # Enviar conteo de no leídas
                await self.send_unread_count()

        except json.JSONDecodeError:
            logger.error(f'Mensaje JSON inválido recibido: {text_data}')
        except Exception as e:
            logger.error(f'Error procesando mensaje WebSocket: {e}')

    async def send_notification(self, event):
        """Enviar notificación al frontend"""
        notification = event['notification']

        # Enviar por WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            **notification
        }))

        logger.debug(f'📤 Notificación enviada por WS a {self.user.username}: {notification.get("titulo")}')

    @database_sync_to_async
    def send_pending_notifications(self):
        """Enviar notificaciones no leídas pendientes"""
        try:
            unread_notifications = NotificacionAdmin.objects.filter(
                usuario=self.user,
                leida=False
            ).order_by('-creada')[:10]  # Últimas 10 no leídas

            for notification in unread_notifications:
                # Usar send() en lugar de channel_layer para evitar loop infinito
                notification_data = {
                    'type': 'notification',
                    'id': notification.id,
                    'tipo': notification.tipo,
                    'titulo': notification.titulo,
                    'mensaje': notification.mensaje,
                    'url': notification.url,
                    'datos': notification.datos,
                    'creada': notification.creada.isoformat(),
                    'leida': notification.leida
                }

                # Enviar directamente (esto se ejecuta en el loop de eventos)
                self.scope['reply_channel'].send({
                    'type': 'websocket.send',
                    'text': json.dumps(notification_data)
                })

        except Exception as e:
            logger.error(f'Error enviando notificaciones pendientes: {e}')

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Marcar notificación como leída"""
        try:
            notification = NotificacionAdmin.objects.get(
                id=notification_id,
                usuario=self.user
            )
            notification.marcar_como_leida()
            logger.info(f'Notificación {notification_id} marcada como leída por {self.user.username}')
        except NotificacionAdmin.DoesNotExist:
            logger.warning(f'Notificación {notification_id} no encontrada para usuario {self.user.username}')
        except Exception as e:
            logger.error(f'Error marcando notificación como leída: {e}')

    @database_sync_to_async
    def send_unread_count(self):
        """Enviar conteo de notificaciones no leídas"""
        try:
            count = NotificacionAdmin.objects.filter(
                usuario=self.user,
                leida=False
            ).count()

            # Enviar directamente
            self.scope['reply_channel'].send({
                'type': 'websocket.send',
                'text': json.dumps({
                    'type': 'unread_count',
                    'count': count,
                    'timestamp': timezone.now().isoformat()
                })
            })
        except Exception as e:
            logger.error(f'Error obteniendo conteo de no leídas: {e}')


class AdminNotificationConsumerV2(AsyncWebsocketConsumer):
    """
    Versión alternativa del consumer con mejor manejo de reconexión.
    Incluye heartbeat automático y mejor gestión de estado.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.group_name = None
        self.heartbeat_interval = None

    async def connect(self):
        """Conectar con heartbeat automático"""
        self.user = self.scope['user']

        # Verificaciones de seguridad
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        if self.user.rol not in ['admin', 'vendedor']:
            await self.close(code=4002)
            return

        # Configurar grupo
        self.group_name = f'admin_notifications_{self.user.id}'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f'✅ Admin {self.user.username} conectado (v2)')

        # Iniciar heartbeat
        await self.start_heartbeat()

        # Enviar confirmación
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'version': '2.0',
            'user': self.user.username,
            'timestamp': timezone.now().isoformat()
        }))

    async def disconnect(self, close_code):
        """Desconectar y limpiar"""
        if self.heartbeat_interval:
            self.heartbeat_interval.cancel()

        if self.group_name:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

        logger.info(f'🔌 Admin {self.user.username} desconectado (código: {close_code})')

    async def start_heartbeat(self):
        """Iniciar heartbeat cada 30 segundos"""
        from asyncio import sleep

        while True:
            try:
                await sleep(30)  # Esperar 30 segundos
                await self.send(text_data=json.dumps({
                    'type': 'heartbeat',
                    'timestamp': timezone.now().isoformat()
                }))
            except Exception as e:
                logger.error(f'Error en heartbeat: {e}')
                break

    async def receive(self, text_data):
        """Manejar mensajes del frontend con mejor error handling"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            # Responder a diferentes tipos de mensajes
            if message_type == 'ping':
                await self.handle_ping()
            elif message_type == 'mark_read':
                await self.handle_mark_read(data)
            elif message_type == 'get_history':
                await self.handle_get_history(data)
            else:
                await self.send_error('unknown_message_type', f'Tipo de mensaje desconocido: {message_type}')

        except json.JSONDecodeError as e:
            await self.send_error('invalid_json', 'JSON inválido recibido')
        except Exception as e:
            logger.error(f'Error procesando mensaje: {e}')
            await self.send_error('internal_error', 'Error interno del servidor')

    async def handle_ping(self):
        """Responder a ping"""
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'timestamp': timezone.now().isoformat()
        }))

    async def handle_mark_read(self, data):
        """Marcar notificación como leída"""
        notification_id = data.get('notification_id')
        if not notification_id:
            await self.send_error('missing_field', 'notification_id es requerido')
            return

        success = await self.mark_notification_read_async(notification_id)
        await self.send(text_data=json.dumps({
            'type': 'mark_read_response',
            'notification_id': notification_id,
            'success': success,
            'timestamp': timezone.now().isoformat()
        }))

    async def handle_get_history(self, data):
        """Enviar historial de notificaciones"""
        page = data.get('page', 1)
        limit = min(data.get('limit', 20), 50)  # Máximo 50

        history = await self.get_notification_history_async(page, limit)
        await self.send(text_data=json.dumps({
            'type': 'notification_history',
            'page': page,
            'limit': limit,
            'notifications': history['results'],
            'has_more': history['has_more'],
            'timestamp': timezone.now().isoformat()
        }))

    async def send_error(self, error_type, message):
        """Enviar mensaje de error al frontend"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'error_type': error_type,
            'message': message,
            'timestamp': timezone.now().isoformat()
        }))

    async def send_notification(self, event):
        """Enviar notificación"""
        notification = event['notification']
        await self.send(text_data=json.dumps({
            'type': 'notification',
            **notification
        }))

    @database_sync_to_async
    def mark_notification_read_async(self, notification_id):
        """Marcar notificación como leída (async)"""
        try:
            notification = NotificacionAdmin.objects.get(
                id=notification_id,
                usuario=self.user
            )
            notification.marcar_como_leida()
            return True
        except NotificacionAdmin.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f'Error marcando notificación como leída: {e}')
            return False

    @database_sync_to_async
    def get_notification_history_async(self, page, limit):
        """Obtener historial de notificaciones (async)"""
        try:
            offset = (page - 1) * limit
            notifications = NotificacionAdmin.objects.filter(
                usuario=self.user
            ).order_by('-creada')[offset:offset + limit]

            results = []
            for notification in notifications:
                results.append({
                    'id': notification.id,
                    'tipo': notification.tipo,
                    'titulo': notification.titulo,
                    'mensaje': notification.mensaje,
                    'url': notification.url,
                    'datos': notification.datos,
                    'creada': notification.creada.isoformat(),
                    'leida': notification.leida
                })

            # Verificar si hay más
            has_more = NotificacionAdmin.objects.filter(
                usuario=self.user
            ).order_by('-creada')[offset + limit:offset + limit + 1].exists()

            return {
                'results': results,
                'has_more': has_more
            }
        except Exception as e:
            logger.error(f'Error obteniendo historial: {e}')
            return {'results': [], 'has_more': False}
