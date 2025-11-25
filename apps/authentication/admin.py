from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    model = User
    # 1. Hiển thị cột Vai trò ra ngoài danh sách
    list_display = ['username', 'first_name', 'last_name', 'role', 'phone', 'is_active']
    list_filter = ['role', 'is_active']
    
    # 2. Thêm ô nhập Vai trò & SĐT vào form chỉnh sửa (Edit)
    fieldsets = UserAdmin.fieldsets + (
        ('Thông tin Nhân viên (CRM)', {'fields': ('role', 'phone')}),
    )
    
    # 3. Thêm ô nhập Vai trò & SĐT vào form tạo mới (Add)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Thông tin Nhân viên (CRM)', {'fields': ('role', 'phone')}),
    )

# Đăng ký lại
admin.site.register(User, CustomUserAdmin)