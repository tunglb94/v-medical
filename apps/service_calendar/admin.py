from django.contrib import admin
from .models import TreatmentSession, ReminderLog

@admin.register(TreatmentSession)
class TreatmentSessionAdmin(admin.ModelAdmin):
    list_display = ('customer', 'service', 'technician', 'doctor', 'session_date', 'created_by')
    list_filter = ('session_date', 'technician', 'service')
    search_fields = ('customer__name', 'customer__phone', 'note')
    date_hierarchy = 'session_date'
    autocomplete_fields = ['customer', 'order']

@admin.register(ReminderLog)
class ReminderLogAdmin(admin.ModelAdmin):
    # Cập nhật các trường hiển thị cho khớp với Model mới
    list_display = ('customer', 'reminder_time', 'status', 'assigned_staff', 'created_at')
    list_filter = ('status', 'reminder_time')
    search_fields = ('customer__name', 'content')
    date_hierarchy = 'reminder_time'