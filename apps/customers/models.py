from django.db import models
from datetime import date
from django.utils import timezone
from django.db.models import Sum

class Customer(models.Model):
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

    # --- THÊM HẠNG THÀNH VIÊN ---
    class Ranking(models.TextChoices):
        MEMBER = "MEMBER", "Thành viên"       # < 10tr
        SILVER = "SILVER", "Bạc"              # 10 - 20tr
        GOLD = "GOLD", "Vàng"                 # 20 - 70tr
        DIAMOND = "DIAMOND", "Kim Cương"      # > 70tr

    name = models.CharField(max_length=100, verbose_name="Họ và Tên")
    phone = models.CharField(max_length=15, unique=True, verbose_name="Số điện thoại")
    dob = models.DateField(null=True, blank=True, verbose_name="Ngày sinh")
    address = models.TextField(null=True, blank=True, verbose_name="Địa chỉ chi tiết")
    city = models.CharField(max_length=50, blank=True, null=True, verbose_name="Tỉnh/Thành phố")
    
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.FACEBOOK, verbose_name="Nguồn khách")
    skin_condition = models.CharField(max_length=50, choices=SkinIssue.choices, default=SkinIssue.OTHER, verbose_name="Vấn đề về da")
    note_telesale = models.TextField(blank=True, verbose_name="Ghi chú ban đầu")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Ngày tạo")

    # Trường lưu hạng thành viên (Mới thêm)
    ranking = models.CharField(
        max_length=20, 
        choices=Ranking.choices, 
        default=Ranking.MEMBER, 
        verbose_name="Hạng thành viên"
    )

    @property
    def age(self):
        if self.dob:
            today = date.today()
            return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
        return None

    # --- HÀM TỰ ĐỘNG CẬP NHẬT HẠNG ---
    def update_ranking(self):
        # Tính tổng tiền từ các đơn hàng ĐÃ THANH TOÁN
        # Lưu ý: Cần import Order bên trong để tránh lỗi vòng lặp (circular import) nếu cần, 
        # hoặc dùng related_name 'orders' nếu đã định nghĩa bên Model Order.
        # Ở đây ta dùng reverse relation mặc định là 'order_set' hoặc 'orders' tùy definition.
        # Giả sử bên Order khai báo: customer = ForeignKey(..., related_name='orders')
        
        total_spent = self.order_set.filter(is_paid=True).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        old_rank = self.ranking
        
        if total_spent > 70000000:
            self.ranking = self.Ranking.DIAMOND
        elif total_spent >= 20000000:
            self.ranking = self.Ranking.GOLD
        elif total_spent >= 10000000:
            self.ranking = self.Ranking.SILVER
        else:
            self.ranking = self.Ranking.MEMBER
            
        if old_rank != self.ranking:
            self.save()

    def __str__(self):
        return f"{self.name} ({self.phone}) - {self.get_ranking_display()}"

    class Meta:
        verbose_name = "Khách hàng"
        verbose_name_plural = "Danh sách Khách hàng"