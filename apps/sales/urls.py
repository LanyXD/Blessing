# sales/urls.py

from django.urls import path
from .views import SaleListCreateView, SaleProductListView

urlpatterns = [
    path('sales/', SaleListCreateView.as_view(), name='sale-list-create'),
    path('sales/products/', SaleProductListView.as_view(), name='sale-product-list'),

]