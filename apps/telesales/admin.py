from django.contrib import admin
from .models import CallLog

@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin): # Đã sửa: admin.ModelAdmin
    list_display = ('customer', 'caller', 'status', 'call_time')
    list_filter = ('status', 'caller')