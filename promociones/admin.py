from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Promocion, DevolucionProducto


@admin.register(Promocion)
class PromocionAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'tipo_badge', 'valor_badge', 'vigencia_badge', 'usos_info', 'activa']
    list_filter = ['activa', 'tipo_descuento', 'fecha_inicio', 'fecha_fin']
    search_fields = ['codigo', 'nombre', 'descripcion']
    readonly_fields = ['usos_actuales', 'fecha_creacion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion', 'activa')
        }),
        ('Configuración de Descuento', {
            'fields': ('tipo_descuento', 'valor_descuento', 'descuento_maximo', 'monto_minimo')
        }),
        ('Vigencia', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
        ('Límites de Uso', {
            'fields': ('usos_maximos', 'usos_actuales')
        }),
    )
    
    def tipo_badge(self, obj):
        color = '#3498db' if obj.tipo_descuento == 'porcentaje' else '#2ecc71'
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>',
            color,
            obj.get_tipo_descuento_display()
        )
    tipo_badge.short_description = 'Tipo'
    
    def valor_badge(self, obj):
        if obj.tipo_descuento == 'porcentaje':
            texto = f"{obj.valor_descuento}%"
        else:
            texto = f"${obj.valor_descuento}"
        return format_html(
            '<strong style="color:#e74c3c; font-size:14px;">{}</strong>',
            texto
        )
    valor_badge.short_description = 'Descuento'
    
    def vigencia_badge(self, obj):
        if obj.esta_vigente():
            return format_html(
                '<span style="color:#27ae60;">● Vigente</span>'
            )
        return format_html(
            '<span style="color:#e74c3c;">● No vigente</span>'
        )
    vigencia_badge.short_description = 'Estado'
    
    def usos_info(self, obj):
        if obj.usos_maximos:
            porcentaje = (obj.usos_actuales / obj.usos_maximos) * 100
            color = '#e74c3c' if porcentaje >= 90 else '#f39c12' if porcentaje >= 70 else '#27ae60'
            return format_html(
                '<span style="color:{};">{} / {}</span>',
                color,
                obj.usos_actuales,
                obj.usos_maximos
            )
        return format_html('<span style="color:#95a5a6;">{} / ∞</span>', obj.usos_actuales)
    usos_info.short_description = 'Usos'


@admin.register(DevolucionProducto)
class DevolucionProductoAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'tipo_badge', 'estado_badge', 'producto_info', 'cantidad', 'monto_reembolso', 'fecha_solicitud']
    list_filter = ['estado', 'tipo', 'fecha_solicitud']
    search_fields = ['motivo', 'descripcion', 'cliente__nombre', 'cliente__email']
    readonly_fields = ['fecha_solicitud', 'fecha_aprobacion', 'fecha_rechazo', 'fecha_completado', 'monto_reembolso']
    
    fieldsets = (
        ('Información de la Devolución', {
            'fields': ('compra_item', 'cliente', 'tipo', 'cantidad')
        }),
        ('Motivo', {
            'fields': ('motivo', 'descripcion')
        }),
        ('Estado Actual', {
            'fields': ('estado', 'monto_reembolso')
        }),
        ('Respuesta del Administrador', {
            'fields': ('atendido_por', 'respuesta_admin', 'producto_reemplazo')
        }),
        ('Fechas de Transición', {
            'fields': ('fecha_solicitud', 'fecha_aprobacion', 'fecha_rechazo', 'fecha_completado'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['aprobar_devoluciones', 'rechazar_devoluciones']
    
    def tipo_badge(self, obj):
        color = '#3498db' if obj.tipo == 'devolucion' else '#9b59b6'
        icono = '↩' if obj.tipo == 'devolucion' else '⇄'
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:3px;">{} {}</span>',
            color,
            icono,
            obj.get_tipo_display()
        )
    tipo_badge.short_description = 'Tipo'
    
    def estado_badge(self, obj):
        colores = {
            'pendiente': '#f39c12',
            'aprobada': '#27ae60',
            'rechazada': '#e74c3c',
            'completada': '#2ecc71',
        }
        return format_html(
            '<span style="background:{}; color:white; padding:5px 10px; border-radius:3px; font-weight:bold;">{}</span>',
            colores.get(obj.estado, '#95a5a6'),
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def producto_info(self, obj):
        return format_html(
            '<strong>{}</strong><br><small style="color:#7f8c8d;">{}</small>',
            obj.compra_item.producto.nombre,
            obj.compra_item.producto.sku
        )
    producto_info.short_description = 'Producto'
    
    def aprobar_devoluciones(self, request, queryset):
        aprobadas = 0
        for devolucion in queryset:
            if devolucion.puede_aprobar():
                devolucion.aprobar(usuario=request.user, respuesta='Aprobado desde admin')
                aprobadas += 1
        self.message_user(request, f'{aprobadas} devolución(es) aprobada(s)')
    aprobar_devoluciones.short_description = "✓ Aprobar devoluciones seleccionadas"
    
    def rechazar_devoluciones(self, request, queryset):
        rechazadas = 0
        for devolucion in queryset:
            if devolucion.puede_rechazar():
                devolucion.rechazar(usuario=request.user, respuesta='Rechazado desde admin')
                rechazadas += 1
        self.message_user(request, f'{rechazadas} devolución(es) rechazada(s)')
    rechazar_devoluciones.short_description = "✗ Rechazar devoluciones seleccionadas"
