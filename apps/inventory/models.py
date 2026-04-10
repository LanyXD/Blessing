from django.db import models


class Item(models.Model):
    TYPE_CHOICES = [
        ('product', 'Product'),
        ('supply', 'Supply'),
        ('bundle', 'Bundle'),
    ]

    name = models.CharField(max_length=150)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    category = models.CharField(max_length=100)
    unit = models.CharField(max_length=20)
    stock = models.IntegerField(default=0)
    min_stock = models.IntegerField(default=0)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sell_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    image = models.CharField(max_length=500, blank=True)
    is_activate = models.BooleanField(default=True)
    created_at = models.DateField(auto_now_add=True)

    def adjust_stock(self, delta, reason='bundle adjustment', reference_table='', reference_id=None):
        """Ajusta el stock del item y registra un movimiento de inventario."""
        new_stock = self.stock + delta
        if new_stock < 0:
            raise ValueError('No hay suficiente stock para esta operación')
        self.stock = new_stock
        self.save(update_fields=['stock'])
        InventoryMovement.objects.create(
            item=self,
            movement_type='in' if delta > 0 else 'out',
            reason=reason,
            reference_table=reference_table or '',
            reference_id=reference_id,
            quantity=abs(delta),
        )

    @property
    def has_stock_history(self):
        return self.movements.exists()

    @property
    def has_components(self):
        return self.type == 'bundle' and hasattr(self, 'bundle') and self.bundle.details.exists()

    @property
    def is_used_in_any_bundle(self):
        return self.used_in_bundles.exists()

    def can_change_type(self):
        return not (self.has_components or self.is_used_in_any_bundle or self.has_stock_history)

    def restore_stock_from_bundle(self):
        """Restaura el stock de los componentes usados por un bundle antes de eliminarlo."""
        if self.type != 'bundle' or not hasattr(self, 'bundle'):
            return
        for detail in self.bundle.details.select_related('item').all():
            if detail.quantity > 0:
                detail.item.adjust_stock(
                    detail.quantity,
                    reason='bundle deleted',
                    reference_table='Bundle',
                    reference_id=self.bundle.pk,
                )

    def __str__(self):
        return self.name

class Product(models.Model):
    item = models.OneToOneField(
        'inventory.Item',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='product'
    )
    description = models.TextField()

    def __str__(self):
        return f"Product: {self.item.name}"

class Supply(models.Model):
    item = models.OneToOneField(
        'inventory.Item',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='supply'
    )
    entry_date = models.DateField()
    is_sellable = models.BooleanField(default=False)

    def __str__(self):
        return f"Supply: {self.item.name}"
    
class Bundle(models.Model):
    item = models.OneToOneField(
        'inventory.Item',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='bundle'
    )
    description = models.TextField()

    def __str__(self):
        return f"Bundle: {self.item.name}"
    
class BundleDetail(models.Model):
    item = models.ForeignKey(
        'inventory.Item',
        on_delete=models.CASCADE,
        related_name='used_in_bundles'
    )
    bundle = models.ForeignKey(
        'inventory.Bundle',
        on_delete=models.CASCADE,
        related_name='details'
    )
    quantity = models.IntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.item.name} in {self.bundle.item.name}"
    
class InventoryMovement(models.Model):
    TYPE_CHOICES = [
        ('in', 'In'),
        ('out', 'Out'),
    ]

    item = models.ForeignKey(
        'inventory.Item',
        on_delete=models.CASCADE,
        related_name='movements'
    )
    movement_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    reason = models.CharField(max_length=30)
    reference_id = models.IntegerField(null=True, blank=True)
    reference_table = models.CharField(max_length=50, blank=True)
    quantity = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.movement_type} - {self.item.name} ({self.quantity})"
