from django.contrib import admin
from .models import Product, InventoryLog

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'unit', 'stock', 'cost_price', 'min_stock')
    search_fields = ('name', 'code')

@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ('product', 'change_type', 'quantity', 'stock_after', 'user', 'created_at')
    list_filter = ('change_type', 'created_at')