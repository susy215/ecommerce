from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal


class Promocion(models.Model):
    """
    Promociones con descuentos.
    Puede ser por porcentaje o monto fijo.
    """
    TIPO_DESCUENTO = [
        ('porcentaje', 'Porcentaje'),
        ('monto', 'Monto Fijo'),
    ]
    
    codigo = models.CharField(max_length=50, unique=True, db_index=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    tipo_descuento = models.CharField(max_length=20, choices=TIPO_DESCUENTO, default='porcentaje')
    
    # Si es porcentaje: 10.00 = 10%
    # Si es monto: 50.00 = $50 de descuento
    valor_descuento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Límite de descuento máximo (opcional, útil para porcentajes)
    descuento_maximo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))]
    )
    
    # Compra mínima para aplicar promoción
    monto_minimo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    activa = models.BooleanField(default=True, db_index=True)
    
    # Uso limitado
    usos_maximos = models.PositiveIntegerField(null=True, blank=True, help_text="Dejar vacío para uso ilimitado")
    usos_actuales = models.PositiveIntegerField(default=0)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'promociones'
        ordering = ['-fecha_creacion']
        verbose_name = 'Promoción'
        verbose_name_plural = 'Promociones'
        indexes = [
            models.Index(fields=['codigo', 'activa']),
            models.Index(fields=['fecha_inicio', 'fecha_fin']),
        ]
    
    def __str__(self):
        if self.tipo_descuento == 'porcentaje':
            return f"{self.codigo} - {self.valor_descuento}%"
        return f"{self.codigo} - ${self.valor_descuento}"
    
    def esta_vigente(self):
        """Verifica si la promoción está vigente"""
        ahora = timezone.now()
        if not self.activa:
            return False
        if ahora < self.fecha_inicio:
            return False
        if self.fecha_fin and ahora > self.fecha_fin:
            return False
        if self.usos_maximos and self.usos_actuales >= self.usos_maximos:
            return False
        return True
    
    def calcular_descuento(self, monto_compra):
        """
        Calcula el descuento aplicable al monto de compra.
        Retorna (descuento, total_final)
        """
        # Convertir a Decimal si viene como float o int
        if not isinstance(monto_compra, Decimal):
            monto_compra = Decimal(str(monto_compra))
        
        if not self.esta_vigente():
            return Decimal('0'), monto_compra
        
        if monto_compra < self.monto_minimo:
            return Decimal('0'), monto_compra
        
        if self.tipo_descuento == 'porcentaje':
            descuento = monto_compra * (self.valor_descuento / Decimal('100'))
            if self.descuento_maximo:
                descuento = min(descuento, self.descuento_maximo)
        else:
            descuento = self.valor_descuento
        
        # No puede ser mayor al monto de compra
        descuento = min(descuento, monto_compra)
        total_final = monto_compra - descuento
        
        return descuento, total_final
    
    def incrementar_uso(self):
        """Incrementa el contador de usos"""
        self.usos_actuales += 1
        self.save(update_fields=['usos_actuales'])


class DevolucionProducto(models.Model):
    """
    Gestión de devoluciones con patrón Estado.
    Estados: pendiente → aprobada → completada / rechazada
    """
    TIPO_SOLICITUD = [
        ('devolucion', 'Devolución con Reembolso'),
        ('cambio', 'Cambio por otro Producto'),
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Revisión'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('completada', 'Completada'),
    ]
    
    # Relaciones
    compra_item = models.ForeignKey('compra.CompraItem', on_delete=models.PROTECT, related_name='devoluciones')
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.PROTECT, related_name='devoluciones')
    
    # Tipo y estado
    tipo = models.CharField(max_length=20, choices=TIPO_SOLICITUD, default='devolucion')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', db_index=True)
    
    # Motivo y descripción
    motivo = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    
    # Cantidad a devolver
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    
    # Monto a reembolsar (se calcula automáticamente)
    monto_reembolso = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    
    # Fechas importantes
    fecha_solicitud = models.DateTimeField(auto_now_add=True, db_index=True)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    fecha_rechazo = models.DateTimeField(null=True, blank=True)
    fecha_completado = models.DateTimeField(null=True, blank=True)
    
    # Respuesta del administrador
    respuesta_admin = models.TextField(blank=True)
    atendido_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='devoluciones_atendidas'
    )
    
    # Producto de reemplazo (solo si tipo='cambio')
    producto_reemplazo = models.ForeignKey(
        'productos.Producto',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usado_en_cambios'
    )
    
    class Meta:
        db_table = 'devoluciones'
        ordering = ['-fecha_solicitud']
        verbose_name = 'Devolución'
        verbose_name_plural = 'Devoluciones'
        indexes = [
            models.Index(fields=['estado', '-fecha_solicitud']),
            models.Index(fields=['cliente', '-fecha_solicitud']),
        ]
    
    def __str__(self):
        return f"Devolución #{self.id} - {self.cliente} - {self.get_estado_display()}"
    
    def save(self, *args, **kwargs):
        # Calcular monto de reembolso automáticamente
        if not self.monto_reembolso:
            self.monto_reembolso = self.compra_item.precio_unitario * self.cantidad
        super().save(*args, **kwargs)
    
    # === PATRÓN ESTADO ===
    
    def puede_aprobar(self):
        """Verifica si la devolución puede ser aprobada"""
        return self.estado == 'pendiente'
    
    def puede_rechazar(self):
        """Verifica si la devolución puede ser rechazada"""
        return self.estado == 'pendiente'
    
    def puede_completar(self):
        """Verifica si la devolución puede ser completada"""
        return self.estado == 'aprobada'
    
    def aprobar(self, usuario, respuesta=''):
        """Transición: pendiente → aprobada"""
        if not self.puede_aprobar():
            raise ValueError(f"No se puede aprobar una devolución en estado '{self.estado}'")
        
        self.estado = 'aprobada'
        self.fecha_aprobacion = timezone.now()
        self.respuesta_admin = respuesta
        self.atendido_por = usuario
        self.save()
    
    def rechazar(self, usuario, respuesta=''):
        """Transición: pendiente → rechazada"""
        if not self.puede_rechazar():
            raise ValueError(f"No se puede rechazar una devolución en estado '{self.estado}'")
        
        self.estado = 'rechazada'
        self.fecha_rechazo = timezone.now()
        self.respuesta_admin = respuesta
        self.atendido_por = usuario
        self.save()
    
    def completar(self, producto_reemplazo=None):
        """Transición: aprobada → completada"""
        if not self.puede_completar():
            raise ValueError(f"No se puede completar una devolución en estado '{self.estado}'")
        
        # Si es cambio, debe tener producto de reemplazo
        if self.tipo == 'cambio' and not producto_reemplazo:
            raise ValueError("Debe especificar el producto de reemplazo")
        
        self.estado = 'completada'
        self.fecha_completado = timezone.now()
        
        if producto_reemplazo:
            self.producto_reemplazo = producto_reemplazo
        
        # Restaurar stock del producto devuelto
        producto_original = self.compra_item.producto
        producto_original.stock += self.cantidad
        producto_original.save(update_fields=['stock'])
        
        # Reducir stock del producto de reemplazo
        if self.tipo == 'cambio' and self.producto_reemplazo:
            if not self.producto_reemplazo.tiene_stock(self.cantidad):
                raise ValueError(f"Stock insuficiente del producto de reemplazo")
            self.producto_reemplazo.reducir_stock(self.cantidad)
        
        self.save()
    
    def dentro_de_garantia(self, dias_garantia=30):
        """Verifica si la solicitud está dentro del período de garantía"""
        fecha_compra = self.compra_item.compra.fecha
        dias_transcurridos = (timezone.now() - fecha_compra).days
        return dias_transcurridos <= dias_garantia
