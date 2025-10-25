from rest_framework import serializers
from .models import Venta, VentaItem


class VentaItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = VentaItem
        fields = ('id', 'producto', 'cantidad', 'precio_unitario', 'subtotal')
        read_only_fields = ('id',)


class VentaSerializer(serializers.ModelSerializer):
    items = VentaItemSerializer(many=True, read_only=True)

    class Meta:
        model = Venta
        fields = (
            'id', 'cliente', 'vendedor', 'fecha', 'total', 'observaciones',
            'estado', 'pago_estado', 'pago_referencia', 'pagado_en', 'items'
        )
        read_only_fields = ('id', 'fecha', 'vendedor', 'pagado_en',)
