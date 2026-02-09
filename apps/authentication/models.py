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

    # [QUAN TRỌNG] Lưu danh sách các menu được phép truy cập (Ví dụ: ['telesale', 'marketing'])
    allowed_menus = models.JSONField(default=list, blank=True, verbose_name="Quyền truy cập Menu")

    def __str__(self):
        team_str = f" - {self.get_team_display()}" if self.team else ""
        return f"{self.username} - {self.get_role_display()}{team_str}"

    def has_menu_access(self, menu_key):
        """Hàm kiểm tra quyền dùng trong Template và View"""
        # 1. Admin tối cao luôn có quyền
        if self.is_superuser or self.role == 'ADMIN':
            return True
        
        # 2. Kiểm tra trong danh sách JSON đã tích chọn
        if self.allowed_menus and isinstance(self.allowed_menus, list):
            return menu_key in self.allowed_menus
            
        return False