from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum
from datetime import date

class Fanpage(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Mã Fanpage")
    name = models.CharField(max_length=200, verbose_name="Tên Fanpage hiển thị")
    # Thay vì nhập tay, ta liên kết trực tiếp với tài khoản nhân viên trong hệ thống
    assigned_marketer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        limit_choices_to={'role__in': ['ADMIN', 'MARKETING']},
        verbose_name="Marketer phụ trách",
        related_name="managed_fanpages"
    )

    def __str__(self):
        return f"{self.name} ({self.assigned_marketer.last_name if self.assigned_marketer else 'Chưa gán'})"

    class Meta:
        verbose_name = "Fanpage"
        verbose_name_plural = "Danh sách Fanpage"

class Customer(models.Model):
    class SkinIssue(models.TextChoices):
        THREAD_LIFT = "THREAD_LIFT", "Căng chỉ"
        PROFHILO = "PROFHILO", "Profhilo" 
        EXOSONE = "EXOSONE", "Exosone"   
        REJURAN = "REJURAN", "Rejuran"   
        KARISMA = "KARISMA", "Karisma"   
        HAIR_TREATMENT = "HAIR_TREATMENT", "Tóc" 
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
    
    class FanpageChoices(models.TextChoices):
        CC_KIM_CUONG_SG_HV = "CC_KIM_CUONG_SG_HV", "Căng chỉ kim cương Sài Gòn - Bác sĩ Hoàng Vũ"
        ULTRA_DIAMOND_DB_HV = "ULTRA_DIAMOND_DB_HV", "Nâng cơ trẻ hoá Ultra Diamond - Bác sĩ Danh Bảo Hoàng Vũ"
        BS_HOANG_VU = "BS_HOANG_VU", "Bác Sĩ Hoàng Vũ - CK I Da Liễu"
        HOANG_VU = 'HOANG_VU', 'Bác sĩ CKI Hoàng Vũ - Viện da liễu V Medical'
        BS_QUAN = "BS_QUAN", "Cao Trần Quân - Viện Da Liễu V Medical"
        QUAN_SINCE_2006 = "QUAN_SINCE_2006", "Bác sĩ Cao Trần Quân - V Medical Clinic"
        VMEDICAL_CLINIC = "VMEDICAL_CLINIC", "V - Medical Clinic"
        DL_VMEDICAL = "DL_VMEDICAL", "Phòng Khám Da Liễu Thẩm Mỹ V-Medical"
        ULTHERAPY_57A = "ULTHERAPY_57A", "Ultherapy Prime - Căng Da Không Phẫu Thuật 57A Trần Quốc Thảo"
        OTHER = "OTHER", "Khác / Không rõ"
        VMEDICAL_PK_DL = "VMEDICAL_PK_DL", "V Medical - Phòng khám da liễu thẩm mỹ"
        PK_VMEDICAL_TM = "PK_VMEDICAL_TM", "Phòng Khám V Medical - Thẩm Mỹ Da Công Nghệ Cao"

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
    fanpages = models.ManyToManyField(Fanpage, blank=True, verbose_name="Các Fanpage Nguồn")
    fanpage = models.CharField(max_length=50, choices=FanpageChoices.choices, null=True, blank=True, verbose_name="Fanpage Nguồn (Cũ)")
    skin_condition = models.CharField(max_length=50, choices=SkinIssue.choices, default=SkinIssue.OTHER, verbose_name="Dịch vụ quan tâm")
    customer_code = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name="Mã khách hàng/ID")
    assigned_telesale = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'role': 'TELESALE'}, verbose_name="Telesale phụ trách")
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