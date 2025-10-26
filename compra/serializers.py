from rest_framework import serializers
from .models import Compra, CompraItem


class CompraItemSerializer(serializers.ModelSerializer):
    """Serializer para items de compra con información del producto"""
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_sku = serializers.CharField(source='producto.sku', read_only=True)

    class Meta:
        model = CompraItem
        fields = (
            'id',
            'producto',
            'producto_nombre',
            'producto_sku',
            'cantidad',
            'precio_unitario',
            'subtotal',
        )
        read_only_fields = ('id', 'subtotal')


class CompraSerializer(serializers.ModelSerializer):
    """Serializer para compras con items anidados"""
    items = CompraItemSerializer(many=True, read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    esta_pagada = serializers.BooleanField(read_only=True)

    class Meta:
        model = Compra
        fields = (
            'id',
            'cliente',
            'cliente_nombre',
            'fecha',
            'total',
            'observaciones',
            'pago_referencia',
            'pagado_en',
            'esta_pagada',
            'stripe_session_id',
            'stripe_payment_intent',
            'items'
        )
        read_only_fields = (
            'id',
            'fecha',
            'total',
            'pagado_en',
            'stripe_session_id',
            'stripe_payment_intent',
        )


class CompraCreateSerializer(serializers.Serializer):
    """Serializer para crear una compra con items"""
    items = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        help_text="Lista de items: [{'producto': ID, 'cantidad': N}, ...]"
    )
    observaciones = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        default=''
    )
