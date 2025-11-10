"""
Modelos para gestión de notificaciones push web.
Usa Web Push API para enviar notificaciones a navegadores.
"""
from django.db import models
from django.conf import settings


class PushSubscription(models.Model):
    """
    Almacena las suscripciones push de los usuarios.
    Cada usuario puede tener múltiples dispositivos/navegadores suscritos.
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='push_subscriptions',
        db_index=True
    )
    endpoint = models.TextField(
        unique=True,
        help_text='URL del endpoint de push del navegador'
    )
    p256dh = models.TextField(
        help_text='Clave pública del cliente para encriptación'
    )
    auth = models.TextField(
        help_text='Token de autenticación del cliente'
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        help_text='User agent del navegador'
    )
    activa = models.BooleanField(
        default=True,
        db_index=True,
        help_text='Si la suscripción está activa'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    ultima_notificacion = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha de la última notificación enviada'
    )

    class Meta:
        db_table = 'push_subscriptions'
        ordering = ['-fecha_creacion']
        verbose_name = 'Suscripción Push'
        verbose_name_plural = 'Suscripciones Push'
        indexes = [
            models.Index(fields=['usuario', 'activa']),
            models.Index(fields=['-fecha_creacion']),
        ]

    def __str__(self):
        return f"{self.usuario.username} - {self.endpoint[:50]}..."


class NotificacionEnviada(models.Model):
    """
    Historial de notificaciones enviadas para auditoría y debugging.
    """
    TIPO_CHOICES = [
        ('compra_exitosa', 'Compra Exitosa'),
        ('cambio_estado', 'Cambio de Estado'),
        ('promocion', 'Promoción'),
        ('nueva_compra', 'Nueva Compra (Admin)'),
        ('nuevo_pago', 'Nuevo Pago (Admin)'),
        ('otro', 'Otro'),
    ]
    
    ESTADO_CHOICES = [
        ('exitoso', 'Exitoso'),
        ('fallido', 'Fallido'),
        ('pendiente', 'Pendiente'),
    ]
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificaciones_recibidas',
        db_index=True
    )
    subscription = models.ForeignKey(
        PushSubscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    tipo = models.CharField(
        max_length=50,
        choices=TIPO_CHOICES,
        db_index=True
    )
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    datos_extra = models.JSONField(
        null=True,
        blank=True,
        help_text='Datos adicionales de la notificación'
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        db_index=True
    )
    error = models.TextField(blank=True)
    fecha_envio = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'notificaciones_enviadas'
        ordering = ['-fecha_envio']
        verbose_name = 'Notificación Enviada'
        verbose_name_plural = 'Notificaciones Enviadas'
        indexes = [
            models.Index(fields=['usuario', '-fecha_envio']),
            models.Index(fields=['tipo', '-fecha_envio']),
            models.Index(fields=['estado']),
        ]
    
    def __str__(self):
        return f"{self.usuario.username} - {self.titulo} ({self.estado})"

