from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

@register.filter(name='has_menu_access')
def has_menu_access(user, menu_name):
    """
    Kiểm tra quyền truy cập menu dựa trên Role của user
    """
    if user.is_superuser or user.role == 'ADMIN':
        return True

    # Cấu hình quyền truy cập Menu
    permissions = {
        # [CẬP NHẬT] Thêm MARKETING vào đây
        'telesale': ['TELESALE', 'MANAGER', 'MARKETING', 'DIRECTOR'], 
        
        # [CẬP NHẬT] Thêm MARKETING vào đây
        'reception': ['RECEPTIONIST', 'MANAGER', 'MARKETING', 'DIRECTOR'],
        
        'service_calendar': ['TECHNICIAN', 'DOCTOR', 'RECEPTIONIST', 'MANAGER', 'ADMIN'],
        'inventory': ['INVENTORY', 'ADMIN', 'MANAGER'],
        'debt': ['ACCOUNTANT', 'ADMIN', 'MANAGER', 'TELESALE'],
        'customers': ['TELESALE', 'RECEPTIONIST', 'MARKETING', 'MANAGER', 'CONSULTANT', 'ADMIN'],
        'marketing': ['MARKETING', 'ADMIN', 'MANAGER', 'CONTENT', 'EDITOR', 'DESIGNER'],
        'sales_report': ['ADMIN', 'MANAGER', 'ACCOUNTANT', 'DIRECTOR'],
        'resources': ['ADMIN', 'MANAGER', 'TELESALE', 'CONSULTANT', 'RECEPTIONIST', 'TECHNICIAN', 'DOCTOR'],
        'hr': ['ADMIN', 'HR', 'DIRECTOR'],
        'attendance': ['ADMIN', 'HR', 'DIRECTOR', 'MANAGER'],
        'chat': ['ADMIN', 'TELESALE', 'MARKETING', 'RECEPTIONIST', 'DOCTOR', 'TECHNICIAN', 'CONTENT', 'EDITOR', 'DESIGNER', 'HR', 'ACCOUNTANT']
    }

    allowed_roles = permissions.get(menu_name, [])
    return user.role in allowed_roles