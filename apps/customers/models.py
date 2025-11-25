from django.db import models

class Customer(models.Model):
    # --- CÁC KHAI BÁO CỐ ĐỊNH (CHOICES) ---
    class SkinIssue(models.TextChoices):
        ACNE = "ACNE", "Mụn viêm/Mụn ẩn"
        PIGMENTATION = "PIGMENTATION", "Nám/Tàn nhang"
        SCAR = "SCAR", "Sẹo rỗ"
        AGING = "AGING", "Lão hóa/Nếp nhăn"
        OTHER = "OTHER", "Khác"

    class Source(models.TextChoices):
        FACEBOOK = "FACEBOOK", "Facebook Ads"
        GOOGLE = "GOOGLE", "Google Ads"
        SEO = "SEO", "SEO Website"
        TIKTOK = "TIKTOK", "Tiktok"
        REFERRAL = "REFERRAL", "Bạn giới thiệu"
        OTHER = "OTHER", "Khác"

    # --- CÁC CỘT DỮ LIỆU ---
    name = models.CharField(max_length=100, verbose_name="Họ và Tên")
    phone = models.CharField(max_length=15, unique=True, verbose_name="Số điện thoại")
    age = models.IntegerField(null=True, blank=True, verbose_name="Tuổi")
    
    # Thay trường address cũ bằng city (Tỉnh thành)
    address = models.TextField(null=True, blank=True, verbose_name="Địa chỉ chi tiết") 
    city = models.CharField(max_length=50, blank=True, null=True, verbose_name="Tỉnh/Thành phố")
    
    source = models.CharField(
        max_length=20, 
        choices=Source.choices, 
        default=Source.FACEBOOK, 
        verbose_name="Nguồn khách"
    )
    
    skin_condition = models.CharField(
        max_length=50, 
        choices=SkinIssue.choices, 
        default=SkinIssue.OTHER, 
        verbose_name="Vấn đề về da"
    )
    
    note_telesale = models.TextField(blank=True, verbose_name="Ghi chú ban đầu")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    def __str__(self):
        return f"{self.name} ({self.phone})"