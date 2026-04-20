# sales/models.py

from django.db import models
from apps.inventory.models import Item  # ajusta el import según tu app


class Sale(models.Model):
    # Datos del cliente
    customer_name   = models.CharField(max_length=200)
    telephone       = models.CharField(max_length=20)
    nit             = models.CharField(max_length=20, blank=True, null=True)
    address         = models.CharField(max_length=300, blank=True, null=True)
    contact_method  = models.CharField(
        max_length=20,
        choices=[('whatsapp', 'WhatsApp'), ('tienda', 'En tienda')],
        blank=True,
        null=True,
    )

    # Totales
    total           = models.DecimalField(max_digits=10, decimal_places=2)

    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Venta #{self.id} - {self.customer_name}'


class SaleItem(models.Model):
    sale            = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product         = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity        = models.PositiveIntegerField()
    unit_price      = models.DecimalField(max_digits=10, decimal_places=2)

    # Subtotal guardado para no depender del precio actual del producto
    subtotal        = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        # Access product safely: product may be None during admin object creation/logging
        # Use product_id to avoid extra DB lookup when FK isn't set yet
        if not getattr(self, 'product_id', None):
            return f'{self.quantity}x <no product>'

        # product exists (or at least product_id does). Try to get a readable name
        try:
            # If Product stores its name on a related Item, adapt accordingly
            name = getattr(self.product, 'name', None) or getattr(getattr(self.product, 'item', None), 'name', None)
        except Exception:
            name = None

        if not name:
            name = '<no product>'

        return f'{self.quantity}x {name}'