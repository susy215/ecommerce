from django.db import models


class Categoria(models.Model):
	nombre = models.CharField(max_length=100, unique=True)
	slug = models.SlugField(max_length=120, unique=True)

	class Meta:
		db_table = 'categorias'
		ordering = ['nombre']
		verbose_name = 'Categoría'
		verbose_name_plural = 'Categorías'

	def __str__(self):
		return self.nombre


class Producto(models.Model):
	sku = models.CharField(max_length=50, unique=True)
	nombre = models.CharField(max_length=150)
	descripcion = models.TextField(blank=True)
	precio = models.DecimalField(max_digits=10, decimal_places=2)
	stock = models.PositiveIntegerField(default=0)
	activo = models.BooleanField(default=True)
	categoria = models.ForeignKey(Categoria, null=True, blank=True, on_delete=models.SET_NULL, related_name='productos')
	fecha_creacion = models.DateTimeField(auto_now_add=True)
	fecha_actualizacion = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = 'productos'
		ordering = ['nombre']
		verbose_name = 'Producto'
		verbose_name_plural = 'Productos'

	def __str__(self):
		return f"{self.sku} - {self.nombre}"
