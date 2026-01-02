from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum
from datetime import date

# --- 1. MODEL QUẢN LÝ FANPAGE (ĐỘNG) ---
class Fanpage(models.Model):
    name = models.CharField(max_length=255, verbose_name="Tên Fanpage")
    status = models.BooleanField(default=True, verbose_name="Đang hoạt động")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Cấu hình: Fanpage"
        verbose_name_plural = "Cấu hình: Danh sách Fanpage"

# --- 2. MODEL QUẢN LÝ NGUỒN KHÁCH (ĐỘNG) ---
class CustomerSource(models.Model):
    name = models.CharField(max_length=100, verbose_name="Tên Nguồn")
    status = models.BooleanField(default=True, verbose_name="Đang hoạt động")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Cấu hình: Nguồn khách"
        verbose_name_plural = "Cấu hình: Danh sách Nguồn"

# --- 3. MODEL QUẢN LÝ DỊCH VỤ (ĐỘNG) ---
class Service(models.Model):
    name = models.CharField(max_length=100, verbose_name="Tên Dịch vụ")
    status = models.BooleanField(default=True, verbose_name="Đang hoạt động")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Cấu hình: Dịch vụ"
        verbose_name_plural = "Cấu hình: Danh sách Dịch vụ"


# --- 4. MODEL KHÁCH HÀNG (CHÍNH) ---
class Customer(models.Model):
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
    
    # [THAY ĐỔI] Dùng ForeignKey thay vì CharField cứng
    source = models.ForeignKey(CustomerSource, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Nguồn khách")
    fanpage = models.ForeignKey(Fanpage, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Fanpage Nguồn")
    skin_condition = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Dịch vụ quan tâm")
    
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