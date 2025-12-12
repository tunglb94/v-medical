from django.db import models
from django.conf import settings
from apps.customers.models import Customer
from apps.bookings.models import Appointment
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from datetime import date # <-- Cần import date


# Service (Dịch vụ) - Mô hình riêng
class Service(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name="Tên dịch vụ")
    base_price = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Giá cố định (VND)")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Dịch vụ"
        verbose_name_plural = "Danh sách Dịch vụ"


# Order (Đơn hàng / Hợp đồng)
class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Khách hàng")
    
    service = models.ForeignKey(Service, on_delete=models.PROTECT, verbose_name="Dịch vụ chính")
    
    original_price = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Giá gốc")
    
    actual_revenue = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Thực thu (VND)")
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Tổng giá trị đơn hàng")
    
    assigned_consultant = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        limit_choices_to={'role': 'CONSULTANT'},
        verbose_name="Tư vấn viên (Sales)"
    )
    
    appointment = models.OneToOneField(Appointment, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Lịch hẹn liên quan")
    
    # FIX LỖI: Dùng date.today
    order_date = models.DateField(default=date.today, verbose_name="Ngày chốt đơn")
    
    note = models.TextField(blank=True, verbose_name="Ghi chú đơn hàng")
    is_paid = models.BooleanField(default=False, verbose_name="Đã thanh toán (Hoàn thành)")

    def save(self, *args, **kwargs):
        if not self.pk:
            self.original_price = self.service.base_price
            
        if self.actual_revenue == 0 and self.total_amount > 0:
            self.actual_revenue = self.total_amount
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"ĐH {self.pk} - {self.customer.name} - {self.service.name}"

    class Meta:
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Đơn hàng và Hợp đồng"
        ordering = ['-order_date']

# Signal để cập nhật Ranking của Customer khi Order được lưu hoặc xóa
@receiver([post_save, post_delete], sender=Order)
def update_customer_ranking(sender, instance, **kwargs):
    if instance.is_paid:
        instance.customer.update_ranking()