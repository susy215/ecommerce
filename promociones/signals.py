"""
Señales para el modelo de Promociones.
Se activa cuando se crea una nueva promoción desde el admin para notificar a clientes.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps

logger = logging.getLogger(__name__)


@receiver(post_save, sender='promociones.Promocion')
def notificar_promocion_clientes(sender, instance, created, **kwargs):
    """
    Señal que se activa cuando se guarda una promoción.
    Solo notifica cuando se crea una nueva promoción (no cuando se actualiza).
    """
    if created and instance.activa:
        try:
            logger.info(f'Enviando notificación de nueva promoción: {instance.nombre} ({instance.codigo})')

            # Importar aquí para evitar dependencias circulares
            from notificaciones.push_service import push_service
            resultado = push_service.send_nueva_promocion_clientes(instance)

            logger.info(
                f'Notificación de promoción enviada: '
                f'{resultado.get("clientes_notificados", 0)} clientes notificados, '
                f'{resultado.get("total_exitosos", 0)} envíos exitosos, '
                f'{resultado.get("total_fallidos", 0)} fallidos'
            )

        except Exception as e:
            logger.error(f'Error al enviar notificación de promoción {instance.id}: {str(e)}', exc_info=True)
