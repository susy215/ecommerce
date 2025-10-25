from django.db import models
from django.db.models import Sum


class Compra(models.Model):
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.PROTECT, related_name='compras')
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    observaciones = models.CharField(max_length=255, blank=True)
    pago_referencia = models.CharField(max_length=100, blank=True)
    pagado_en = models.DateTimeField(null=True, blank=True)
    # Integración de pago (Stripe u otros)
    stripe_session_id = models.CharField(max_length=200, blank=True)
    stripe_payment_intent = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'compras'
        ordering = ['-fecha']
        verbose_name = 'Compra'
        verbose_name_plural = 'Compras'

    def __str__(self):
        return f"Compra #{self.id} - {self.cliente} - {self.fecha:%Y-%m-%d}"

    def recalc_total(self, save=True):
        total = self.items.aggregate(s=Sum('subtotal'))['s'] or 0
        self.total = total
        if save:
            self.save(update_fields=['total'])
        return total


class CompraItem(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey('productos.Producto', on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'compras_items'
        verbose_name = 'Item de compra'
        verbose_name_plural = 'Items de compra'

    def __str__(self):
        return f"{self.producto} x {self.cantidad}"
