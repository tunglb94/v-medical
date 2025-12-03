from django.db import models
from django.conf import settings
from apps.sales.models import Service

# 1. QUẢN LÝ CÔNG VIỆC & CONTENT (ĐÃ CẬP NHẬT)
class MarketingTask(models.Model):
    class Status(models.TextChoices):
        PLANNING = 'PLANNING', 'Lên kế hoạch'
        WRITING = 'WRITING', 'Đang viết/Sản xuất'
        DESIGNING = 'DESIGNING', 'Đang thiết kế'
        RUNNING = 'RUNNING', 'Đang chạy Ads'
        COMPLETED = 'COMPLETED', 'Hoàn thành'
        PAUSED = 'PAUSED', 'Tạm dừng'

    title = models.CharField(max_length=200, verbose_name="Tiêu đề/Chủ đề")
    
    # Các trường mở rộng
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Dịch vụ quảng bá")
    start_date = models.DateField(null=True, blank=True, verbose_name="Ngày bắt đầu")
    deadline = models.DateField(null=True, blank=True, verbose_name="Deadline")
    script_link = models.URLField(max_length=500, blank=True, null=True, verbose_name="Link kịch bản")

    content = models.TextField(blank=True, verbose_name="Nội dung bài viết")
    platform = models.CharField(max_length=50, default='Facebook', verbose_name="Nền tảng")
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.PLANNING, verbose_name="Trạng thái")
    
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Người phụ trách")
    budget = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Ngân sách dự kiến")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Công việc Marketing"
        verbose_name_plural = "Quản lý Content & Ads"

# 2. BÁO CÁO SỐ LIỆU ADS (KHÔI PHỤC CÁC TRƯỜNG BỊ THIẾU)
class DailyCampaignStat(models.Model):
    report_date = models.DateField(verbose_name="Ngày báo cáo") # Đổi từ 'date' thành 'report_date'
    
    marketer = models.CharField(max_length=100, blank=True, null=True, verbose_name="Người chạy Ads")
    service = models.CharField(max_length=200, blank=True, null=True, verbose_name="Dịch vụ/Chiến dịch")
    
    spend_amount = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Chi tiêu (VNĐ)") # Đổi từ 'spend'
    
    # Các chỉ số chi tiết
    inboxes = models.IntegerField(default=0, verbose_name="Tin nhắn (Inbox)")
    comments = models.IntegerField(default=0, verbose_name="Bình luận")
    leads = models.IntegerField(default=0, verbose_name="Số SĐT (Leads)")
    appointments = models.IntegerField(default=0, verbose_name="Số lịch hẹn")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ads {self.report_date}: {self.spend_amount:,.0f}đ"

    # Property tính toán (dùng trong Admin)
    @property
    def cost_per_lead(self):
        if self.leads > 0:
            return self.spend_amount / self.leads
        return 0

    class Meta:
        verbose_name = "Số liệu Ads hàng ngày"
        verbose_name_plural = "Báo cáo Ads"

# 3. CONTENT ADS (MODEL MỚI)
class ContentAd(models.Model):
    title = models.CharField(max_length=200, verbose_name="Tiêu đề nội bộ")
    ad_headline = models.CharField(max_length=200, verbose_name="Headline (Giật tít)")
    post_content = models.TextField(verbose_name="Nội dung bài viết")
    
    content_creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_ads', verbose_name="Người viết")
    editor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='edited_ads', verbose_name="Editor duyệt")
    marketer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='marketing_ads', verbose_name="Marketer chạy")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Bài Content Ads"
        verbose_name_plural = "Kho Content Quảng Cáo"