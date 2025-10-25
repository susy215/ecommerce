from rest_framework import serializers
from .models import Compra


class CompraSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = Compra
        fields = (
            'id', 'cliente', 'fecha', 'total', 'observaciones',
            'pago_referencia', 'pagado_en', 'items'
        )
        read_only_fields = ('id', 'fecha', 'pagado_en',)

    def get_items(self, obj):
        return [
            {
                'id': it.id,
                'producto': it.producto_id,
                'producto_nombre': getattr(it.producto, 'nombre', ''),
                'cantidad': it.cantidad,
                'precio_unitario': str(it.precio_unitario),
                'subtotal': str(it.subtotal),
            }
            for it in obj.items.select_related('producto').all()
        ]
