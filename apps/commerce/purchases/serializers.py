from rest_framework import serializers
from .models import PurchasePlace, Supplier, Purchase, PurchaseDetail


# ── PurchasePlace ──────────────────────────────────────────────────────────────

class PurchasePlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PurchasePlace
        fields = ['id', 'name', 'address', 'is_active']


# ── Supplier ───────────────────────────────────────────────────────────────────

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Supplier
        fields = ['id', 'name', 'contact', 'phone', 'nit', 'is_active']


# ── PurchaseDetail ─────────────────────────────────────────────────────────────

class PurchaseDetailInputSerializer(serializers.Serializer):
    """Lee los ítems que vienen del frontend al crear una compra."""
    item_id    = serializers.IntegerField()
    quantity   = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)


class PurchaseDetailOutputSerializer(serializers.ModelSerializer):
    """Devuelve los ítems al frontend."""
    item_name = serializers.CharField(source='item.name', read_only=True)

    class Meta:
        model  = PurchaseDetail
        fields = ['id', 'item', 'item_name', 'quantity', 'unit_price', 'subtotal']


# ── Purchase ───────────────────────────────────────────────────────────────────

class PurchaseOutputSerializer(serializers.ModelSerializer):
    """Devuelve una compra completa al frontend."""
    details      = PurchaseDetailOutputSerializer(many=True, read_only=True)
    supplier     = SupplierSerializer(read_only=True)
    place        = PurchasePlaceSerializer(read_only=True)
    user_display = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model  = Purchase
        fields = [
            'id', 'user', 'user_display',
            'supplier', 'place',
            'date', 'total', 'note',
            'created_at', 'details',
        ]


class PurchaseCreateSerializer(serializers.Serializer):
    """Recibe y valida el payload completo de una nueva compra."""
    supplier_id = serializers.IntegerField(required=False, allow_null=True)
    place_id    = serializers.IntegerField(required=False, allow_null=True)
    date        = serializers.DateField()
    total       = serializers.DecimalField(max_digits=10, decimal_places=2)
    note        = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    details     = PurchaseDetailInputSerializer(many=True)

    def validate(self, data):
        if not data.get('supplier_id') and not data.get('place_id'):
            raise serializers.ValidationError(
                'Una compra debe tener al menos un proveedor o un lugar.'
            )
        return data

    def validate_details(self, details):
        if len(details) == 0:
            raise serializers.ValidationError(
                'La compra debe tener al menos un ítem.'
            )
        return details
