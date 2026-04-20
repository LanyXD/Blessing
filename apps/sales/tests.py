from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from decimal import Decimal
from apps.inventory.models import Item, Product
from apps.sales.models import Sale, SaleItem

class SalesAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('tester', 't@t.com', 'pass')
        # Crear item + product
        self.item = Item.objects.create(
            name='Rosas Rojas (Docena)',
            type='product',
            category='flores',
            unit='docena',
            stock=50,
            min_stock=10,
            purchase_price=Decimal('100.00'),
            sell_price=Decimal('150.00'),
            image=''
        )
        self.product = Product.objects.create(item=self.item, description='Docena de rosas rojas')
        # autenticar en pruebas
        self.client.force_authenticate(user=self.user)

    def test_products_list(self):
        resp = self.client.get('/api/sales/products/')
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        p = data[0]
        # verifica claves y tipos
        assert 'id' in p and isinstance(p['id'], int)
        assert p['sell_price'] == float(self.item.sell_price)
        assert p['type'] in ('product', 'bundel') or isinstance(p['type'], str)

    def test_create_sale_and_decrease_stock(self):
        payload = {
            "customer_name": "Cliente X",
            "telephone": "123",
            "nit": "",
            "address": "",
            "contact_method": "whatsapp",
            "total": "150.00",
            "items": [
                {"item_id": self.product.pk, "quantity": 1, "unit_price": "150.00"}
            ]
        }
        resp = self.client.post('/api/sales/', payload, format='json')
        assert resp.status_code == 201
        # recargar item
        self.item.refresh_from_db()
        assert self.item.stock == 49
        # revisar que la venta se creó
        assert Sale.objects.count() == 1
        assert SaleItem.objects.count() == 1