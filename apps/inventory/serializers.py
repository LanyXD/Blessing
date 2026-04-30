from rest_framework import serializers
from .models import Item, Product, Supply, Bundle
from decimal import Decimal


class ItemSerializer(serializers.ModelSerializer):

    image = serializers.ImageField(use_url=True, required=False, allow_null=True)
    description = serializers.SerializerMethodField()

    class Meta:
        model  = Item
        fields = '__all__'
    
    def get_description(self, obj):
        """Obtiene description desde la tabla específica según el tipo."""
        if obj.type == 'bundle' and hasattr(obj, 'bundle'):
            return obj.bundle.description
        if obj.type == 'product' and hasattr(obj, 'product'):
            return obj.product.description
        if obj.type == 'supply' and hasattr(obj, 'supply'):
            return obj.supply.description
        return ''

    def update(self, instance, validated_data):
        description = self.context['request'].data.get('description', None)

        # Actualiza los campos de la tabla Item normalmente
        instance = super().update(instance, validated_data)

        # Guarda description en la tabla correcta según el tipo
        if description is not None:
            if instance.type == 'bundle' and hasattr(instance, 'bundle'):
                instance.bundle.description = description
                instance.bundle.save(update_fields=['description'])
            elif instance.type == 'product' and hasattr(instance, 'product'):
                instance.product.description = description
                instance.product.save(update_fields=['description'])
            elif instance.type == 'supply' and hasattr(instance, 'supply'):
                instance.supply.description = description
                instance.supply.save(update_fields=['description'])

        return instance

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