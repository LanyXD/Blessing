from rest_framework import serializers
from .models import Item, Product, Supply, Bundle
from decimal import Decimal


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Item
        fields = '__all__'

    # validate_<field> asocia el error al campo correcto
    # DRF lo ejecuta antes que validate() general
    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError(
                'El stock no puede ser negativo.'
            )
        return value

    def validate_min_stock(self, value):
        if value < 0:
            raise serializers.ValidationError(
                'El stock mínimo no puede ser negativo.'
            )
        return value

    def validate_purchase_price(self, value):
        if value is not None and Decimal(str(value)) < Decimal('0'):
            raise serializers.ValidationError(
                'El precio de compra no puede ser negativo.'
            )
        return value

    def validate_sell_price(self, value):
        if value is not None and Decimal(str(value)) < Decimal('0'):
            raise serializers.ValidationError(
                'El precio de venta no puede ser negativo.'
            )
        return value


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Product
        fields = '__all__'


class SupplySerializer(serializers.ModelSerializer):
    class Meta:
        model  = Supply
        fields = '__all__'


class BundleSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Bundle
        fields = '__all__'