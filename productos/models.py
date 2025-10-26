from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


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
