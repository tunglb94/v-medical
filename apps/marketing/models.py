from django.db import models
from django.conf import settings
from django.utils import timezone

# --- MODEL CŨ (GIỮ NGUYÊN) ---
class DailyCampaignStat(models.Model):
    report_date = models.DateField(unique=True, verbose_name="Ngày báo cáo")
    spend_amount = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Ngân sách tiêu (VNĐ)")
    comments = models.IntegerField(default=0, verbose_name="Số Comment")
    inboxes = models.IntegerField(default=0, verbose_name="Số Inbox")
    leads = models.IntegerField(default=0, verbose_name="Số điện thoại (Leads)")
    appointments = models.IntegerField(default=0, verbose_name="Số lịch hẹn")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_interactions(self):
        return self.comments + self.inboxes

    @property
    def cost_per_lead(self):
        if self.leads > 0: return self.spend_amount / self.leads
        return 0

    @property
    def cost_per_appointment(self):
        if self.appointments > 0: return self.spend_amount / self.appointments
        return 0

    @property
    def conversion_rate_lead(self):
        total = self.total_interactions
        if total > 0: return (self.leads / total) * 100
        return 0

    @property
    def conversion_rate_appt(self):
        if self.leads > 0: return (self.appointments / self.leads) * 100
        return 0

    def __str__(self):
        return f"Báo cáo ngày {self.report_date}"

    class Meta:
        verbose_name = "Báo cáo Marketing"
        verbose_name_plural = "Báo cáo Marketing"
        ordering = ['-report_date']

# --- MODEL MỚI: QUẢN LÝ CÔNG VIỆC ---
class MarketingTask(models.Model):
    class Category(models.TextChoices):
        CONTENT = "CONTENT", "Viết Content"
        DESIGN = "DESIGN", "Thiết kế (Designer)"
        VIDEO = "VIDEO", "Quay/Dựng Video"
        ADS = "ADS", "Chạy Ads"
        OTHER = "OTHER", "Khác"

    class Status(models.TextChoices):
        TODO = "TODO", "Chưa làm"
        DOING = "DOING", "Đang làm"
        REVIEW = "REVIEW", "Chờ duyệt"
        DONE = "DONE", "Hoàn thành"

    title = models.CharField(max_length=255, verbose_name="Tên công việc")
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.CONTENT, verbose_name="Hạng mục")
    
    # PIC: Người phụ trách (Lưu ý: Cần thêm role MARKETING vào User model nếu muốn lọc kỹ hơn)
    pic = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Người phụ trách (PIC)")
    
    start_date = models.DateField(default=timezone.now, verbose_name="Ngày bắt đầu")
    deadline = models.DateField(verbose_name="Hạn chót (Deadline)")
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO, verbose_name="Trạng thái")
    note = models.TextField(blank=True, verbose_name="Ghi chú/Yêu cầu")
    
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_overdue(self):
        """Kiểm tra quá hạn (Chưa xong mà đã qua deadline)"""
        return self.status != 'DONE' and self.deadline < timezone.now().date()

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Công việc Marketing"
        verbose_name_plural = "Quản lý Công việc"
        ordering = ['deadline']