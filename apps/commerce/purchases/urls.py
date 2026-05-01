from django.urls import path
from .views import (
    PurchasePlaceListCreateView,
    PurchasePlaceDetailView,
    SupplierListCreateView,
    SupplierDetailView,
    PurchaseItemListView,
    PurchaseListCreateView,
)

urlpatterns = [
    # Lugares de compra
    path('places/',        PurchasePlaceListCreateView.as_view(), name='purchase-place-list-create'),
    path('places/<int:pk>/', PurchasePlaceDetailView.as_view(),   name='purchase-place-detail'),

    # Proveedores
    path('suppliers/',           SupplierListCreateView.as_view(), name='supplier-list-create'),
    path('suppliers/<int:pk>/',  SupplierDetailView.as_view(),     name='supplier-detail'),

    # Compras
    path('items/',     PurchaseItemListView.as_view(),    name='purchase-item-list'),
    path('',           PurchaseListCreateView.as_view(),  name='purchase-list-create'),
]
