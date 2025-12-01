from django.db import models
from django.conf import settings
from django.utils import timezone

# 1. Cấu hình Lương cho từng nhân viên
class EmployeeContract(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contract', verbose_name="Nhân viên")
    base_salary = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Lương cứng (VNĐ)")
    allowance = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Phụ cấp cố định")
    start_date = models.DateField(default=timezone.now, verbose_name="Ngày bắt đầu làm")
    
    def __str__(self):
        return f"HĐ: {self.user.username}"

    class Meta:
        verbose_name = "Hợp đồng & Lương"
        verbose_name_plural = "Cấu hình Lương Nhân sự"

# 2. Chấm công hàng ngày
class Attendance(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Nhân viên")
    date = models.DateField(default=timezone.now, verbose_name="Ngày")
    check_in = models.TimeField(null=True, blank=True, verbose_name="Giờ vào")
    check_out = models.TimeField(null=True, blank=True, verbose_name="Giờ ra")
    ip_address = models.CharField(max_length=50, blank=True, null=True, verbose_name="IP Mạng")
    note = models.TextField(blank=True, verbose_name="Ghi chú (Đi muộn/Về sớm)")

    def __str__(self):
        return f"{self.user.username} - {self.date}"

    class Meta:
        verbose_name = "Chấm công"
        verbose_name_plural = "Nhật ký Chấm công"
        unique_together = ('user', 'date')

# 3. Bảng lương tháng
class SalarySlip(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Nhân viên")
    month = models.DateField(verbose_name="Tháng tính lương")
    standard_work_days = models.FloatField(default=26, verbose_name="Công chuẩn")
    actual_work_days = models.FloatField(default=0, verbose_name="Công thực tế")
    base_salary_lock = models.DecimalField(max_digits=15, decimal_places=0, verbose_name="Lương cứng chốt")
    allowance_lock = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Phụ cấp chốt")
    bonus = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Thưởng thêm")
    deduction = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Phạt/Khấu trừ")
    total_salary = models.DecimalField(max_digits=15, decimal_places=0, verbose_name="Thực lĩnh")
    is_finalized = models.BooleanField(default=False, verbose_name="Đã chốt sổ")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lương T{self.month.month}/{self.month.year} - {self.user.username}"

    class Meta:
        verbose_name = "Phiếu lương"
        verbose_name_plural = "Quản lý Bảng lương"