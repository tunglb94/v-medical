from django.contrib import admin
from .models import ReminderLog

@admin.register(ReminderLog)
class ReminderLogAdmin(admin.ModelAdmin):
    list_display = ('get_customer', 'appointment', 'is_reminded', 'reminded_by', 'created_at')
    list_filter = ('is_reminded', 'created_at')
    search_fields = ('appointment__customer__name', 'appointment__customer__phone', 'note')
    
    def get_customer(self, obj):
        return obj.appointment.customer.name
    get_customer.short_description = 'Khách hàng'