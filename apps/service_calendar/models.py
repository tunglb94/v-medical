from django.db import models
from django.conf import settings
from apps.bookings.models import Appointment

class ReminderLog(models.Model):
    # Liên kết 1-1 với lịch hẹn cũ
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='reminder_log', verbose_name="Lịch hẹn")
    
    is_reminded = models.BooleanField(default=False, verbose_name="Đã nhắc khách")
    note = models.TextField(blank=True, verbose_name="Ghi chú nhắc hẹn")
    reminded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Người nhắc")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Nhắc hẹn: {self.appointment.customer.name}"