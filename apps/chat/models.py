from django.db import models
from django.conf import settings

class Message(models.Model):
    # ... (Giữ nguyên code cũ của Message)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    is_pinned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender} -> {self.receiver}"

    class Meta:
        ordering = ['timestamp']

# --- MỚI THÊM: BẢNG THÔNG BÁO ---
class Announcement(models.Model):
    TARGET_CHOICES = [
        ('ALL', 'Toàn bộ hệ thống'),
        ('TELESALE', 'Team Telesale'),
        ('MARKETING', 'Team Marketing'),
        ('RECEPTIONIST', 'Team Lễ tân'),
    ]
    
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Người tạo")
    title = models.CharField(max_length=200, verbose_name="Tiêu đề")
    content = models.TextField(verbose_name="Nội dung")
    target_role = models.CharField(max_length=50, choices=TARGET_CHOICES, default='ALL', verbose_name="Gửi tới")
    is_active = models.BooleanField(default=True, verbose_name="Hiển thị (Ghim)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']