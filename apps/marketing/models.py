from django.db import models
from django.conf import settings
from apps.sales.models import Service

class MarketingTask(models.Model):
    class Status(models.TextChoices):
        PLANNING = 'PLANNING', 'Lên kế hoạch'
        WRITING = 'WRITING', 'Đang viết/Sản xuất'
        DESIGNING = 'DESIGNING', 'Đang thiết kế'
        RUNNING = 'RUNNING', 'Đang chạy Ads'
        COMPLETED = 'COMPLETED', 'Hoàn thành'
        PAUSED = 'PAUSED', 'Tạm dừng'

    title = models.CharField(max_length=200, verbose_name="Tiêu đề/Chủ đề")
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Dịch vụ quảng bá")
    
    # --- THỜI GIAN ---
    start_date = models.DateField(null=True, blank=True, verbose_name="Ngày bắt đầu")
    deadline = models.DateField(null=True, blank=True, verbose_name="Deadline")

    # --- NHÂN SỰ THỰC HIỆN (MỚI) ---
    pic_content = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks_content', verbose_name="NV Content")
    pic_design = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks_design', verbose_name="NV Dựng/Thiết kế")
    pic_ads = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks_ads', verbose_name="NV Chạy Ads")

    # --- TÀI NGUYÊN (MỚI) ---
    link_source = models.URLField(max_length=500, blank=True, null=True, verbose_name="Link Source (Kịch bản/Raw)")
    link_thumb = models.URLField(max_length=500, blank=True, null=True, verbose_name="Link Ảnh Thumb")
    link_final = models.URLField(max_length=500, blank=True, null=True, verbose_name="Link Final (Sản phẩm)")

    content = models.TextField(blank=True, verbose_name="Nội dung bài viết/Ghi chú")
    platform = models.CharField(max_length=50, default='Facebook', verbose_name="Nền tảng")
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.PLANNING, verbose_name="Trạng thái")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Công việc Marketing"
        verbose_name_plural = "Quản lý Content & Ads"

class DailyCampaignStat(models.Model):
    report_date = models.DateField(verbose_name="Ngày báo cáo")
    marketer = models.CharField(max_length=100, blank=True, null=True, verbose_name="Người chạy Ads")
    service = models.CharField(max_length=200, blank=True, null=True, verbose_name="Dịch vụ/Chiến dịch")
    spend_amount = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Chi tiêu (VNĐ)")
    
    inboxes = models.IntegerField(default=0, verbose_name="Tin nhắn (Inbox)")
    comments = models.IntegerField(default=0, verbose_name="Bình luận")
    leads = models.IntegerField(default=0, verbose_name="Số SĐT (Leads)")
    appointments = models.IntegerField(default=0, verbose_name="Số lịch hẹn")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ads {self.report_date}: {self.spend_amount:,.0f}đ"

    @property
    def cost_per_lead(self):
        return (self.spend_amount / self.leads) if self.leads > 0 else 0

    class Meta:
        verbose_name = "Số liệu Ads hàng ngày"
        verbose_name_plural = "Báo cáo Ads"