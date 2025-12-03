from django.db import models

class ProductDocument(models.Model):
    CATEGORY_CHOICES = [
        ('MACHINE', 'Máy móc & Công nghệ'),
        ('PROTOCOL', 'Phác đồ điều trị'),
        ('SERVICE', 'Dịch vụ lâm sàng'),
    ]

    title = models.CharField(max_length=200, verbose_name="Tên tài liệu")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='MACHINE')
    
    # Link ảnh online (để dùng được script tự động)
    image_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="Link Ảnh minh họa")
    
    content = models.TextField(verbose_name="Nội dung chi tiết")
    
    created_at = models.DateTimeField(auto_now_add=True)
    # THÊM LẠI DÒNG NÀY ĐỂ KHỚP VỚI ADMIN
    updated_at = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Tài liệu đào tạo"
        verbose_name_plural = "Kho Tài liệu"