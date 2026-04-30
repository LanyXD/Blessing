# from django.shortcuts import render
from rest_framework import serializers, viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.db import transaction
from .models import Item, Product, Supply, Bundle, BundleDetail
from .serializers import (
    ItemSerializer,
    ProductSerializer,
    SupplySerializer,
    BundleSerializer
)
from apps.sales.models import SaleItem  # ajusta el path según tu estructura


def _validate_unique_name(name, exclude_id=None):
    """Valida que no exista otro item con el mismo nombre."""
    if Item.objects.filter(name__iexact=name).exclude(id=exclude_id).exists():
        raise ValueError(f'Ya existe un producto con el nombre "{name}"')


def _get_material_data(materials):
    """FormData envía todo como string — parseamos si es necesario"""
    if isinstance(materials, str):
        import json
        try:
            materials = json.loads(materials)
        except json.JSONDecodeError:
            raise ValueError('Formato de materiales inválido')
        
    """Convierte la lista de materiales entrante en un diccionario de item->cantidad.
    Valida que cada componente exista, tenga cantidad positiva y no sea un arreglo.
    """
    if not isinstance(materials, list):
        raise ValueError('Se esperaba una lista de materiales')

    material_map = {}
    for mat in materials:
        if not isinstance(mat, dict):
            raise ValueError('Cada material debe ser un objeto')

        item_id = mat.get('item')
        quantity = mat.get('quantity')

        if item_id is None or quantity is None:
            raise ValueError('Cada material debe tener "artículo" y "cantidad".')

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            raise ValueError('La cantidad debe ser un número entero.')

        if quantity <= 0:
            raise ValueError('La cantidad debe ser mayor que cero')

        try:
            item = Item.objects.get(id=item_id)
        except Item.DoesNotExist:
            raise ValueError(f'Item with id {item_id} does not exist')

        if item.type == 'bundle':
            raise ValueError('No se permiten arreglos dentro de arreglos')

        if item.type == 'supply':
            raise ValueError('No se permiten insumos dentro de arreglos')

        if item_id in material_map:
            material_map[item_id]['quantity'] += quantity
        else:
            material_map[item_id] = {
                'item': item,
                'quantity': quantity,
            }

    return material_map


def _restore_bundle_stock(bundle):
    """Restaura stock de los materiales usados por un bundle antes de eliminarlo."""
    for detail in bundle.details.select_related('item').all():
        if detail.quantity > 0:
            detail.item.adjust_stock(
                detail.quantity,
                reason='bundle deleted',
                reference_table='Bundle',
                reference_id=bundle.pk,
            )


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

    def create(self, request, *args, **kwargs):
        print('MATERIALS RECIBIDOS:', request.data.get('materials'))

        data = request.data.copy()
        item_type = data.get('type')
        materials = data.get('materials', [])  # ← recibir materiales junto al item

        # Fields for Item model
        item_fields = ['name', 'type', 'category', 'unit', 'stock', 'min_stock', 'purchase_price', 'sell_price', 'image']
        item_data = {k: v for k, v in data.items() if k in item_fields}

        name = item_data.get('name')
        if name:
            try:
                _validate_unique_name(name)
            except ValueError as exc:
                return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        # transaction.atomic() garantiza que si algo falla,
        # TODO se revierte — ni el item ni los materiales quedan a medias
        with transaction.atomic():
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
                bundle = Bundle.objects.create(item=item, description=description)

                # Si vienen materiales, los validamos y guardamos
                # en la misma transacción — si algo falla, el item tampoco se crea
                if materials:
                    try:
                        material_map = _get_material_data(materials)
                    except ValueError as exc:
                        raise serializers.ValidationError({'materials': str(exc)})

                    if not material_map:
                        raise serializers.ValidationError({
                            'materials': 'Un arreglo debe tener al menos un componente.'
                        })

                    for item_id, info in material_map.items():
                        item_obj = info['item']
                        qty = info['quantity']

                        # Verificamos stock antes de descontar
                        if item_obj.stock < qty:
                            raise serializers.ValidationError({
                                'materials': f'No hay suficiente stock de "{item_obj.name}". Disponible: {item_obj.stock}'
                            })

                        item_obj.adjust_stock(
                            -qty,
                            reason='bundle created',
                            reference_table='Bundle',
                            reference_id=bundle.pk,
                        )

                        BundleDetail.objects.create(
                            bundle=bundle,
                            item_id=item_id,
                            quantity=qty,
                        )

        return Response(item_serializer.data, status=status.HTTP_201_CREATED)


    def perform_update(self, serializer):
        """Controla cambios de tipo y mantiene las relaciones de tipo correctas."""
        item = self.get_object()

        # ── Eliminar imagen si el frontend envió el flag remove_image ────────
        if self.request.data.get('remove_image') == 'true':
            if item.image:
                item.image.delete(save=False)  # borra el archivo físico
            # Fuerza image=None en el serializer para que no la restaure
            serializer.validated_data['image'] = None
        new_type = serializer.validated_data.get('type', item.type)
        old_type = item.type

        if new_type != old_type and not item.can_change_type():
            raise serializers.ValidationError({
                'type': 'No se puede cambiar el tipo si tiene componentes, ha sido usado en un arreglo o tiene historial.'
            })

        new_name = serializer.validated_data.get('name')
        if new_name:
            try:
                _validate_unique_name(new_name, exclude_id=item.id)
            except ValueError as exc:
                raise serializers.ValidationError({'name': str(exc)})

        super().perform_update(serializer)

        if new_type != old_type:
            if old_type == 'product' and hasattr(item, 'product'):
                item.product.delete()
            elif old_type == 'supply' and hasattr(item, 'supply'):
                item.supply.delete()
            elif old_type == 'bundle' and hasattr(item, 'bundle'):
                item.bundle.delete()

            if new_type == 'product':
                Product.objects.create(
                    item=item,
                    description=serializer.validated_data.get('description', ''),
                )
            elif new_type == 'supply':
                Supply.objects.create(
                    item=item,
                    entry_date=serializer.validated_data.get('entry_date', timezone.now().date()),
                    is_sellable=serializer.validated_data.get('is_sellable', False),
                )
            elif new_type == 'bundle':
                Bundle.objects.create(
                    item=item,
                    description=serializer.validated_data.get('description', ''),
                )

    def destroy(self, request, *args, **kwargs):
        item = self.get_object()

        # """Protección: no eliminar si tiene historial de ventas"""
        if SaleItem.objects.filter(product=item).exists():
            return Response(
                {'error': 'No se puede eliminar este producto porque tiene historial de ventas.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        """Restaura stock si se elimina un bundle a través del endpoint de items."""
        if item.type == 'bundle' and hasattr(item, 'bundle'):
            _restore_bundle_stock(item.bundle)
        return super().destroy(request, *args, **kwargs)

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
        Agrega o actualiza materiales de un bundle, ajustando stock según diferencias.
        """
        bundle = self.get_object()
        materials = request.data

        try:
            material_map = _get_material_data(materials)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if not material_map:
            return Response(
                {'error': 'Un arreglo debe tener al menos un componente.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        old_details = {
            detail.item_id: detail.quantity
            for detail in bundle.details.select_related('item').all()
        }

        # Validación de disponibilidad antes de descontar stock.
        for item_id, new_info in material_map.items():
            item = new_info['item']
            new_qty = new_info['quantity']
            old_qty = old_details.get(item_id, 0)
            delta = new_qty - old_qty

            if delta > 0 and item.stock < delta:
                return Response(
                    {
                        'error': 'No hay suficiente stock para {}. Disponible: {}'.format(item.name, item.stock)
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        with transaction.atomic():
            # Ajustar stock y actualizar detalles del bundle.
            for item_id, new_info in material_map.items():
                item = new_info['item']
                new_qty = new_info['quantity']
                old_qty = old_details.pop(item_id, 0)
                delta = new_qty - old_qty

                if delta != 0:
                    item.adjust_stock(
                        -delta,
                        reason='bundle material update',
                        reference_table='Bundle',
                        reference_id=bundle.pk,
                    )

            # Los materiales eliminados del bundle regresan stock.
            for removed_item_id, removed_qty in old_details.items():
                removed_item = Item.objects.get(id=removed_item_id)
                removed_item.adjust_stock(
                    removed_qty,
                    reason='bundle material removed',
                    reference_table='Bundle',
                    reference_id=bundle.pk,
                )

            BundleDetail.objects.filter(bundle=bundle).delete()
            for item_id, new_info in material_map.items():
                BundleDetail.objects.create(
                    bundle=bundle,
                    item_id=item_id,
                    quantity=new_info['quantity'],
                )

        return Response(
            {
                'message': 'Materiales guardados y stock actualizado correctamente.',
                'bundle_id': bundle.pk,
            },
            status=status.HTTP_201_CREATED
        )

    def destroy(self, request, *args, **kwargs):
        bundle = self.get_object()

        # Protección: no eliminar si el Item del bundle tiene historial de ventas
        if SaleItem.objects.filter(product=bundle.item).exists():
            return Response(
                {'error': 'No se puede eliminar este arreglo porque tiene historial de ventas.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        """Restaura el stock usado por un bundle antes de eliminarlo."""
        bundle = self.get_object()
        _restore_bundle_stock(bundle)
        return super().destroy(request, *args, **kwargs)
