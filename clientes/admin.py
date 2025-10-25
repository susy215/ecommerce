from django.contrib import admin

# Register your models here.
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
	list_display = ('nombre', 'email', 'telefono', 'asignado_a', 'fecha_creacion')
	search_fields = ('nombre', 'email', 'telefono')
	list_filter = ('fecha_creacion',)

# Register your models here.
