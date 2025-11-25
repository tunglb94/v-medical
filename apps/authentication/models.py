from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Quản trị viên"
        TELESALE = "TELESALE", "Nhân viên Telesale"
        RECEPTIONIST = "RECEPTIONIST", "Lễ tân"
        DOCTOR = "DOCTOR", "Bác sĩ"
        CONSULTANT = "CONSULTANT", "Sale Tư vấn"
        TECHNICIAN = "TECHNICIAN", "Kỹ thuật viên" # <--- MỚI THÊM

    role = models.CharField(max_length=50, choices=Role.choices, default=Role.ADMIN, verbose_name="Vai trò")
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="Số điện thoại")

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"