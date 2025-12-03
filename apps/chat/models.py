from django.db import models
from django.conf import settings

class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    # --- MỚI THÊM ---
    # Tin nhắn cha (để trả lời)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    # Ghim tin nhắn
    is_pinned = models.BooleanField(default=False)

    def __str__(self):
        return f"Từ {self.sender} đến {self.receiver}: {self.content[:20]}..."

    class Meta:
        ordering = ['timestamp']