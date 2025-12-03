from django.db import models

class ProductDocument(models.Model):
    CATEGORY_CHOICES = [
        ('MACHINE', 'Máy móc & Công nghệ'),
        ('PROTOCOL', 'Phác đồ điều trị'),
        ('SERVICE', 'Dịch vụ lâm sàng'),
    ]

    title = models.CharField(max_length=200, verbose_name="Tên tài liệu")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='MACHINE')
    image_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="Link Ảnh minh họa")
    
    # THAY ĐỔI QUAN TRỌNG: Thay vì lưu nội dung dài, ta lưu TÊN FILE template
    template_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tên file HTML nội dung (VD: ultherapy.html)")
    
    # Vẫn giữ content ngắn để làm mô tả sơ lược (Preview)
    short_description = models.TextField(verbose_name="Mô tả ngắn", blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Tài liệu đào tạo"
        verbose_name_plural = "Kho Tài liệu"