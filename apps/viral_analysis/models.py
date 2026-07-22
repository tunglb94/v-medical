from django.conf import settings
from django.db import models


class ViralSubmission(models.Model):
    class Platform(models.TextChoices):
        TIKTOK = "TIKTOK", "TikTok"
        YOUTUBE = "YOUTUBE", "YouTube Shorts"
        FACEBOOK = "FACEBOOK", "Facebook Reels"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Đang chấm..."
        DONE = "DONE", "Đã chấm xong"
        ERROR = "ERROR", "Lỗi khi chấm"

    platform = models.CharField(max_length=10, choices=Platform.choices, verbose_name="Nền tảng")
    title = models.CharField(max_length=200, blank=True, verbose_name="Tên chủ đề/dự án")
    hook = models.TextField(verbose_name="Hook (3 giây đầu)")
    script_content = models.TextField(verbose_name="Nội dung kịch bản")
    post_caption = models.TextField(blank=True, verbose_name="Nội dung bài đăng (caption)")

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, verbose_name="Trạng thái")
    score = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Điểm số (0-100)")
    verdict = models.CharField(max_length=300, blank=True, verbose_name="Kết luận ngắn gọn")
    checks = models.JSONField(default=list, blank=True, verbose_name="Checklist từng tiêu chí (kiểu Yoast)")
    strengths = models.JSONField(default=list, blank=True, verbose_name="Điểm mạnh")
    weaknesses = models.JSONField(default=list, blank=True, verbose_name="Điểm yếu")
    suggestions = models.JSONField(default=list, blank=True, verbose_name="Gợi ý cải thiện")
    production_tips = models.JSONField(default=list, blank=True, verbose_name="Gợi ý sản xuất (hình ảnh/âm thanh/dựng phim)")
    platform_fit = models.TextField(blank=True, verbose_name="Nhận xét mức độ phù hợp nền tảng")
    error_message = models.TextField(blank=True, verbose_name="Lỗi (nếu có)")

    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='viral_submissions')
    created_at = models.DateTimeField(auto_now_add=True)
    analyzed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_platform_display()} - {self.title or self.hook[:40]}"

    class Meta:
        verbose_name = "Kịch bản Viral"
        verbose_name_plural = "Chấm điểm Viral"
        ordering = ['-created_at']
