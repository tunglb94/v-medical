from django.contrib import admin
from .models import FacebookPage, FacebookPostLog

@admin.register(FacebookPage)
class FacebookPageAdmin(admin.ModelAdmin):
    list_display = ('name', 'page_id', 'is_active')
    search_fields = ('name', 'page_id')
    list_filter = ('is_active',)
    # Cấu hình filter_horizontal giúp bạn dễ dàng gán quyền nhân viên bằng 2 cột kéo thả (dành cho sau này)
    filter_horizontal = ('allowed_staff',) 

@admin.register(FacebookPostLog)
class FacebookPostLogAdmin(admin.ModelAdmin):
    list_display = ('page', 'staff', 'status', 'created_at')
    list_filter = ('status', 'page', 'staff')
    search_fields = ('content', 'post_id', 'error_message')
    readonly_fields = ('created_at',)