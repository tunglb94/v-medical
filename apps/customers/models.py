from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum
from datetime import date

class Customer(models.Model):
    # GIỮ NGUYÊN TÊN CLASS LÀ SkinIssue
    class SkinIssue(models.TextChoices):
        # --- CÁC DỊCH VỤ MỚI ---
        THREAD_LIFT = "THREAD_LIFT", "Căng chỉ"  # <--- Đã thêm theo yêu cầu
        PROFHILO = "PROFHILO", "Profhilo" 
        EXOSONE = "EXOSONE", "Exosone"   
        REJURAN = "REJURAN", "Rejuran"   
        KARISMA = "KARISMA", "Karisma"   
        HAIR_TREATMENT = "HAIR_TREATMENT", "Tóc" 
        
        # --- CÁC DỊCH VỤ CŨ ---
        ULTHERAPY = "ULTHERAPY", "Ultherapy"
        THERMA = "THERMA", "Therma"
        PRP = "PRP", "PRP"
        VAGINAL_REJUVENATION = "VAGINAL_REJUVENATION", "Trẻ hoá vùng kín"
        HAIR_REMOVAL = "HAIR_REMOVAL", "Triệt lông"
        FAT_REDUCTION = "FAT_REDUCTION", "Giảm béo"
        LASER = "LASER", "Laser"
        OTHER = "OTHER", "Khác"

    class Source(models.TextChoices):
        FACEBOOK = "FACEBOOK", "Facebook Ads"
        GOOGLE = "GOOGLE", "Google Ads"
        SEO = "SEO", "SEO Website"
        TIKTOK = "TIKTOK", "Tiktok"
        REFERRAL = "REFERRAL", "Bạn giới thiệu"
        OTHER = "OTHER", "Khác"
    
    # --- CẬP NHẬT: THÊM DANH SÁCH FANPAGE ---
    class Fanpage(models.TextChoices):
        # <--- MỚI THÊM 2 PAGE BÁC SĨ HOÀNG VŨ ---
        CC_KIM_CUONG_SG_HV = "CC_KIM_CUONG_SG_HV", "Căng chỉ kim cương Sài Gòn - Bác sĩ Hoàng Vũ"
        ULTRA_DIAMOND_DB_HV = "ULTRA_DIAMOND_DB_HV", "Nâng cơ trẻ hoá Ultra Diamond - Bác sĩ Danh Bảo Hoàng Vũ"
        
        # CÁC PAGE CŨ
        BS_QUAN = "BS_QUAN", "Bác sĩ Cao Trần Quân"
        VMEDICAL_CLINIC = "VMEDICAL_CLINIC", "V - Medical Clinic"
        DL_VMEDICAL = "DL_VMEDICAL", "Phòng Khám Da Liễu Thẩm Mỹ V-Medical"
        QUAN_SINCE_2006 = "QUAN_SINCE_2006", "Cao Trần Quân - Viện Da Liễu V Medical since 2006"
        ULTHERAPY_57A = "ULTHERAPY_57A", "Ultherapy Prime - Căng Da Không Phẫu Thuật 57A Trần Quốc Thảo"
        OTHER = "OTHER", "Khác / Không rõ"

    class Ranking(models.TextChoices):
        MEMBER = "MEMBER", "Thành viên"
        SILVER = "SILVER", "Bạc"
        GOLD = "GOLD", "Vàng"
        DIAMOND = "DIAMOND", "Kim Cương"
        
    class Gender(models.TextChoices):
        FEMALE = "FEMALE", "Nữ"
        MALE = "MALE", "Nam"
        UNKNOWN = "UNKNOWN", "Không rõ"

    name = models.CharField(max_length=100, verbose_name="Họ và Tên")
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.FEMALE, verbose_name="Giới tính")
    phone = models.CharField(max_length=15, unique=True, verbose_name="Số điện thoại")
    dob = models.DateField(null=True, blank=True, verbose_name="Ngày sinh")
    address = models.TextField(null=True, blank=True, verbose_name="Địa chỉ chi tiết")
    city = models.CharField(max_length=50, blank=True, null=True, verbose_name="Tỉnh/Thành phố")
    
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.FACEBOOK, verbose_name="Nguồn khách")
    
    fanpage = models.CharField(max_length=50, choices=Fanpage.choices, null=True, blank=True, verbose_name="Fanpage Nguồn")

    skin_condition = models.CharField(max_length=50, choices=SkinIssue.choices, default=SkinIssue.OTHER, verbose_name="Dịch vụ quan tâm")
    
    customer_code = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name="Mã khách hàng/ID")

    assigned_telesale = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        limit_choices_to={'role': 'TELESALE'},
        verbose_name="Telesale phụ trách"
    )

    note_telesale = models.TextField(blank=True, verbose_name="Ghi chú ban đầu")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Ngày tạo")
    ranking = models.CharField(max_length=20, choices=Ranking.choices, default=Ranking.MEMBER, verbose_name="Hạng thành viên")

    @property
    def age(self):
        if self.dob:
            today = date.today()
            return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
        return None

    def update_ranking(self):
        # Tránh import vòng lặp nếu cần
        total_spent = self.order_set.filter(is_paid=True).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        if total_spent > 70000000: self.ranking = self.Ranking.DIAMOND
        elif total_spent >= 20000000: self.ranking = self.Ranking.GOLD
        elif total_spent >= 10000000: self.ranking = self.Ranking.SILVER
        else: self.ranking = self.Ranking.MEMBER
        self.save()

    def __str__(self):
        return f"{self.name} ({self.phone})"

    class Meta:
        verbose_name = "Khách hàng"
        verbose_name_plural = "Danh sách Khách hàng"