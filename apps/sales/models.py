from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from datetime import date
from apps.customers.models import Customer
from apps.bookings.models import Appointment

class Service(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name="Tên dịch vụ")
    base_price = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Giá cố định (VND)")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Dịch vụ"
        verbose_name_plural = "Danh sách Dịch vụ"


class Order(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Tiền mặt'
        TRANSFER = 'TRANSFER', 'Chuyển khoản'
        CARD = 'CARD', 'Quẹt thẻ'
        INSTALLMENT = 'INSTALLMENT', 'Trả góp'

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Khách hàng")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, verbose_name="Dịch vụ chính")
    
    original_price = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Giá gốc")
    actual_revenue = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Thực thu (Đã trả)")
    total_amount = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Tổng giá trị đơn hàng")
    debt_amount = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Còn nợ")
    
    assigned_consultant = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        limit_choices_to={'role': 'CONSULTANT'},
        verbose_name="Tư vấn viên (Sales)"
    )
    
    appointment = models.OneToOneField(Appointment, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Lịch hẹn liên quan")
    order_date = models.DateField(default=date.today, verbose_name="Ngày chốt đơn")
    
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.TRANSFER, verbose_name="Hình thức thanh toán")
    note = models.TextField(blank=True, verbose_name="Ghi chú đơn hàng")
    is_paid = models.BooleanField(default=False, verbose_name="Đã thanh toán (Hoàn thành)")

    def save(self, *args, **kwargs):
        # 1. Tự động lấy giá gốc từ dịch vụ nếu là đơn mới
        if not self.pk and self.service:
            self.original_price = self.service.base_price
        
        # 2. Logic điền tự động Tổng tiền nếu để trống
        # Nếu nhập Thực thu mà quên nhập Tổng tiền -> Coi như Tổng tiền = Thực thu (để không bị nợ âm)
        if (not self.total_amount or self.total_amount == 0) and self.actual_revenue > 0:
             self.total_amount = self.actual_revenue

        # 3. Tính toán Công nợ
        if self.total_amount > 0:
            self.debt_amount = self.total_amount - self.actual_revenue
            if self.debt_amount < 0:
                self.debt_amount = 0
        else:
            self.debt_amount = 0
            
        # 4. Cập nhật trạng thái thanh toán
        if self.debt_amount <= 0 and self.total_amount > 0:
            self.is_paid = True
        else:
            self.is_paid = False
            
        super().save(*args, **kwargs)

    def __str__(self):
        status = "Đủ" if self.is_paid else "Nợ"
        return f"ĐH {self.pk} - {self.customer.name} - {self.service.name} ({status})"

    class Meta:
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Đơn hàng và Hợp đồng"
        ordering = ['-order_date']

@receiver([post_save, post_delete], sender=Order)
def update_customer_ranking(sender, instance, **kwargs):
    if instance.customer:
        instance.customer.update_ranking()