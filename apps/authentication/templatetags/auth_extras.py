from django import template

register = template.Library()

@register.filter(name='has_menu_access')
def has_menu_access(user, menu_key):
    """
    Kiểm tra quyền truy cập menu.
    Sử dụng trong template: request.user|has_menu_access:"telesale"
    """
    if not user or not user.is_authenticated:
        return False
    
    # Gọi hàm kiểm tra quyền đã viết trong Model User
    # (Hàm has_menu_access trong apps/authentication/models.py)
    if hasattr(user, 'has_menu_access'):
        return user.has_menu_access(menu_key)
    
    return False