from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'inventory': reverse('inventory-root', request=request, format=format),
        'sales':     reverse('sales-root',     request=request, format=format),
        'commerce':  reverse('commerce-root',  request=request, format=format),
    })

urlpatterns = [
    path('admin/',         admin.site.urls),
    path('api/',           api_root,                              name='api-root'),
    path('api/inventory/', include('apps.inventory.urls')),
    path('api/sales/',     include('apps.sales.urls')),
    path('api/commerce/',  include('apps.commerce.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)