from django.db import transaction

from apps.customers.models import Customer
from apps.inventory.models import Item

from .models import Sale, SaleItem


@transaction.atomic
def create_sale(data):
    customer = _get_customer(data.get("customer_id"))

    sale = Sale.objects.create(
        customer=customer,
        customer_name=data.get("customer_name") or "",
        telephone=data.get("telephone") or "",
        nit=data.get("nit") or "",
        address=data.get("address") or "",
        contact_method=data.get("contact_method") or "",
        payment_method=data.get("payment_method", "efectivo"),
        notes=data.get("notes") or "",
        total=data["total"],
    )

    _create_sale_items(
        sale,
        data["items"],
    )

    return sale


def _get_customer(customer_id):
    if not customer_id:
        return None

    try:
        return Customer.objects.get(
            id=customer_id,
            is_active=True,
        )
    except Customer.DoesNotExist:
        raise ValueError(
            "El cliente seleccionado no existe."
        )


def _create_sale_items(sale, items):
    for item_data in items:
        item = Item.objects.select_for_update().get(
            id=item_data["item_id"],
        )

        _validate_stock(
            item,
            item_data["quantity"],
        )

        item.stock -= item_data["quantity"]
        item.save()

        SaleItem.objects.create(
            sale=sale,
            product=item,
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            subtotal=(
                item_data["unit_price"]
                * item_data["quantity"]
            ),
        )


def _validate_stock(item, quantity):
    if item.stock < quantity:
        raise ValueError(
            f'Stock insuficiente para "{item.name}". '
            f"Disponible: {item.stock}"
        )
    