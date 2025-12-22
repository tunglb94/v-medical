from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    model = User
    # 1. Hiển thị cột Vai trò và Team ra ngoài danh sách
    list_display = ['username', 'first_name', 'last_name', 'role', 'team', 'phone', 'is_active']
    
    # Thêm bộ lọc theo Team để dễ quản lý
    list_filter = ['role', 'team', 'is_active']
    
    # 2. Thêm ô nhập Team vào form chỉnh sửa (Edit)
    fieldsets = UserAdmin.fieldsets + (
        ('Thông tin Nhân viên (CRM)', {'fields': ('role', 'team', 'phone')}),
    )
    
    # 3. Thêm ô nhập Team vào form tạo mới (Add)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Thông tin Nhân viên (CRM)', {'fields': ('role', 'team', 'phone')}),
    )

# Đăng ký lại
admin.site.register(User, CustomUserAdmin)