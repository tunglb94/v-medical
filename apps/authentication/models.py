from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Quản trị viên"
        TELESALE = "TELESALE", "Nhân viên Telesale"
        RECEPTIONIST = "RECEPTIONIST", "Lễ tân"
        DOCTOR = "DOCTOR", "Bác sĩ"
        CONSULTANT = "CONSULTANT", "Sale Tư vấn"
        TECHNICIAN = "TECHNICIAN", "Kỹ thuật viên"
        MARKETING = "MARKETING", "Marketing (Chạy Ads)"
        CONTENT = "CONTENT", "Nhân viên Content"
        EDITOR = "EDITOR", "Nhân viên Editor"
        DESIGNER = "DESIGNER", "Nhân viên Thiết kế"

    class Team(models.TextChoices):
        TEAM_A = "TEAM_A", "Team A"
        TEAM_B = "TEAM_B", "Team B"

    role = models.CharField(max_length=50, choices=Role.choices, default=Role.ADMIN, verbose_name="Vai trò")
    
    team = models.CharField(max_length=20, choices=Team.choices, null=True, blank=True, verbose_name="Nhóm Telesale")
    
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="Số điện thoại")

    # [MỚI] Trường lưu danh sách menu được phép xem (Dạng List JSON)
    allowed_menus = models.JSONField(default=list, blank=True, verbose_name="Menu được phép truy cập")

    def __str__(self):
        team_str = f" - {self.get_team_display()}" if self.team else ""
        return f"{self.username} - {self.get_role_display()}{team_str}"

    # [MỚI] Hàm kiểm tra quyền dùng trong Template base.html
    def has_menu_access(self, menu_key):
        # 1. Admin và Superuser luôn thấy tất cả
        if self.is_superuser or self.role == 'ADMIN':
            return True
        
        # 2. Kiểm tra trong danh sách được cấp
        if self.allowed_menus and isinstance(self.allowed_menus, list):
            return menu_key in self.allowed_menus
        
        # 3. [Tùy chọn] Fallback cho User cũ chưa set allowed_menus (Giữ logic cũ nếu cần)
        # Tuy nhiên, để linh hoạt tuyệt đối, ta nên trả về False nếu không có trong list.
        # Điều này có nghĩa: Sau khi update code, bạn cần vào sửa nhân viên và tick chọn quyền cho họ.
        return False