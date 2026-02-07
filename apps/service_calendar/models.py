from django.db import models
from django.conf import settings
from apps.customers.models import Customer
from apps.sales.models import Service, Order

class TreatmentSession(models.Model):
    """Lưu lại mỗi lần KTV làm dịch vụ cho khách (Tính tua)"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Khách hàng")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, verbose_name="Dịch vụ thực hiện")
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Thuộc đơn hàng")
    
    # Nhân sự thực hiện
    technician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sessions_as_tech', verbose_name="KTV chính")
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions_as_doctor', verbose_name="Bác sĩ phụ trách")
    
    session_date = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian làm")
    note = models.TextField(blank=True, verbose_name="Ghi chú buổi làm")
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.customer.name} - {self.service.name} - {self.session_date.strftime('%d/%m')}"

    class Meta:
        verbose_name = "Buổi điều trị (Tour)"
        verbose_name_plural = "Lịch sử Tour KTV"
        ordering = ['-session_date']

# (Giữ lại ReminderLog cũ nếu cần, hoặc xóa đi nếu bạn muốn thay thế hoàn toàn)
class ReminderLog(models.Model):
    # ... (Code cũ giữ nguyên để tránh lỗi migration cũ) ...
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True)
    customer_phone_backup = models.CharField(max_length=20, blank=True)
    reminder_time = models.DateTimeField()
    content = models.TextField()
    status = models.CharField(max_length=20, default='PENDING')
    assigned_staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_reminders')
    created_at = models.DateTimeField(auto_now_add=True)