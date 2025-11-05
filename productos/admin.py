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
		'imagen_thumbnail',
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
	readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'imagen_preview')
	list_editable = ('precio', 'stock', 'activo')
	date_hierarchy = 'fecha_creacion'
	autocomplete_fields = ['categoria']
	
	fieldsets = (
		('Información Básica', {
			'fields': ('sku', 'nombre', 'descripcion', 'categoria')
		}),
		('Imagen', {
			'fields': ('imagen', 'imagen_preview'),
			'description': 'La imagen se optimizará automáticamente al guardar (máx. 800x800px, calidad 85%)'
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
	
	def imagen_thumbnail(self, obj):
		"""Muestra miniatura de la imagen en la lista"""
		if obj.imagen:
			return format_html(
				'<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />',
				obj.imagen.url
			)
		return format_html('<span style="color: #999;">Sin imagen</span>')
	imagen_thumbnail.short_description = 'Imagen'
	
	def imagen_preview(self, obj):
		"""Muestra vista previa grande de la imagen en el formulario"""
		if obj.imagen:
			return format_html(
				'<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
				obj.imagen.url
			)
		return format_html('<p style="color: #999;">No hay imagen cargada</p>')
	imagen_preview.short_description = 'Vista Previa'
