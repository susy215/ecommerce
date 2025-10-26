from rest_framework import serializers
from .models import Cliente


class ClienteSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True, allow_null=True)
    asignado_a_nombre = serializers.CharField(
        source='asignado_a.get_full_name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = Cliente
        fields = (
            'id',
            'usuario',
            'usuario_username',
            'nombre',
            'email',
            'telefono',
            'direccion',
            'asignado_a',
            'asignado_a_nombre',
            'fecha_creacion',
            'fecha_actualizacion'
        )
        read_only_fields = (
            'id',
            'usuario',
            'fecha_creacion',
            'fecha_actualizacion',
            'asignado_a'
        )
