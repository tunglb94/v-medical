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

class DailyCampaignStat(models.Model):
    date = models.DateField(verbose_name="Ngày báo cáo")
    spend = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Chi tiêu (VNĐ)")
    impressions = models.IntegerField(default=0, verbose_name="Lượt hiển thị")
    clicks = models.IntegerField(default=0, verbose_name="Lượt Click")
    conversions = models.IntegerField(default=0, verbose_name="Chuyển đổi (Tin nhắn/Form)")
    revenue_ads = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Doanh thu từ Ads")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ads {self.date}: {self.spend:,.0f}đ"

    class Meta:
        verbose_name = "Số liệu Ads hàng ngày"
        verbose_name_plural = "Báo cáo Ads"

# --- BỔ SUNG MODEL CONTENT AD CÒN THIẾU ---
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