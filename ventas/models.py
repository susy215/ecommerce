from django.db import models
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone


class Venta(models.Model):
	ESTADOS = (
		('pendiente', 'Pendiente'),
		('pagado', 'Pagado'),
		('enviado', 'Enviado'),
		('completado', 'Completado'),
		('cancelado', 'Cancelado'),
	)
	PAGO_ESTADOS = (
		('pendiente', 'Pendiente'),
		('pagado', 'Pagado'),
		('fallido', 'Fallido'),
	)

	cliente = models.ForeignKey('clientes.Cliente', on_delete=models.PROTECT, related_name='ventas')
	vendedor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='ventas_realizadas', null=True, blank=True)
	fecha = models.DateTimeField(auto_now_add=True)
	total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	observaciones = models.CharField(max_length=255, blank=True)
	estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
	pago_estado = models.CharField(max_length=20, choices=PAGO_ESTADOS, default='pendiente')
	pago_referencia = models.CharField(max_length=100, blank=True)
	pagado_en = models.DateTimeField(null=True, blank=True)

	class Meta:
		db_table = 'ventas'
		ordering = ['-fecha']
		verbose_name = 'Venta'
		verbose_name_plural = 'Ventas'

	def __str__(self):
		return f"Venta #{self.id} - {self.cliente} - {self.fecha:%Y-%m-%d}"

	def recalc_total(self, save=True):
		total = self.items.aggregate(s=Sum('subtotal'))['s'] or 0
		self.total = total
		if save:
			self.save(update_fields=['total'])
		return total


class VentaItem(models.Model):
	venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='items')
	producto = models.ForeignKey('productos.Producto', on_delete=models.PROTECT)
	cantidad = models.PositiveIntegerField()
	precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
	subtotal = models.DecimalField(max_digits=12, decimal_places=2)

	class Meta:
		db_table = 'ventas_items'
		verbose_name = 'Item de venta'
		verbose_name_plural = 'Items de venta'

	def __str__(self):
		return f"{self.producto} x {self.cantidad}"
