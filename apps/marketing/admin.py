from django.contrib import admin
from django.utils import timezone
from .models import DailyCampaignStat, MarketingTask, ContentAd

# 1. Quản lý Báo cáo Ngày
@admin.register(DailyCampaignStat)
class DailyCampaignStatAdmin(admin.ModelAdmin):
    # Đã sửa 'date' -> 'report_date', 'spend' -> 'spend_amount'
    list_display = ('report_date', 'marketer', 'service', 'spend_amount', 'leads', 'cost_per_lead')
    list_filter = ('report_date', 'marketer', 'service')
    search_fields = ('marketer', 'service')
    date_hierarchy = 'report_date'

# 2. Quản lý Công việc (Task)
@admin.register(MarketingTask)
class MarketingTaskAdmin(admin.ModelAdmin):
    # Sửa: category -> platform, pic -> assigned_to
    list_display = ('title', 'platform', 'assigned_to', 'deadline', 'status', 'is_overdue_display')
    list_filter = ('status', 'platform', 'assigned_to')
    # Sửa: note -> content
    search_fields = ('title', 'content')
    date_hierarchy = 'deadline'

    # Tạo cột hiển thị Quá hạn (tính toán trực tiếp)
    @admin.display(description='Quá hạn?', boolean=True)
    def is_overdue_display(self, obj):
        if obj.deadline and obj.status != 'COMPLETED':
            return obj.deadline < timezone.now().date()
        return False

# 3. Quản lý Content Ads
@admin.register(ContentAd)
class ContentAdAdmin(admin.ModelAdmin):
    list_display = ('title', 'ad_headline', 'content_creator', 'editor', 'marketer', 'created_at')
    list_filter = ('content_creator', 'editor', 'marketer', 'created_at')
    search_fields = ('title', 'ad_headline', 'post_content')
    date_hierarchy = 'created_at'