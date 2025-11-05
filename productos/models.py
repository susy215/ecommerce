from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from PIL import Image


class Categoria(models.Model):
	nombre = models.CharField(max_length=100, unique=True)
	slug = models.SlugField(max_length=120, unique=True)

	class Meta:
		db_table = 'categorias'
		ordering = ['nombre']
		verbose_name = 'Categoría'
		verbose_name_plural = 'Categorías'
		indexes = [
			models.Index(fields=['nombre']),
		]

	def __str__(self):
		return self.nombre


class Producto(models.Model):
	sku = models.CharField(max_length=50, unique=True, db_index=True)
	nombre = models.CharField(max_length=150, db_index=True)
	descripcion = models.TextField(blank=True)
	precio = models.DecimalField(
		max_digits=10,
		decimal_places=2,
		validators=[MinValueValidator(Decimal('0.01'))]
	)
	stock = models.PositiveIntegerField(default=0)
	activo = models.BooleanField(default=True, db_index=True)
	categoria = models.ForeignKey(
		Categoria,
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name='productos'
	)
	imagen = models.ImageField(
		upload_to='productos/',
		blank=True,
		null=True,
		help_text='Imagen del producto (se optimizará automáticamente)'
	)
	fecha_creacion = models.DateTimeField(auto_now_add=True)
	fecha_actualizacion = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = 'productos'
		ordering = ['nombre']
		verbose_name = 'Producto'
		verbose_name_plural = 'Productos'
		indexes = [
			models.Index(fields=['activo', 'categoria']),
			models.Index(fields=['-fecha_creacion']),
		]

	def __str__(self):
		return f"{self.sku} - {self.nombre}"
	
	def tiene_stock(self, cantidad):
		"""Verifica si hay stock suficiente"""
		return self.stock >= cantidad
	
	def reducir_stock(self, cantidad):
		"""Reduce el stock de forma segura"""
		if not self.tiene_stock(cantidad):
			raise ValueError(f'Stock insuficiente para {self.nombre}. Disponible: {self.stock}')
		self.stock -= cantidad
		self.save(update_fields=['stock'])
	
	def save(self, *args, **kwargs):
		"""Optimiza la imagen al guardar"""
		super().save(*args, **kwargs)
		
		if self.imagen:
			try:
				img = Image.open(self.imagen.path)
				
				# Convertir a RGB si es necesario (para PNG con transparencia)
				if img.mode in ('RGBA', 'LA', 'P'):
					background = Image.new('RGB', img.size, (255, 255, 255))
					if img.mode == 'P':
						img = img.convert('RGBA')
					background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
					img = background
				
				# Redimensionar si es muy grande (máximo 800x800)
				if img.width > 800 or img.height > 800:
					img.thumbnail((800, 800), Image.Resampling.LANCZOS)
				
				# Guardar optimizado (calidad 85, buen balance tamaño/calidad)
				img.save(self.imagen.path, 'JPEG', quality=85, optimize=True)
				
			except Exception as e:
				# Si hay error optimizando, continuar sin optimizar
				import logging
				logger = logging.getLogger(__name__)
				logger.warning(f'Error optimizando imagen para producto {self.id}: {str(e)}')
