# sales/serializers.py

from rest_framework import serializers

from .models import Sale, SaleItem


PAYMENT_METHODS = [
    'efectivo',
    'transferencia',
    'tarjeta',
]


# ── Input ──────────────────────────────────────────────────────────────────────


class SaleItemInputSerializer(serializers.Serializer):
    """Lee los items que vienen del frontend al crear una venta."""

    item_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )


class SaleCreateSerializer(serializers.Serializer):
    """Valida los datos necesarios para crear una venta."""

    # Cliente registrado
    customer_id = serializers.IntegerField(
        required=False,
        allow_null=True,
    )

    # Datos del cliente
    customer_name = serializers.CharField(
        max_length=200,
        required=True,
        allow_blank=False,
        error_messages={
            'required': 'El nombre es obligatorio.',
            'blank': 'El nombre no puede ir vacío.',
        },
    )

    telephone = serializers.CharField(
        max_length=20,
        required=True,
        allow_blank=False,
        allow_null=False,
        error_messages={
            'required': 'El teléfono es obligatorio.',
            'blank': 'El teléfono no puede ir vacío.',
            'null': 'El teléfono no puede ser null.',
        },
    )

    nit = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    address = serializers.CharField(
        max_length=300,
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    contact_method = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    # Venta
    payment_method = serializers.ChoiceField(
        choices=PAYMENT_METHODS,
        required=True,
        allow_blank=False,
        error_messages={
            'required': 'El método de pago es obligatorio.',
            'blank': 'El método de pago no puede ir vacío.',
            'invalid_choice': 'El método de pago es obligatorio.',
        },
    )

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    total = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    items = SaleItemInputSerializer(many=True)

    def validate_items(self, items):
        """Garantiza que la venta contenga al menos un producto."""

        if not items:
            raise serializers.ValidationError(
                'La venta debe tener al menos un producto.'
            )

        return items

    def validate(self, data):
        """Valida que exista un cliente registrado o un nombre manual."""

        if self._requires_customer_name(data):
            raise serializers.ValidationError({
                'customer_name': (
                    'Ingresa el nombre del cliente o '
                    'selecciona uno registrado.'
                )
            })

        return data

    @staticmethod
    def _requires_customer_name(data):
        """Indica si la venta necesita un nombre de cliente manual."""

        has_registered_customer = data.get('customer_id') is not None
        customer_name = data.get('customer_name', '').strip()

        return not has_registered_customer and not customer_name


# ── Output ─────────────────────────────────────────────────────────────────────


class SaleItemOutputSerializer(serializers.ModelSerializer):
    """Representa un producto incluido en una venta."""

    product_name = serializers.CharField(
        source='product.name',
        read_only=True,
    )

    type = serializers.CharField(
        source='product.type',
        read_only=True,
    )

    category = serializers.CharField(
        source='product.category.name',
        read_only=True,
        allow_null=True,
    )

    components = serializers.SerializerMethodField()

    class Meta:
        model = SaleItem
        fields = [
            'id',
            'product',
            'product_name',
            'type',
            'category',
            'quantity',
            'unit_price',
            'subtotal',
            'components',
        ]

    def get_components(self, sale_item):
        """Devuelve los componentes si el producto es un bundle."""

        if sale_item.product.type != 'bundle':
            return []

        return [
            {
                'name': detail.item.name,
                'quantity': detail.quantity,
            }
            for detail in (
                sale_item.product.bundle.details
                .select_related('item')
                .all()
            )
        ]


class SaleOutputSerializer(serializers.ModelSerializer):
    """Representa una venta completa para el frontend."""

    items = SaleItemOutputSerializer(
        many=True,
        read_only=True,
    )

    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = [
            'id',
            'customer',
            'customer_name',
            'telephone',
            'nit',
            'address',
            'contact_method',
            'payment_method',
            'notes',
            'total',
            'items',
            'created_at',
        ]

    def get_customer_name(self, sale):
        """Obtiene el nombre del cliente asociado a la venta."""

        return sale.get_customer_name()