from django.contrib import admin
from apps.commerce.purchases.models import (
    PurchasePlace, Supplier, Purchase, PurchaseDetail
)


class PurchaseDetailInline(admin.TabularInline):
    model = PurchaseDetail
    extra = 0


@admin.register(PurchasePlace)
class PurchasePlaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'is_active')


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact', 'phone', 'nit', 'is_active')
    search_fields = ('name', 'nit')


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'supplier', 'place', 'date', 'total')
    list_filter  = ('supplier', 'place')
    inlines      = [PurchaseDetailInline]