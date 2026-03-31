from django.db import models
from django.conf import settings

class FacebookPage(models.Model):
    name = models.CharField(max_length=255, verbose_name="Tên Fanpage")
    page_id = models.CharField(max_length=100, unique=True, verbose_name="Page ID")
    access_token = models.TextField(verbose_name="Page Access Token")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    allowed_staff = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, verbose_name="Nhân viên được quyền đăng")

    class Meta:
        verbose_name = "Cấu hình Fanpage"
        verbose_name_plural = "Cấu hình Fanpage"

    def __str__(self):
        return self.name