from django.contrib import admin
from .models import Sale
from .models import SaleItem

admin.site.register(Sale)
admin.site.register(SaleItem)