from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from .views import ItemViewSet, ProductViewSet, SupplyViewSet, BundleViewSet

router = DefaultRouter()
router.include_root_view = False  # ← desactiva la raíz doble del router

router.register(r'items',    ItemViewSet)
router.register(r'products', ProductViewSet)
router.register(r'supplies', SupplyViewSet)
router.register(r'bundles',  BundleViewSet)

@api_view(['GET'])
def inventory_root(request, format=None):
    return Response({
        'items':    reverse('item-list',    request=request, format=format),
        'products': reverse('product-list', request=request, format=format),
        'supplies': reverse('supply-list',  request=request, format=format),
        'bundles':  reverse('bundle-list',  request=request, format=format),
    })

urlpatterns = [
    path('', inventory_root, name='inventory-root'),
] + router.urls