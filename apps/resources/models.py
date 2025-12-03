from django.db import models
from django.conf import settings

class ProductDocument(models.Model):
    CATEGORY_CHOICES = [
        ('MACHINE', 'Công nghệ / Máy móc'),
        ('SERVICE', 'Dịch vụ điều trị'),
        ('PROTOCOL', 'Phác đồ điều trị'),
        ('OTHER', 'Tài liệu khác'),
    ]

    title = models.CharField(max_length=200, verbose_name="Tên tài liệu / Dịch vụ")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='MACHINE', verbose_name="Danh mục")
    
    # Ảnh minh họa chính
    image = models.ImageField(upload_to='documents/', blank=True, null=True, verbose_name="Ảnh đại diện")
    
    # Nội dung chi tiết (Mô tả cơ chế, ưu điểm...)
    content = models.TextField(verbose_name="Nội dung chi tiết (Hỗ trợ HTML)")
    
    # File đính kèm (PDF, Slide nếu có)
    attachment = models.FileField(upload_to='documents/files/', blank=True, null=True, verbose_name="File đính kèm (PDF/PPT)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Tài liệu sản phẩm"
        verbose_name_plural = "Kho Tài liệu & Đào tạo"