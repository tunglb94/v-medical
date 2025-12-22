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
        DESIGNER = "DESIGNER", "Nhân viên Thiết kế" # <--- MỚI THÊM

    # --- THÊM CLASS TEAM ĐỂ CHIA ĐỘI ---
    class Team(models.TextChoices):
        TEAM_A = "TEAM_A", "Team A"
        TEAM_B = "TEAM_B", "Team B"

    role = models.CharField(max_length=50, choices=Role.choices, default=Role.ADMIN, verbose_name="Vai trò")
    
    # --- THÊM FIELD TEAM (Null=True vì các vai trò khác không cần team) ---
    team = models.CharField(max_length=20, choices=Team.choices, null=True, blank=True, verbose_name="Nhóm Telesale")
    
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="Số điện thoại")

    def __str__(self):
        # Cập nhật hiển thị: Nếu có team thì hiện thêm tên team phía sau
        team_str = f" - {self.get_team_display()}" if self.team else ""
        return f"{self.username} - {self.get_role_display()}{team_str}"