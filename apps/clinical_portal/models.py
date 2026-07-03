from django.conf import settings
from django.db import models


class PlannedSession(models.Model):
    class SessionType(models.TextChoices):
        MAIN = "MAIN", "Buổi chính"
        BONUS = "BONUS", "Buổi tặng kèm"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Chưa đặt lịch"
        SCHEDULED = "SCHEDULED", "Đã đặt lịch"
        DONE = "DONE", "Đã hoàn thành"
        CANCELLED = "CANCELLED", "Đã huỷ"

    order = models.ForeignKey('sales.Order', on_delete=models.CASCADE, related_name='planned_sessions', verbose_name="Đơn hàng")
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='planned_sessions', verbose_name="Khách hàng")
    service = models.ForeignKey('sales.Service', on_delete=models.PROTECT, verbose_name="Dịch vụ")

    session_type = models.CharField(max_length=10, choices=SessionType.choices, default=SessionType.MAIN, verbose_name="Loại buổi")
    session_number = models.PositiveIntegerField(default=1, verbose_name="Buổi số")
    total_in_group = models.PositiveIntegerField(default=1, verbose_name="Tổng buổi cùng loại")

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, verbose_name="Trạng thái")
    scheduled_date = models.DateTimeField(null=True, blank=True, verbose_name="Ngày giờ hẹn")

    assigned_doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='planned_sessions_as_doctor', limit_choices_to={'role': 'DOCTOR'}, verbose_name="Bác sĩ phụ trách"
    )
    assigned_technician = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='planned_sessions_as_tech', limit_choices_to={'role': 'TECHNICIAN'}, verbose_name="KTV phụ trách"
    )

    completed_log = models.OneToOneField(
        'service_calendar.TreatmentSession', null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name="Bản ghi tính hoa hồng"
    )

    note = models.TextField(blank=True, verbose_name="Ghi chú")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        label = "Chính" if self.session_type == self.SessionType.MAIN else "Tặng"
        return f"{self.customer.name} - {self.service.name} ({label} {self.session_number}/{self.total_in_group})"

    class Meta:
        verbose_name = "Buổi điều trị đã lên kế hoạch"
        verbose_name_plural = "Kế hoạch điều trị"
        ordering = ['scheduled_date', 'session_number']
