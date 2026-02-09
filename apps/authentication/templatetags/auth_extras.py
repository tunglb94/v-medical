from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

@register.filter(name='has_menu_access')
def has_menu_access(user, menu_name):
    """
    Kiểm tra quyền truy cập menu:
    1. Nếu là Admin -> True
    2. Nếu user có key của menu trong list allowed_menus -> True
    """
    return user.has_menu_access(menu_name)