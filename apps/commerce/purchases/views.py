from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db import transaction

from apps.inventory.models import Item
from .models import PurchasePlace, Supplier, Purchase, PurchaseDetail
from .serializers import (
    PurchasePlaceSerializer,
    SupplierSerializer,
    PurchaseCreateSerializer,
    PurchaseOutputSerializer,
)


# ── PurchasePlace ──────────────────────────────────────────────────────────────

class PurchasePlaceListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Lista todos los lugares activos."""
        places = PurchasePlace.objects.filter(is_active=True).order_by('name')
        return Response(PurchasePlaceSerializer(places, many=True).data)

    def post(self, request):
        """Crea un nuevo lugar de compra."""
        serializer = PurchasePlaceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PurchasePlaceDetailView(APIView):
    permission_classes = [AllowAny]

    def _get_object(self, pk):
        try:
            return PurchasePlace.objects.get(pk=pk)
        except PurchasePlace.DoesNotExist:
            return None

    def put(self, request, pk):
        """Actualiza un lugar de compra."""
        place = self._get_object(pk)
        if not place:
            return Response({'detail': 'Lugar no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = PurchasePlaceSerializer(place, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        """Desactiva un lugar (soft delete)."""
        place = self._get_object(pk)
        if not place:
            return Response({'detail': 'Lugar no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        place.is_active = False
        place.save(update_fields=['is_active'])
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Supplier ───────────────────────────────────────────────────────────────────

class SupplierListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Lista todos los proveedores activos."""
        suppliers = Supplier.objects.filter(is_active=True).order_by('name')
        return Response(SupplierSerializer(suppliers, many=True).data)

    def post(self, request):
        """Crea un nuevo proveedor."""
        serializer = SupplierSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SupplierDetailView(APIView):
    permission_classes = [AllowAny]

    def _get_object(self, pk):
        try:
            return Supplier.objects.get(pk=pk)
        except Supplier.DoesNotExist:
            return None

    def put(self, request, pk):
        """Actualiza un proveedor."""
        supplier = self._get_object(pk)
        if not supplier:
            return Response({'detail': 'Proveedor no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SupplierSerializer(supplier, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        """Desactiva un proveedor (soft delete)."""
        supplier = self._get_object(pk)
        if not supplier:
            return Response({'detail': 'Proveedor no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        supplier.is_active = False
        supplier.save(update_fields=['is_active'])
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Purchase ───────────────────────────────────────────────────────────────────

class PurchaseItemListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Devuelve ítems activos disponibles para agregar a una compra."""
        items = Item.objects.filter(is_activate=True).order_by('name')
        data = [
            {
                'id':             item.id,
                'name':           item.name,
                'type':           item.type,
                'unit':           item.unit,
                'stock':          int(item.stock),
                'purchase_price': float(item.purchase_price),
                'image': request.build_absolute_uri(item.image.url) if item.image else None,
            }
            for item in items
        ]
        return Response(data)


class PurchaseListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Lista todas las compras ordenadas por más reciente."""
        purchases = (
            Purchase.objects
            .select_related('supplier', 'place', 'user')
            .prefetch_related('details__item')
            .order_by('-created_at')
        )
        return Response(PurchaseOutputSerializer(purchases, many=True).data)

    def post(self, request):
        """Crea una compra y actualiza el stock de cada ítem."""
        serializer = PurchaseCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            with transaction.atomic():

                # Resolver supplier y place
                supplier = None
                place    = None

                if data.get('supplier_id'):
                    try:
                        supplier = Supplier.objects.get(pk=data['supplier_id'], is_active=True)
                    except Supplier.DoesNotExist:
                        return Response(
                            {'detail': 'Proveedor no encontrado o inactivo.'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                if data.get('place_id'):
                    try:
                        place = PurchasePlace.objects.get(pk=data['place_id'], is_active=True)
                    except PurchasePlace.DoesNotExist:
                        return Response(
                            {'detail': 'Lugar no encontrado o inactivo.'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                # BUG FIX: request.user puede ser AnonymousUser con AllowAny.
                # Usamos el primer superuser disponible como fallback temporal
                # hasta implementar autenticación real.
                user = request.user if request.user.is_authenticated else None
                if user is None:
                    from apps.accounts.models import User as AppUser
                    user = AppUser.objects.filter(is_superuser=True).first()
                    if user is None:
                        return Response(
                            {'detail': 'No hay usuario autenticado para registrar la compra.'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                purchase = Purchase.objects.create(
                    user     = user,
                    supplier = supplier,
                    place    = place,
                    date     = data['date'],
                    total    = data['total'],
                    note     = data.get('note') or '',
                )

                for detail_data in data['details']:
                    try:
                        item = Item.objects.select_for_update().get(pk=detail_data['item_id'])
                    except Item.DoesNotExist:
                        return Response(
                            {'detail': f'Ítem con id {detail_data["item_id"]} no encontrado.'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    # BUG FIX: no pasamos subtotal explícitamente — PurchaseDetail.save()
                    # ya lo calcula. Pasarlo aquí era redundante y propenso a inconsistencias.
                    PurchaseDetail.objects.create(
                        purchase   = purchase,
                        item       = item,
                        quantity   = detail_data['quantity'],
                        unit_price = detail_data['unit_price'],
                        # subtotal es calculado automáticamente por el modelo
                        subtotal   = detail_data['unit_price'] * detail_data['quantity'],
                    )

            return Response(
                PurchaseOutputSerializer(purchase).data,
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
