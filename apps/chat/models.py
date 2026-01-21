from django.db import models
from django.conf import settings

class Room(models.Model):
    ROOM_TYPES = (
        ('DIRECT', 'Chat Riêng'),
        ('GROUP', 'Chat Nhóm'),
    )
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Tên nhóm")
    type = models.CharField(max_length=10, choices=ROOM_TYPES, default='DIRECT')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chat_rooms')
    admins = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chat_admin_rooms', verbose_name="Trưởng nhóm")
    updated_at = models.DateTimeField(auto_now=True) # Để sắp xếp phòng nào mới nhắn lên đầu

    def __str__(self):
        return self.name if self.name else f"Room {self.id}"

class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    # Bỏ receiver, vì tin nhắn giờ gửi vào Room
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False) # Logic: Ai đọc thì đánh dấu (cần bảng riêng nếu muốn chính xác từng người, ở đây làm đơn giản)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    is_pinned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender} in {self.room}"

    class Meta:
        ordering = ['timestamp']

# --- GIỮ NGUYÊN: BẢNG THÔNG BÁO ---
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