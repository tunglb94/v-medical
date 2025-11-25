from django.db import models
from django.conf import settings
from apps.customers.models import Customer
from apps.bookings.models import Appointment

# 1. MODEL DỊCH VỤ (MỚI)
class Service(models.Model):
    name = models.CharField(max_length=200, verbose_name="Tên dịch vụ/Liệu trình")
    price = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Giá niêm yết (VNĐ)")
    description = models.TextField(blank=True, verbose_name="Mô tả chi tiết")
    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động")

    def __str__(self):
        return f"{self.name} - {self.price:,.0f}đ"

    class Meta:
        verbose_name = "Dịch vụ & Bảng giá"
        verbose_name_plural = "Quản lý Dịch vụ"

# 2. MODEL ĐƠN HÀNG (CẬP NHẬT)
class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Khách hàng")
    appointment = models.OneToOneField(Appointment, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Từ lịch hẹn nào")
    sale_consultant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Sale chốt đơn")
    
    # Liên kết với Service (Mới)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Dịch vụ chọn")
    
    # Vẫn giữ treatment_name để lưu tên tại thời điểm mua (phòng trường hợp sau này đổi tên dịch vụ gốc)
    treatment_name = models.CharField(max_length=200, verbose_name="Tên liệu trình chốt")
    
    total_amount = models.DecimalField(max_digits=15, decimal_places=0, verbose_name="Thực thu (VNĐ)")
    is_paid = models.BooleanField(default=False, verbose_name="Đã thanh toán")
    note = models.TextField(blank=True, verbose_name="Ghi chú thêm")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo đơn")

    def __str__(self):
        return f"Đơn: {self.treatment_name} - {self.total_amount:,.0f} đ"

    class Meta:
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Doanh thu & Đơn hàng"