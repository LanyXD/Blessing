from django.contrib import admin

# Register your models here.
from .models import (
    Item,
    Product,
    Supply,
    Bundle,
    BundleDetail,
    InventoryMovement
)

admin.site.register(Item)
admin.site.register(Product)
admin.site.register(Supply)
admin.site.register(Bundle)
admin.site.register(BundleDetail)
admin.site.register(InventoryMovement)