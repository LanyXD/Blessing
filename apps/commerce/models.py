from django.db import models
from apps.accounts.models import User
from apps.inventory.models import Item


class PurchasePlace(models.Model):
    name = models.CharField(max_length=150)
    address = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'purchase_place'

    def __str__(self):
        return self.name


class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    place = models.ForeignKey(PurchasePlace, on_delete=models.PROTECT)
    date = models.DateField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'purchase'

    def __str__(self):
        return f'Purchase {self.id} - {self.date}'


class PurchaseDetail(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'purchase_detail'


class Customer(models.Model):
    name = models.CharField(max_length=150)
    nit = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'customer'

    def __str__(self):
        return self.name


class Sale(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    date = models.DateField()
    total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'sale'

    def __str__(self):
        return f'Sale {self.id} - {self.date}'


class SaleDetail(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'sale_detail'


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('ready', 'Ready'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    date = models.DateField(auto_now_add=True)
    delivery_date = models.DateField()
    advance_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'order'

    def __str__(self):
        return f'Order {self.id} - {self.customer}'


class OrderDetail(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'order_detail'