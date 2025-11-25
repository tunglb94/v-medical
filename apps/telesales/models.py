from django.db import models
from django.conf import settings
from apps.customers.models import Customer

class CallLog(models.Model):
    class CallStatus(models.TextChoices):
        NEW = "NEW", "Mới (Chưa gọi)"
        CALLING = "CALLING", "Đang chăm sóc"
        NO_ANSWER = "NO_ANSWER", "Không nghe máy"
        WRONG_NUMBER = "WRONG_NUMBER", "Sai số"
        NOT_INTERESTED = "NOT_INTERESTED", "Không có nhu cầu"
        BOOKED = "BOOKED", "Đã đặt lịch hẹn"

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='call_logs', verbose_name="Khách hàng")
    caller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Người gọi")
    
    status = models.CharField(max_length=50, choices=CallStatus.choices, default=CallStatus.NEW, verbose_name="Kết quả cuộc gọi")
    note = models.TextField(blank=True, verbose_name="Ghi chú chi tiết")
    call_time = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian gọi")

    def __str__(self):
        return f"{self.customer.name} - {self.get_status_display()}"

    class Meta:
        verbose_name = "Lịch sử cuộc gọi"
        verbose_name_plural = "Quản lý Telesale"