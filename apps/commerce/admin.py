from django.contrib import admin
from .models import (
    PurchasePlace, Purchase, PurchaseDetail,
    Customer, Sale, SaleDetail,
    Order, OrderDetail
)


class PurchaseDetailInline(admin.TabularInline):
    model = PurchaseDetail
    extra = 0


class SaleDetailInline(admin.TabularInline):
    model = SaleDetail
    extra = 0


class OrderDetailInline(admin.TabularInline):
    model = OrderDetail
    extra = 0


@admin.register(PurchasePlace)
class PurchasePlaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'is_active')


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'place', 'date', 'total')
    inlines = [PurchaseDetailInline]


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'nit', 'phone')
    search_fields = ('name', 'nit')


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'customer', 'date', 'total')
    inlines = [SaleDetailInline]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'user', 'date', 'delivery_date', 'status', 'total')
    list_filter = ('status',)
    inlines = [OrderDetailInline]