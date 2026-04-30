# sales/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db import transaction

from .models import Sale, SaleItem
from .serializers import SaleCreateSerializer, SaleOutputSerializer
from apps.inventory.models import Item


class SaleProductListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Devuelve productos y bundles activos para agregar a una venta."""
        items = Item.objects.filter(
            is_activate=True,
            type__in=['product', 'bundle'],
        )

        data = [
            {
                'id':            item.id,
                'name':          item.name,
                'stock':         int(item.stock),
                'stock_minimum': int(item.min_stock),
                'sell_price':    float(item.sell_price),
                'type':          item.type,       # 'product' | 'bundle' — tal cual está en la BD
                'image': request.build_absolute_uri(item.image.url) if item.image else None,

            }
            for item in items
        ]

        return Response(data)


class SaleListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Devuelve todas las ventas ordenadas por más reciente."""
        sales = Sale.objects.prefetch_related('items__product').order_by('-created_at')
        serializer = SaleOutputSerializer(sales, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = SaleCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:                                    # ← agrega try/except
            with transaction.atomic():
                sale = Sale.objects.create(
                    customer_name  = data['customer_name'],
                    telephone      = data['telephone'],
                    nit            = data.get('nit') or '',
                    address        = data.get('address') or '',
                    contact_method = data.get('contact_method') or '',
                    total          = data['total'],
                )

                for item_data in data['items']:
                    item = Item.objects.select_for_update().get(id=item_data['item_id'])

                    if item.stock < item_data['quantity']:
                        return Response(
                            {'detail': f'Stock insuficiente para {item.name}. Disponible: {item.stock}'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    item.stock -= item_data['quantity']
                    item.save()

                    SaleItem.objects.create(
                        sale       = sale,
                        product    = item,
                        quantity   = item_data['quantity'],
                        unit_price = item_data['unit_price'],
                        subtotal   = item_data['unit_price'] * item_data['quantity'],
                    )

            return Response(
                SaleOutputSerializer(sale).data,
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            print('ERROR EN POST SALE:', str(e))   # ← imprime en terminal Django
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )