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
