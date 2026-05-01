from django.urls import path
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from .views import SaleListCreateView, SaleProductListView

@api_view(['GET'])
def sales_root(request, format=None):
    return Response({
        'sales':    reverse('sale-list-create', request=request, format=format),
        'products': reverse('sale-product-list', request=request, format=format),
    })

urlpatterns = [
    path('',          sales_root,                        name='sales-root'),
    path('list/',     SaleListCreateView.as_view(),      name='sale-list-create'),
    path('products/', SaleProductListView.as_view(),     name='sale-product-list'),
]
