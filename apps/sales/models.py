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
    
    # actual_revenue bây giờ là số tiền KHÁCH ĐÃ TRẢ
    actual_revenue = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Thực thu (Đã trả)")
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Tổng giá trị đơn hàng")
    
    # --- THÊM MỚI: Trường lưu số nợ ---
    debt_amount = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Còn nợ")
    
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
            
        # Logic cũ: Nếu chưa nhập thực thu thì gán bằng tổng tiền (Giữ lại để tương thích ngược nếu cần)
        # Nhưng logic mới sẽ ưu tiên tính toán nợ
        
        # TÍNH TOÁN CÔNG NỢ
        # Nợ = Tổng tiền - Thực thu
        if self.total_amount > 0:
            self.debt_amount = self.total_amount - self.actual_revenue
            # Đảm bảo không âm (nếu khách trả thừa thì coi như nợ = 0 hoặc xử lý logic tiền thừa riêng)
            if self.debt_amount < 0:
                self.debt_amount = 0
        else:
            self.debt_amount = 0
            
        # Tự động cập nhật trạng thái thanh toán
        # Nếu nợ <= 0 thì coi như đã thanh toán xong
        if self.debt_amount <= 0 and self.total_amount > 0:
            self.is_paid = True
        elif self.total_amount == 0:
            self.is_paid = False
        else:
            self.is_paid = False # Vẫn còn nợ
            
        super().save(*args, **kwargs)

    def __str__(self):
        status = "Đủ" if self.is_paid else "Nợ"
        return f"ĐH {self.pk} - {self.customer.name} - {self.service.name} ({status})"

    class Meta:
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Đơn hàng và Hợp đồng"
        ordering = ['-order_date']

# Signal để cập nhật Ranking của Customer khi Order được lưu hoặc xóa
@receiver([post_save, post_delete], sender=Order)
def update_customer_ranking(sender, instance, **kwargs):
    # Logic ranking: Chỉ cộng những đơn đã thanh toán hoặc tính theo thực thu tùy chính sách
    # Ở đây giữ nguyên logic cũ: Nếu is_paid mới update (hoặc bạn có thể sửa lại tính tổng actual_revenue)
    instance.customer.update_ranking()