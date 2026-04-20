# sales/serializers.py

from rest_framework import serializers
from .models import Sale, SaleItem
from apps.inventory.models import Product


class SaleItemInputSerializer(serializers.Serializer):
    """Para leer los items que vienen del frontend al crear una venta."""
    item_id    = serializers.IntegerField()
    quantity   = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)


class SaleItemOutputSerializer(serializers.ModelSerializer):
    """Para devolver los items al frontend."""
    product_name = serializers.CharField(source='product.item.name', read_only=True)

    class Meta:
        model  = SaleItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price', 'subtotal']


class SaleOutputSerializer(serializers.ModelSerializer):
    """Para devolver una venta completa al frontend."""
    items = SaleItemOutputSerializer(many=True, read_only=True)

    class Meta:
        model  = Sale
        fields = [
            'id', 'customer_name', 'telephone', 'nit',
            'address', 'contact_method', 'total', 'items', 'created_at',
        ]


class SaleCreateSerializer(serializers.Serializer):
    """Para recibir y validar el payload completo de nueva venta."""
    customer_name  = serializers.CharField(max_length=200)
    telephone      = serializers.CharField(max_length=20)
    nit            = serializers.CharField(max_length=20, required=False, allow_null=True, allow_blank=True)
    address        = serializers.CharField(max_length=300, required=False, allow_null=True, allow_blank=True)
    contact_method = serializers.CharField(max_length=20, required=False, allow_null=True, allow_blank=True)
    total          = serializers.DecimalField(max_digits=10, decimal_places=2)
    items          = SaleItemInputSerializer(many=True)

    def validate_items(self, items):
        if len(items) == 0:
            raise serializers.ValidationError('La venta debe tener al menos un producto.')
        return items