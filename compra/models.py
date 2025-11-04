from django.db import models
from django.db.models import Sum
from django.core.validators import MinValueValidator
from decimal import Decimal


class Compra(models.Model):
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.PROTECT, related_name='compras')
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    observaciones = models.CharField(max_length=255, blank=True)
    pago_referencia = models.CharField(max_length=100, blank=True)
    pagado_en = models.DateTimeField(null=True, blank=True, db_index=True)
    # Integración de pago (Stripe u otros)
    stripe_session_id = models.CharField(max_length=200, blank=True)
    stripe_payment_intent = models.CharField(max_length=200, blank=True, db_index=True)
    # Promoción aplicada
    promocion = models.ForeignKey(
        'promociones.Promocion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='compras'
    )
    descuento_aplicado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )

    class Meta:
        db_table = 'compras'
        ordering = ['-fecha']
        verbose_name = 'Compra'
        verbose_name_plural = 'Compras'
        indexes = [
            models.Index(fields=['cliente', '-fecha']),
            models.Index(fields=['pagado_en']),
        ]

    def __str__(self):
        return f"Compra #{self.id} - {self.cliente} - {self.fecha:%Y-%m-%d}"

    def recalc_total(self, save=True):
        """Recalcula el total de la compra con descuento aplicado"""
        subtotal = self.items.aggregate(s=Sum('subtotal'))['s'] or 0
        total = subtotal - self.descuento_aplicado
        self.total = max(total, 0)  # No puede ser negativo
        if save:
            self.save(update_fields=['total'])
        return self.total
    
    def aplicar_promocion(self, promocion):
        """Aplica una promoción a la compra"""
        subtotal = self.items.aggregate(s=Sum('subtotal'))['s'] or 0
        descuento, total_final = promocion.calcular_descuento(subtotal)
        
        self.promocion = promocion
        self.descuento_aplicado = descuento
        self.total = total_final
        self.save()
        
        # Incrementar uso de la promoción
        promocion.incrementar_uso()
        
        return descuento
    
    @property
    def esta_pagada(self):
        """Verifica si la compra está pagada"""
        return self.pagado_en is not None


class CompraItem(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey('productos.Producto', on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )

    class Meta:
        db_table = 'compras_items'
        verbose_name = 'Item de compra'
        verbose_name_plural = 'Items de compra'
        indexes = [
            models.Index(fields=['compra', 'producto']),
        ]

    def __str__(self):
        return f"{self.producto} x {self.cantidad}"
    
    def save(self, *args, **kwargs):
        """Auto-calcula el subtotal antes de guardar"""
        self.subtotal = self.precio_unitario * self.cantidad
        super().save(*args, **kwargs)
