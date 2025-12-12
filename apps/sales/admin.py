from django.contrib import admin
from .models import Service, Order

# Admin cho Service model
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    # FIX: Thay 'price' bằng 'base_price'. Loại bỏ 'is_active'.
    list_display = ('name', 'base_price')
    list_filter = []  # Loại bỏ 'is_active'
    search_fields = ('name',)
    ordering = ('name',)

# Admin cho Order model
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # FIX: 
    # [1] 'treatment_name' -> 'service_name'
    # [3] 'sale_consultant' -> 'consultant_name'
    # [4] 'created_at' -> 'order_date'
    list_display = (
        'customer', 
        'service_name', 
        'actual_revenue', # NEW: Thêm trường thực thu
        'total_amount', 
        'consultant_name', 
        'order_date', 
        'is_paid'
    )
    
    # FIX: 'created_at' -> 'order_date'
    list_filter = ('is_paid', 'order_date', 'assigned_consultant')
    search_fields = ('customer__name', 'customer__phone', 'service__name')
    ordering = ('-order_date',)
    raw_id_fields = ('customer', 'service', 'assigned_consultant', 'appointment')
    
    # Custom methods để hiển thị tên dịch vụ và tên tư vấn viên
    def service_name(self, obj):
        return obj.service.name
    service_name.short_description = 'Dịch vụ'
    
    def consultant_name(self, obj):
        if obj.assigned_consultant:
            return obj.assigned_consultant.get_full_name()
        return "N/A"
    consultant_name.short_description = 'Tư vấn viên'