from django.db import models
from django.conf import settings
from apps.customers.models import Customer

class Appointment(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Đã đặt lịch"
        ARRIVED = "ARRIVED", "Khách đã đến"
        IN_CONSULTATION = "IN_CONSULTATION", "Đang tư vấn"
        COMPLETED = "COMPLETED", "Hoàn thành"
        CANCELLED = "CANCELLED", "Hủy hẹn"
        NO_SHOW = "NO_SHOW", "Khách không đến"

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='appointments', verbose_name="Khách hàng")
    appointment_date = models.DateTimeField(verbose_name="Ngày giờ hẹn")
    
    # Người tạo & Người check-in
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_appointments', on_delete=models.SET_NULL, null=True)
    receptionist = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='checkin_appointments', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Lễ tân check-in")
    
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.SCHEDULED, verbose_name="Trạng thái")
    
    # --- ĐIỀU PHỐI NHÂN SỰ ---
    assigned_doctor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='doctor_appointments', limit_choices_to={'role': 'DOCTOR'}, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bác sĩ phụ trách")
    
    # Kỹ thuật viên (Mới thêm)
    assigned_technician = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='technician_appointments', limit_choices_to={'role': 'TECHNICIAN'}, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kỹ thuật viên")
    
    assigned_consultant = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='consultant_appointments', limit_choices_to={'role': 'CONSULTANT'}, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Sale tư vấn")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lịch hẹn: {self.customer.name} - {self.appointment_date.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        verbose_name = "Lịch hẹn"
        verbose_name_plural = "Quản lý Lịch hẹn"