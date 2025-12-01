from django.db import models
from django.conf import settings
from django.utils import timezone

# 1. Cấu hình Lương & Hoa hồng cho nhân viên
class EmployeeContract(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contract', verbose_name="Nhân viên")
    base_salary = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Lương cứng (VNĐ)")
    allowance = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Phụ cấp cố định")
    
    # Thêm phần trăm hoa hồng
    commission_rate = models.FloatField(default=0, verbose_name="% Hoa hồng (VD: 5.0)")
    
    start_date = models.DateField(default=timezone.now, verbose_name="Ngày bắt đầu làm")
    
    def __str__(self):
        return f"HĐ: {self.user.username} - {self.commission_rate}% HH"

    class Meta:
        verbose_name = "Hợp đồng & Lương"
        verbose_name_plural = "Cấu hình Lương Nhân sự"

# 2. Chấm công (Đơn giản hóa: Có bản ghi = Có đi làm)
class Attendance(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Nhân viên")
    date = models.DateField(default=timezone.now, verbose_name="Ngày")
    is_present = models.BooleanField(default=True, verbose_name="Có mặt") # Admin tích vào là True
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.date}"

    class Meta:
        verbose_name = "Chấm công"
        verbose_name_plural = "Nhật ký Chấm công"
        unique_together = ('user', 'date')

# 3. Bảng lương tháng (Cập nhật thêm cột Hoa hồng)
class SalarySlip(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Nhân viên")
    month = models.DateField(verbose_name="Tháng tính lương")
    
    # Thông tin cơ bản
    standard_work_days = models.FloatField(default=26, verbose_name="Công chuẩn")
    actual_work_days = models.FloatField(default=0, verbose_name="Công thực tế")
    base_salary_lock = models.DecimalField(max_digits=15, decimal_places=0, verbose_name="Lương cứng")
    allowance_lock = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Phụ cấp")
    
    # Thông tin Hoa hồng
    sales_revenue = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Doanh số đạt được")
    commission_rate_lock = models.FloatField(default=0, verbose_name="% Hoa hồng áp dụng")
    commission_amount = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Tiền hoa hồng")

    # Tổng kết
    bonus = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Thưởng khác")
    deduction = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Phạt/Khấu trừ")
    total_salary = models.DecimalField(max_digits=15, decimal_places=0, verbose_name="THỰC LĨNH")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lương T{self.month.month}/{self.month.year} - {self.user.username}"

    class Meta:
        verbose_name = "Phiếu lương"
        verbose_name_plural = "Quản lý Bảng lương"