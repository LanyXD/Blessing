# from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from .models import Item, Product, Supply, Bundle, BundleDetail
from .serializers import (
    ItemSerializer,
    ProductSerializer,
    SupplySerializer,
    BundleSerializer
)


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        item_type = data.get('type')

        # Fields for Item model
        item_fields = ['name', 'type', 'category', 'unit', 'stock', 'min_stock', 'purchase_price', 'sell_price', 'image']
        item_data = {k: v for k, v in data.items() if k in item_fields}

        item_serializer = self.get_serializer(data=item_data)
        item_serializer.is_valid(raise_exception=True)
        item = item_serializer.save()

        # Create related model based on type
        if item_type == 'product':
            description = data.get('description', '')
            Product.objects.create(item=item, description=description)
        elif item_type == 'supply':
            entry_date = data.get('entry_date', timezone.now().date())
            Supply.objects.create(item=item, entry_date=entry_date)
        elif item_type == 'bundle':
            description = data.get('description', '')
            Bundle.objects.create(item=item, description=description)
            # Materiales se agregan después vía /api/bundles/{id}/materials/

        return Response(item_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='materials')
    def get_materials(self, request, pk=None):
        """
        GET /api/items/{id}/materials/
        Obtiene los materiales de un bundle.
        """
        item = self.get_object()
        if item.type != 'bundle':
            return Response({'error': 'Item is not a bundle'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            bundle = item.bundle
        except Bundle.DoesNotExist:
            return Response({'error': 'Bundle not found'}, status=status.HTTP_404_NOT_FOUND)
        
        details = BundleDetail.objects.filter(bundle=bundle).select_related('item')
        materials = [
            {
                'productId': detail.item.id,
                'name': detail.item.name,
                'quantity': detail.quantity,
            }
            for detail in details
        ]
        return Response(materials)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class SupplyViewSet(viewsets.ModelViewSet):
    queryset = Supply.objects.all()
    serializer_class = SupplySerializer


class BundleViewSet(viewsets.ModelViewSet):
    queryset = Bundle.objects.all()
    serializer_class = BundleSerializer

    @action(detail=True, methods=['post'], url_path='materials')
    def add_materials(self, request, pk=None):
        """
        POST /api/bundles/{id}/materials/
        Agrega/reemplaza materiales de un bundle.
        
        Expected body: [
            {"item": 3, "quantity": 1},
            {"item": 8, "quantity": 2}
        ]
        """
        bundle = self.get_object()
        materials = request.data

        if not isinstance(materials, list):
            return Response(
                {'error': 'Expected a list of materials'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar que todos los items existan antes de hacer cambios
        for mat in materials:
            if 'item' not in mat or 'quantity' not in mat:
                return Response(
                    {'error': 'Each material must have "item" and "quantity"'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                Item.objects.get(id=mat['item'])
            except Item.DoesNotExist:
                return Response(
                    {'error': f'Item with id {mat["item"]} does not exist'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Si todas las validaciones pasaron, eliminar y recrear
        BundleDetail.objects.filter(bundle=bundle).delete()

        for mat in materials:
            BundleDetail.objects.create(
                bundle=bundle,
                item_id=mat['item'],
                quantity=mat['quantity']
            )

        return Response(
            {'message': f'Successfully added {len(materials)} materials to bundle'},
            status=status.HTTP_201_CREATED
        )
    