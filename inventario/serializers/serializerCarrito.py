from rest_framework import serializers
from inventario.modelsCarrito import Carrito
from inventario.serializers.serializerDetalleCarrito import DetalleCarritoSerializer
import uuid


class CarritoSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    cliente_apellido = serializers.CharField(source='cliente.apellido', read_only=True)
    detalles = DetalleCarritoSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_carrito = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    esta_vacio = serializers.SerializerMethodField()
    codigo = serializers.CharField(required=False)

    class Meta:
        model = Carrito
        fields = [
            'id',
            'codigo',
            'estado',
            'cliente',
            'cliente_nombre',
            'cliente_apellido',
            'fecha_creacion',
            'fecha_actualizacion',
            'detalles',
            'total_items',
            'total_carrito',
            'esta_vacio'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion', 'total_items', 'total_carrito']

    def create(self, validated_data):
        """Genera un código único si no se proporciona"""
        if 'codigo' not in validated_data or not validated_data['codigo']:
            validated_data['codigo'] = f"CAR-{uuid.uuid4().hex[:8].upper()}"
        return super().create(validated_data)

    def get_esta_vacio(self, obj):
        """Método para obtener si el carrito está vacío"""
        return obj.esta_vacio()


class CarritoSimpleSerializer(serializers.ModelSerializer):
    """Serializer sin los detalles anidados, útil para listados"""
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_carrito = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Carrito
        fields = [
            'id',
            'codigo',
            'estado',
            'cliente',
            'cliente_nombre',
            'fecha_creacion',
            'fecha_actualizacion',
            'total_items',
            'total_carrito'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']
