from django.contrib import admin
from .models import Order, Service # Import thêm Service

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('customer', 'treatment_name', 'total_amount', 'sale_consultant', 'created_at')
    list_filter = ('is_paid', 'created_at')
    search_fields = ('customer__name', 'treatment_name')