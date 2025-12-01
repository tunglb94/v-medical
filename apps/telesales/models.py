from django.db import models
from django.conf import settings
from apps.customers.models import Customer

class CallLog(models.Model):
    # --- CẬP NHẬT TRẠNG THÁI GỌI ---
    class CallStatus(models.TextChoices):
        NEW = "NEW", "Mới (Chưa gọi)"       # Mặc định
        NO_ANSWER = "NO_ANSWER", "Không nhấc máy"
        BUSY = "BUSY", "Bận"
        WRONG_NUMBER = "WRONG_NUMBER", "Sai số"
        SPAM = "SPAM", "Spam"
        BOOKED = "BOOKED", "Đặt hẹn"
        CONSULTING = "CONSULTING", "Tham khảo"
        FOLLOW_UP = "FOLLOW_UP", "Chăm thêm"
        FAR_AWAY = "FAR_AWAY", "Tỉnh xa"

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