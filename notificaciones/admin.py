"""
Administración de notificaciones push en Django Admin.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import PushSubscription, NotificacionEnviada


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'usuario', 'endpoint_corto', 'activa_badge',
        'user_agent_corto', 'fecha_creacion', 'ultima_notificacion'
    ]
    list_filter = ['activa', 'fecha_creacion']
    search_fields = ['usuario__username', 'usuario__email', 'endpoint', 'user_agent']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    date_hierarchy = 'fecha_creacion'
    
    fieldsets = (
        ('Usuario', {
            'fields': ('usuario', 'activa')
        }),
        ('Información de Suscripción', {
            'fields': ('endpoint', 'p256dh', 'auth', 'user_agent')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion', 'ultima_notificacion'),
            'classes': ('collapse',)
        }),
    )
    
    def endpoint_corto(self, obj):
        """Muestra solo los primeros caracteres del endpoint"""
        return obj.endpoint[:50] + '...' if len(obj.endpoint) > 50 else obj.endpoint
    endpoint_corto.short_description = 'Endpoint'
    
    def user_agent_corto(self, obj):
        """Muestra solo los primeros caracteres del user agent"""
        if not obj.user_agent:
            return '-'
        return obj.user_agent[:40] + '...' if len(obj.user_agent) > 40 else obj.user_agent
    user_agent_corto.short_description = 'Navegador'
    
    def activa_badge(self, obj):
        """Badge visual para el estado activo"""
        if obj.activa:
            return format_html(
                '<span style="background:#27ae60;color:white;padding:3px 8px;border-radius:3px;font-size:11px;">✓ Activa</span>'
            )
        return format_html(
            '<span style="background:#95a5a6;color:white;padding:3px 8px;border-radius:3px;font-size:11px;">✗ Inactiva</span>'
        )
    activa_badge.short_description = 'Estado'
    
    actions = ['activar_suscripciones', 'desactivar_suscripciones']
    
    def activar_suscripciones(self, request, queryset):
        """Acción para activar múltiples suscripciones"""
        updated = queryset.update(activa=True)
        self.message_user(request, f'{updated} suscripción(es) activada(s).')
    activar_suscripciones.short_description = 'Activar suscripciones seleccionadas'
    
    def desactivar_suscripciones(self, request, queryset):
        """Acción para desactivar múltiples suscripciones"""
        updated = queryset.update(activa=False)
        self.message_user(request, f'{updated} suscripción(es) desactivada(s).')
    desactivar_suscripciones.short_description = 'Desactivar suscripciones seleccionadas'


@admin.register(NotificacionEnviada)
class NotificacionEnviadaAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'usuario', 'tipo_badge', 'titulo', 'estado_badge',
        'fecha_envio'
    ]
    list_filter = ['tipo', 'estado', 'fecha_envio']
    search_fields = ['usuario__username', 'titulo', 'mensaje']
    readonly_fields = ['usuario', 'subscription', 'tipo', 'titulo', 'mensaje', 
                      'datos_extra', 'estado', 'error', 'fecha_envio']
    date_hierarchy = 'fecha_envio'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('usuario', 'subscription', 'tipo', 'estado')
        }),
        ('Contenido', {
            'fields': ('titulo', 'mensaje', 'datos_extra')
        }),
        ('Error', {
            'fields': ('error',),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('fecha_envio',)
        }),
    )
    
    def has_add_permission(self, request):
        """No se pueden crear notificaciones manualmente desde el admin"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """No se pueden editar notificaciones"""
        return False
    
    def tipo_badge(self, obj):
        """Badge visual para el tipo de notificación"""
        colores = {
            'compra_exitosa': '#27ae60',
            'cambio_estado': '#3498db',
            'promocion': '#f39c12',
            'otro': '#95a5a6',
        }
        return format_html(
            '<span style="background:{};color:white;padding:3px 8px;border-radius:3px;font-size:11px;">{}</span>',
            colores.get(obj.tipo, '#95a5a6'),
            obj.get_tipo_display()
        )
    tipo_badge.short_description = 'Tipo'
    
    def estado_badge(self, obj):
        """Badge visual para el estado de envío"""
        colores = {
            'exitoso': '#27ae60',
            'fallido': '#e74c3c',
            'pendiente': '#f39c12',
        }
        return format_html(
            '<span style="background:{};color:white;padding:3px 8px;border-radius:3px;font-size:11px;">{}</span>',
            colores.get(obj.estado, '#95a5a6'),
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'

