from django.contrib import admin
from .models import Appointment

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin): # Đã sửa: admin.ModelAdmin
    list_display = ('customer', 'appointment_date', 'status', 'assigned_doctor')
    list_filter = ('status', 'appointment_date')
    date_hierarchy = 'appointment_date'