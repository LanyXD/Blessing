from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inventory.models import Item

from .models import Sale
from .serializers import SaleCreateSerializer, SaleOutputSerializer
from .services import create_sale


class SaleProductListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        items = (
            Item.objects
            .filter(
                is_activate=True,
                type__in=["product", "bundle"],
            )
            .select_related("category")
            .order_by("-created_at")
        )

        data = [
            {
                "id": item.id,
                "name": item.name,
                "stock": int(item.stock),
                "min_stock": int(item.min_stock),
                "sell_price": float(item.sell_price),
                "type": item.type,
                "image": (
                    request.build_absolute_uri(item.image.url)
                    if item.image
                    else None
                ),
                "category_name": (
                    item.category.name
                    if item.category
                    else None
                ),
            }
            for item in items
        ]

        return Response(data)


class SaleListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        sales = (
            Sale.objects
            .select_related("customer")
            .prefetch_related(
                "items__product__bundle__details__item"
            )
            .order_by("-created_at")
        )

        serializer = SaleOutputSerializer(
            sales,
            many=True,
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = SaleCreateSerializer(
            data=request.data,
        )
        serializer.is_valid(
            raise_exception=True,
        )

        sale = create_sale(
            serializer.validated_data,
        )

        return Response(
            SaleOutputSerializer(sale).data,
            status=status.HTTP_201_CREATED,
        )
    