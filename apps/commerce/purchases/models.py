from django.db import models
from django.core.exceptions import ValidationError
from apps.accounts.models import User
from apps.inventory.models import Item


class PurchasePlace(models.Model):
    name      = models.CharField(max_length=150)
    address   = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'commerce'
        db_table  = 'purchase_place'

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name      = models.CharField(max_length=150)
    contact   = models.CharField(max_length=150, blank=True, null=True)
    phone     = models.CharField(max_length=20,  blank=True, null=True)
    nit       = models.CharField(max_length=20,  blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'commerce'
        db_table  = 'supplier'

    def __str__(self):
        return self.name


class Purchase(models.Model):
    user       = models.ForeignKey(User, on_delete=models.PROTECT)
    supplier   = models.ForeignKey(
        Supplier, on_delete=models.PROTECT,
        null=True, blank=True
    )
    place      = models.ForeignKey(
        PurchasePlace, on_delete=models.PROTECT,
        null=True, blank=True
    )
    date       = models.DateField()
    total      = models.DecimalField(max_digits=10, decimal_places=2)
    note       = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'commerce'
        db_table  = 'purchase'

    def clean(self):
        if not self.supplier_id and not self.place_id:
            raise ValidationError(
                'Una compra debe tener al menos un proveedor o un lugar.'
            )

    def __str__(self):
        ref = self.supplier or self.place
        return f'Compra #{self.id} - {ref} ({self.date})'


class PurchaseDetail(models.Model):
    purchase   = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='details')
    item       = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity   = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal   = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        app_label = 'commerce'
        db_table  = 'purchase_detail'

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)

        if is_new:
            self.item.adjust_stock(
                delta=self.quantity,
                reason='purchase',
                reference_table='purchase',
                reference_id=self.purchase_id,
            )

    def __str__(self):
        return f'{self.quantity}x {self.item} - Compra #{self.purchase_id}'
