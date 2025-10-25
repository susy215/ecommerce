from django.contrib import admin
from .models import Producto, Categoria


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
	list_display = ('sku', 'nombre', 'precio', 'stock', 'activo', 'categoria', 'fecha_creacion')
	search_fields = ('sku', 'nombre')
	list_filter = ('activo', 'categoria')


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
	list_display = ('nombre', 'slug')
	search_fields = ('nombre', 'slug')
