from django.urls import path, include
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse

@api_view(['GET'])
def commerce_root(request, format=None):
    return Response({
        'purchases': reverse('purchase-list-create', request=request, format=format),
        'suppliers': reverse('supplier-list-create', request=request, format=format),
        'places':    reverse('purchase-place-list-create', request=request, format=format),
    })

urlpatterns = [
    path('',           commerce_root, name='commerce-root'),
    path('purchases/', include('apps.commerce.purchases.urls')),
]