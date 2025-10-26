from django.contrib import admin
from django.utils.html import format_html
from .models import Producto, Categoria


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
	list_display = ('id', 'nombre', 'slug', 'cantidad_productos')
	search_fields = ('nombre', 'slug')
	prepopulated_fields = {'slug': ('nombre',)}

	def cantidad_productos(self, obj):
		count = obj.productos.count()
		return format_html(
			'<span style="color: blue;">{} productos</span>',
			count
		)
	cantidad_productos.short_description = 'Productos'


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'sku',
		'nombre',
		'categoria',
		'precio',
		'stock',
		'estado_stock',
		'activo',
		'fecha_creacion'
	)
	list_filter = ('activo', 'categoria', 'fecha_creacion')
	search_fields = ('sku', 'nombre', 'descripcion')
	readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
	list_editable = ('precio', 'stock', 'activo')
	date_hierarchy = 'fecha_creacion'
	autocomplete_fields = ['categoria']
	
	fieldsets = (
		('Información Básica', {
			'fields': ('sku', 'nombre', 'descripcion', 'categoria')
		}),
		('Precio y Stock', {
			'fields': ('precio', 'stock', 'activo')
		}),
		('Fechas', {
			'fields': ('fecha_creacion', 'fecha_actualizacion'),
			'classes': ('collapse',)
		}),
	)

	def estado_stock(self, obj):
		if obj.stock == 0:
			return format_html(
				'<span style="color: red; font-weight: bold;">⚠ Sin stock</span>'
			)
		elif obj.stock < 10:
			return format_html(
				'<span style="color: orange;">⚠ Stock bajo</span>'
			)
		return format_html(
			'<span style="color: green;">✓ En stock</span>'
		)
	estado_stock.short_description = 'Estado'
