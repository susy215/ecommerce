"""
Servicio para enviar notificaciones push usando Web Push API.
Usa VAPID (Voluntary Application Server Identification) para autenticación.
"""
import logging
import json
from typing import Optional, Dict, Any, List
from pywebpush import webpush, WebPushException
from django.conf import settings
from django.utils import timezone
from .models import PushSubscription, NotificacionEnviada

logger = logging.getLogger(__name__)


class PushNotificationService:
    """
    Servicio centralizado para enviar notificaciones push.
    """
    
    def __init__(self):
        """Inicializa el servicio con las claves VAPID"""
        self.vapid_private_key = getattr(settings, 'VAPID_PRIVATE_KEY', None)
        self.vapid_public_key = getattr(settings, 'VAPID_PUBLIC_KEY', None)
        self.vapid_claims = getattr(settings, 'VAPID_CLAIMS', {})
        
        if not self.vapid_private_key or not self.vapid_public_key:
            logger.warning(
                'VAPID keys not configured. Push notifications will not work. '
                'Generate keys with: python manage.py generate_vapid_keys'
            )
    
    def send_notification(
        self,
        usuario,
        titulo: str,
        mensaje: str,
        tipo: str = 'otro',
        datos_extra: Optional[Dict[str, Any]] = None,
        url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envía una notificación push a todas las suscripciones activas del usuario.
        
        Args:
            usuario: Usuario al que enviar la notificación
            titulo: Título de la notificación
            mensaje: Cuerpo del mensaje
            tipo: Tipo de notificación (compra_exitosa, cambio_estado, etc.)
            datos_extra: Datos adicionales para el payload
            url: URL para abrir al hacer clic en la notificación
        
        Returns:
            Dict con resumen del envío (exitosos, fallidos)
        """
        if not self.vapid_private_key:
            logger.error('No se pueden enviar notificaciones: VAPID keys no configuradas')
            return {'exitosos': 0, 'fallidos': 0, 'error': 'VAPID keys no configuradas'}
        
        # Obtener todas las suscripciones activas del usuario
        subscriptions = PushSubscription.objects.filter(
            usuario=usuario,
            activa=True
        )
        
        if not subscriptions.exists():
            logger.info(f'Usuario {usuario.username} no tiene suscripciones activas')
            return {'exitosos': 0, 'fallidos': 0, 'mensaje': 'Sin suscripciones activas'}
        
        # Preparar payload
        payload = {
            'title': titulo,
            'body': mensaje,
            'icon': '/icon-192x192.png',  # Ajusta según tu app
            'badge': '/badge-72x72.png',
            'data': {
                'tipo': tipo,
                'timestamp': timezone.now().isoformat(),
                **(datos_extra or {})
            }
        }
        
        if url:
            payload['data']['url'] = url
        
        exitosos = 0
        fallidos = 0
        
        for subscription in subscriptions:
            try:
                # Preparar información de la suscripción
                subscription_info = {
                    "endpoint": subscription.endpoint,
                    "keys": {
                        "p256dh": subscription.p256dh,
                        "auth": subscription.auth
                    }
                }
                
                # Enviar notificación
                webpush(
                    subscription_info=subscription_info,
                    data=json.dumps(payload),
                    vapid_private_key=self.vapid_private_key,
                    vapid_claims=self.vapid_claims
                )
                
                # Actualizar última notificación
                subscription.ultima_notificacion = timezone.now()
                subscription.save(update_fields=['ultima_notificacion'])
                
                # Guardar en historial como exitoso
                NotificacionEnviada.objects.create(
                    usuario=usuario,
                    subscription=subscription,
                    tipo=tipo,
                    titulo=titulo,
                    mensaje=mensaje,
                    datos_extra=datos_extra,
                    estado='exitoso'
                )
                
                exitosos += 1
                logger.info(f'Notificación enviada a {usuario.username} (subscription {subscription.id})')
                
            except WebPushException as e:
                fallidos += 1
                error_msg = str(e)
                
                # Si el error indica que la suscripción expiró, desactivarla
                if e.response and e.response.status_code in [404, 410]:
                    subscription.activa = False
                    subscription.save(update_fields=['activa'])
                    logger.warning(f'Suscripción {subscription.id} desactivada (error {e.response.status_code})')
                
                # Guardar en historial como fallido
                NotificacionEnviada.objects.create(
                    usuario=usuario,
                    subscription=subscription,
                    tipo=tipo,
                    titulo=titulo,
                    mensaje=mensaje,
                    datos_extra=datos_extra,
                    estado='fallido',
                    error=error_msg
                )
                
                logger.error(f'Error al enviar notificación a {usuario.username}: {error_msg}')
                
            except Exception as e:
                fallidos += 1
                error_msg = str(e)
                
                NotificacionEnviada.objects.create(
                    usuario=usuario,
                    subscription=subscription,
                    tipo=tipo,
                    titulo=titulo,
                    mensaje=mensaje,
                    datos_extra=datos_extra,
                    estado='fallido',
                    error=error_msg
                )
                
                logger.error(f'Error inesperado al enviar notificación: {error_msg}', exc_info=True)

        return {
            'exitosos': exitosos,
            'fallidos': fallidos,
            'total': subscriptions.count()
        }

    def get_administradores(self):
        """
        Obtiene todos los usuarios con rol 'admin' o 'vendedor' para notificaciones.
        """
        from usuarios.models import Usuario
        return Usuario.objects.filter(rol__in=['admin', 'vendedor'])

    def send_to_administradores(self, titulo: str, mensaje: str, tipo: str = 'admin', datos_extra: Optional[Dict[str, Any]] = None, url: Optional[str] = None) -> Dict[str, Any]:
        """
        Envía una notificación push a todos los administradores/vendedores.

        Args:
            titulo: Título de la notificación
            mensaje: Cuerpo del mensaje
            tipo: Tipo de notificación (admin, nueva_compra, nuevo_pago, etc.)
            datos_extra: Datos adicionales para el payload
            url: URL para abrir al hacer clic en la notificación

        Returns:
            Dict con resumen del envío a todos los admins
        """
        administradores = self.get_administradores()
        total_exitosos = 0
        total_fallidos = 0
        resultados = []

        for admin in administradores:
            resultado = self.send_notification(
                usuario=admin,
                titulo=titulo,
                mensaje=mensaje,
                tipo=tipo,
                datos_extra=datos_extra,
                url=url
            )
            resultados.append({
                'admin': admin.username,
                'exitosos': resultado.get('exitosos', 0),
                'fallidos': resultado.get('fallidos', 0)
            })
            total_exitosos += resultado.get('exitosos', 0)
            total_fallidos += resultado.get('fallidos', 0)

        return {
            'total_exitosos': total_exitosos,
            'total_fallidos': total_fallidos,
            'administradores_notificados': len([r for r in resultados if r['exitosos'] > 0]),
            'detalles': resultados
        }

    def send_to_all_clientes(self, titulo: str, mensaje: str, tipo: str = 'promocion', datos_extra: Optional[Dict[str, Any]] = None, url: Optional[str] = None) -> Dict[str, Any]:
        """
        Envía una notificación push a todos los clientes activos.

        Args:
            titulo: Título de la notificación
            mensaje: Cuerpo del mensaje
            tipo: Tipo de notificación
            datos_extra: Datos adicionales para el payload
            url: URL para abrir al hacer clic en la notificación

        Returns:
            Dict con resumen del envío a todos los clientes
        """
        from usuarios.models import Usuario
        clientes = Usuario.objects.filter(rol='cliente', is_active=True)
        total_exitosos = 0
        total_fallidos = 0
        resultados = []

        for cliente in clientes:
            resultado = self.send_notification(
                usuario=cliente,
                titulo=titulo,
                mensaje=mensaje,
                tipo=tipo,
                datos_extra=datos_extra,
                url=url
            )
            resultados.append({
                'cliente': cliente.username,
                'exitosos': resultado.get('exitosos', 0),
                'fallidos': resultado.get('fallidos', 0)
            })
            total_exitosos += resultado.get('exitosos', 0)
            total_fallidos += resultado.get('fallidos', 0)

        return {
            'total_exitosos': total_exitosos,
            'total_fallidos': total_fallidos,
            'clientes_notificados': len([r for r in resultados if r['exitosos'] > 0]),
            'detalles': resultados
        }
    
    def send_compra_exitosa(self, compra) -> Dict[str, Any]:
        """
        Envía notificación de compra exitosa.
        
        Args:
            compra: Instancia del modelo Compra
        """
        usuario = compra.cliente.usuario
        if not usuario:
            logger.warning(f'Compra {compra.id} no tiene usuario asociado')
            return {'error': 'Usuario no encontrado'}
        
        titulo = '🎉 ¡Compra realizada con éxito!'
        mensaje = f'Tu pedido #{compra.id} por ${compra.total} ha sido confirmado.'
        
        return self.send_notification(
            usuario=usuario,
            titulo=titulo,
            mensaje=mensaje,
            tipo='compra_exitosa',
            datos_extra={
                'compra_id': compra.id,
                'total': float(compra.total),
                'items_count': compra.items.count()
            },
            url=f'/mis-pedidos/{compra.id}'
        )
    
    def send_cambio_estado(self, compra, estado_anterior: str) -> Dict[str, Any]:
        """
        Envía notificación de cambio de estado de pedido.
        
        Args:
            compra: Instancia del modelo Compra
            estado_anterior: Estado previo del pedido
        """
        usuario = compra.cliente.usuario
        if not usuario:
            return {'error': 'Usuario no encontrado'}
        
        # Mensajes según el estado
        estados_mensajes = {
            'pagado': {
                'emoji': '✅',
                'titulo': 'Pago confirmado',
                'mensaje': f'El pago de tu pedido #{compra.id} ha sido confirmado.'
            },
            'enviado': {
                'emoji': '📦',
                'titulo': 'Pedido enviado',
                'mensaje': f'Tu pedido #{compra.id} está en camino. ¡Pronto lo recibirás!'
            },
            'completado': {
                'emoji': '🎁',
                'titulo': 'Pedido completado',
                'mensaje': f'Tu pedido #{compra.id} ha sido entregado. ¡Gracias por tu compra!'
            }
        }
        
        # Si pagado_en acaba de establecerse, considerarlo como "pagado"
        if compra.pagado_en and not estado_anterior:
            estado_key = 'pagado'
        else:
            # Para futuros estados (si se agregan)
            estado_key = 'pagado' if compra.pagado_en else 'pendiente'
        
        info = estados_mensajes.get(estado_key, {
            'emoji': '📋',
            'titulo': 'Estado actualizado',
            'mensaje': f'El estado de tu pedido #{compra.id} ha cambiado.'
        })
        
        titulo = f"{info['emoji']} {info['titulo']}"
        mensaje = info['mensaje']
        
        return self.send_notification(
            usuario=usuario,
            titulo=titulo,
            mensaje=mensaje,
            tipo='cambio_estado',
            datos_extra={
                'compra_id': compra.id,
                'estado_anterior': estado_anterior,
                'pagado': bool(compra.pagado_en)
            },
            url=f'/mis-pedidos/{compra.id}'
        )

    def send_nueva_compra_admin(self, compra) -> Dict[str, Any]:
        """
        Notifica a administradores sobre una nueva compra realizada por cliente.

        Args:
            compra: Instancia del modelo Compra
        """
        titulo = '🛒 Nueva Compra Realizada'
        mensaje = f"El cliente {compra.cliente.nombre} realizó una compra #{compra.id} por ${compra.total}"

        return self.send_to_administradores(
            titulo=titulo,
            mensaje=mensaje,
            tipo='nueva_compra',
            datos_extra={
                'compra_id': compra.id,
                'cliente_id': compra.cliente.id,
                'cliente_nombre': compra.cliente.nombre,
                'total': float(compra.total),
                'items_count': compra.items.count(),
                'pagado': bool(compra.pagado_en)
            },
            url=f'/admin/compra/compra/{compra.id}/change/'
        )

    def send_nuevo_pago_admin(self, compra) -> Dict[str, Any]:
        """
        Notifica a administradores sobre un nuevo pago confirmado.

        Args:
            compra: Instancia del modelo Compra
        """
        titulo = '💰 Nuevo Pago Confirmado'
        mensaje = f"El cliente {compra.cliente.nombre} confirmó el pago de la compra #{compra.id} por ${compra.total}"

        return self.send_to_administradores(
            titulo=titulo,
            mensaje=mensaje,
            tipo='nuevo_pago',
            datos_extra={
                'compra_id': compra.id,
                'cliente_id': compra.cliente.id,
                'cliente_nombre': compra.cliente.nombre,
                'total': float(compra.total),
                'metodo_pago': getattr(compra, 'stripe_payment_intent', 'N/A')[:10] + '...' if getattr(compra, 'stripe_payment_intent', None) else 'N/A'
            },
            url=f'/admin/compra/compra/{compra.id}/change/'
        )

    def send_nueva_promocion_clientes(self, promocion) -> Dict[str, Any]:
        """
        Notifica a todos los clientes sobre una nueva promoción.

        Args:
            promocion: Instancia del modelo Promocion
        """
        if promocion.tipo_descuento == 'porcentaje':
            descuento_texto = f"{promocion.valor_descuento}% de descuento"
        else:
            descuento_texto = f"${promocion.valor_descuento} de descuento"

        titulo = '🎉 ¡Nueva Promoción Disponible!'
        mensaje = f"{descuento_texto} en {promocion.nombre}. {promocion.descripcion[:50]}..."

        return self.send_to_all_clientes(
            titulo=titulo,
            mensaje=mensaje,
            tipo='promocion',
            datos_extra={
                'promocion_id': promocion.id,
                'codigo': promocion.codigo,
                'tipo_descuento': promocion.tipo_descuento,
                'valor_descuento': float(promocion.valor_descuento),
                'monto_minimo': float(promocion.monto_minimo) if promocion.monto_minimo else None,
                'fecha_fin': promocion.fecha_fin.isoformat() if promocion.fecha_fin else None
            },
            url=f'/productos?promocion={promocion.codigo}'
        )


# Instancia singleton del servicio
push_service = PushNotificationService()

