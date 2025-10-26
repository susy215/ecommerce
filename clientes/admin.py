from django.contrib import admin
from django.utils.html import format_html
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'nombre',
        'email',
        'telefono',
        'tiene_usuario',
        'asignado_a',
        'fecha_creacion'
    )
    list_filter = ('fecha_creacion', 'asignado_a')
    search_fields = ('nombre', 'email', 'telefono', 'direccion')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'usuario')
    date_hierarchy = 'fecha_creacion'
    autocomplete_fields = ['asignado_a']
    
    fieldsets = (
        ('Información del Cliente', {
            'fields': ('nombre', 'email', 'telefono', 'direccion')
        }),
        ('Relaciones', {
            'fields': ('usuario', 'asignado_a')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    def tiene_usuario(self, obj):
        if obj.usuario:
            return format_html(
                '<span style="color: green;">✓ {}</span>',
                obj.usuario.username
            )
        return format_html(
            '<span style="color: gray;">- Sin cuenta</span>'
        )
    tiene_usuario.short_description = 'Usuario'
