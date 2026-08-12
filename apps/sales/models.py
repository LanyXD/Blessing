from django.db import models
from apps.customers.models import Customer
from apps.inventory.models import Item


class Sale(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ("efectivo", "Efectivo"),
        ("transferencia", "Transferencia"),
        ("tarjeta", "Tarjeta"),
    ]

    CONTACT_METHOD_CHOICES = [
        ("whatsapp", "WhatsApp"),
        ("tienda", "En tienda"),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sales",
    )

    customer_name = models.CharField(
        max_length=200,
        blank=True,
    )
    telephone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )
    nit = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )
    address = models.CharField(
        max_length=300,
        blank=True,
        null=True,
    )
    contact_method = models.CharField(
        max_length=20,
        choices=CONTACT_METHOD_CHOICES,
        blank=True,
        null=True,
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default="efectivo",
    )
    notes = models.TextField(
        blank=True,
        null=True,
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"

    def get_customer_name(self):
        """Retorna el nombre del cliente registrado o el ingresado manualmente."""
        if self.customer:
            return self.customer.name

        return self.customer_name or "Cliente general"

    def __str__(self):
        return f"Venta #{self.id} - {self.get_customer_name()}"


class SaleItem(models.Model):
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    def __str__(self):
        return f"{self.quantity}x {self.product.name} (Venta #{self.sale_id})"
    