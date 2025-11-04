from rest_framework import serializers
from .models import Promocion, DevolucionProducto


class PromocionSerializer(serializers.ModelSerializer):
    esta_vigente = serializers.SerializerMethodField()
    
    class Meta:
        model = Promocion
        fields = [
            'id', 'codigo', 'nombre', 'descripcion',
            'tipo_descuento', 'valor_descuento', 'descuento_maximo',
            'monto_minimo', 'fecha_inicio', 'fecha_fin',
            'activa', 'usos_maximos', 'usos_actuales',
            'esta_vigente'
        ]
        read_only_fields = ['usos_actuales', 'fecha_creacion']
    
    def get_esta_vigente(self, obj):
        return obj.esta_vigente()


class DevolucionProductoSerializer(serializers.ModelSerializer):
    compra_item_info = serializers.SerializerMethodField()
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    puede_cancelar = serializers.SerializerMethodField()
    dentro_garantia = serializers.SerializerMethodField()
    
    class Meta:
        model = DevolucionProducto
        fields = [
            'id', 'compra_item', 'compra_item_info', 'cliente', 'cliente_nombre',
            'tipo', 'tipo_display', 'estado', 'estado_display',
            'motivo', 'descripcion', 'cantidad', 'monto_reembolso',
            'fecha_solicitud', 'fecha_aprobacion', 'fecha_rechazo', 'fecha_completado',
            'respuesta_admin', 'producto_reemplazo',
            'puede_cancelar', 'dentro_garantia'
        ]
        read_only_fields = [
            'monto_reembolso', 'fecha_solicitud', 'fecha_aprobacion',
            'fecha_rechazo', 'fecha_completado', 'respuesta_admin'
        ]
    
    def get_compra_item_info(self, obj):
        return {
            'id': obj.compra_item.id,
            'producto_id': obj.compra_item.producto.id,
            'producto_nombre': obj.compra_item.producto.nombre,
            'producto_sku': obj.compra_item.producto.sku,
            'cantidad_comprada': obj.compra_item.cantidad,
            'precio_unitario': str(obj.compra_item.precio_unitario),
        }
    
    def get_puede_cancelar(self, obj):
        # El cliente puede cancelar solo si está pendiente
        return obj.estado == 'pendiente'
    
    def get_dentro_garantia(self, obj):
        return obj.dentro_de_garantia(dias_garantia=30)
    
    def validate(self, data):
        # Validar que la cantidad no exceda la cantidad comprada
        if 'cantidad' in data and 'compra_item' in data:
            if data['cantidad'] > data['compra_item'].cantidad:
                raise serializers.ValidationError(
                    f"La cantidad a devolver no puede ser mayor a la cantidad comprada ({data['compra_item'].cantidad})"
                )
        
        # Si es cambio, validar garantía
        if data.get('tipo') == 'cambio':
            compra_item = data.get('compra_item')
            if compra_item:
                devolucion_temp = DevolucionProducto(compra_item=compra_item)
                if not devolucion_temp.dentro_de_garantia(dias_garantia=30):
                    raise serializers.ValidationError(
                        "El producto está fuera del período de garantía (30 días)"
                    )
        
        return data


class DevolucionCreateSerializer(serializers.ModelSerializer):
    """Serializer simplificado para crear devoluciones desde el cliente"""
    
    class Meta:
        model = DevolucionProducto
        fields = ['compra_item', 'tipo', 'motivo', 'descripcion', 'cantidad']
    
    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0")
        return value
    
    def create(self, validated_data):
        # El cliente se obtiene del usuario autenticado
        user = self.context['request'].user
        
        # Obtener o crear el cliente asociado al usuario
        from clientes.models import Cliente
        try:
            cliente = Cliente.objects.get(usuario=user)
        except Cliente.DoesNotExist:
            raise serializers.ValidationError("Usuario no tiene un perfil de cliente asociado")
        
        validated_data['cliente'] = cliente
        return super().create(validated_data)
