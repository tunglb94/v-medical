from django.db import models
from django.conf import settings
from django.utils import timezone

# --- 1. MODEL BÁO CÁO NGÀY (GIỮ NGUYÊN) ---
class DailyCampaignStat(models.Model):
    # Bỏ unique=True để 1 ngày có thể nhập nhiều dòng cho nhiều người chạy khác nhau
    report_date = models.DateField(verbose_name="Ngày báo cáo")
    
    # --- TRƯỜNG MỚI (NHẬP TEXT) ---
    marketer = models.CharField(max_length=100, blank=True, null=True, verbose_name="Người chạy Ads")
    service = models.CharField(max_length=200, blank=True, null=True, verbose_name="Dịch vụ/Sản phẩm")
    # -----------------------------

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
    def conversion_rate_appt(self):
        if self.leads > 0: return (self.appointments / self.leads) * 100
        return 0

    def __str__(self):
        return f"{self.report_date} - {self.marketer}"

    class Meta:
        verbose_name = "Báo cáo Marketing"
        verbose_name_plural = "Báo cáo Marketing"
        ordering = ['-report_date', 'marketer']

# --- 2. MODEL QUẢN LÝ CÔNG VIỆC (GIỮ NGUYÊN) ---
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
    pic = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Người phụ trách (PIC)")
    start_date = models.DateField(default=timezone.now, verbose_name="Ngày bắt đầu")
    deadline = models.DateField(verbose_name="Hạn chót (Deadline)")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO, verbose_name="Trạng thái")
    note = models.TextField(blank=True, verbose_name="Ghi chú/Yêu cầu")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_overdue(self):
        return self.status != 'DONE' and self.deadline < timezone.now().date()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Công việc Marketing"
        verbose_name_plural = "Quản lý Công việc"
        ordering = ['deadline']

# --- 3. MODEL MỚI: QUẢN LÝ CONTENT ADS ---
class ContentAd(models.Model):
    title = models.CharField(max_length=255, verbose_name="Tên Ads (Mã)")
    
    # Nhân sự thực hiện (Liên kết với User để quản lý trách nhiệm)
    content_creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_contents', limit_choices_to={'role': 'CONTENT'}, verbose_name="NV Content")
    editor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='edited_contents', limit_choices_to={'role': 'EDITOR'}, verbose_name="NV Editor")
    marketer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='running_ads', limit_choices_to={'role': 'MARKETING'}, verbose_name="Người chạy Ads")

    # Nội dung chi tiết
    ad_headline = models.CharField(max_length=255, blank=True, verbose_name="Tiêu đề (Headline)")
    post_content = models.TextField(blank=True, verbose_name="Nội dung bài Post")
    
    # Link tài nguyên (Source)
    link_video = models.URLField(blank=True, null=True, verbose_name="Link Source Video")
    link_thumb = models.URLField(blank=True, null=True, verbose_name="Link Source Thumb")
    
    # Kết quả (Không bắt buộc)
    result_note = models.TextField(blank=True, verbose_name="Kết quả chạy/Ghi chú")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Content Quảng Cáo"
        verbose_name_plural = "Kho Content & Ads"
        ordering = ['-created_at']