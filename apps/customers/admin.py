from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin): # Đã sửa: admin.ModelAdmin
    list_display = ('name', 'phone', 'skin_condition', 'created_at')
    search_fields = ('name', 'phone')
    list_filter = ('skin_condition',)