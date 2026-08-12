from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from apps.inventory.models import Item, Product
from apps.sales.models import Sale, SaleItem


class SalesAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="tester",
            email="t@t.com",
            password="pass",
        )

        self.item = Item.objects.create(
            name="Rosas Rojas (Docena)",
            type="product",
            category="flores",
            unit="docena",
            stock=50,
            min_stock=10,
            purchase_price=Decimal("100.00"),
            sell_price=Decimal("150.00"),
            image="",
        )

        self.product = Product.objects.create(
            item=self.item,
            description="Docena de rosas rojas",
        )

        self.client.force_authenticate(user=self.user)

    def test_products_list(self):
        response = self.client.get("/api/sales/products/")

        assert response.status_code == 200

        data = response.json()

        assert isinstance(data, list)

        product = data[0]

        assert "id" in product
        assert isinstance(product["id"], int)
        assert product["sell_price"] == float(self.item.sell_price)
        assert product["type"] in ("product", "bundle") or isinstance(
            product["type"],
            str,
        )

    def test_create_sale_and_decrease_stock(self):
        payload = {
            "customer_name": "Cliente X",
            "telephone": "123",
            "nit": "",
            "address": "",
            "contact_method": "whatsapp",
            "total": "150.00",
            "items": [
                {
                    "item_id": self.product.pk,
                    "quantity": 1,
                    "unit_price": "150.00",
                }
            ],
        }

        response = self.client.post(
            "/api/sales/",
            payload,
            format="json",
        )

        assert response.status_code == 201

        self.item.refresh_from_db()

        assert self.item.stock == 49
        assert Sale.objects.count() == 1
        assert SaleItem.objects.count() == 1
        