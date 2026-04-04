from rest_framework.routers import DefaultRouter
from .views import (
    ItemViewSet,
    ProductViewSet,
    SupplyViewSet,
    BundleViewSet
)

router = DefaultRouter()

router.register(r'items', ItemViewSet)
router.register(r'products', ProductViewSet)
router.register(r'supplies', SupplyViewSet)
router.register(r'bundles', BundleViewSet)

urlpatterns = router.urls