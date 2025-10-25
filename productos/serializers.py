from rest_framework import serializers
from .models import Producto, Categoria


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ('id', 'nombre', 'slug')


class ProductoSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer(read_only=True)
    categoria_id = serializers.PrimaryKeyRelatedField(source='categoria', queryset=Categoria.objects.all(), write_only=True, allow_null=True, required=False)
    class Meta:
        model = Producto
        fields = (
            'id', 'sku', 'nombre', 'descripcion', 'precio', 'stock', 'activo',
            'categoria', 'categoria_id', 'fecha_creacion', 'fecha_actualizacion'
        )
        read_only_fields = ('id', 'fecha_creacion', 'fecha_actualizacion')
