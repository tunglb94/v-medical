from django.contrib import admin
from .models import DailyCampaignStat, MarketingTask, ContentAd

# 1. Quản lý Báo cáo Ngày
@admin.register(DailyCampaignStat)
class DailyCampaignStatAdmin(admin.ModelAdmin):
    list_display = ('report_date', 'marketer', 'service', 'spend_amount', 'leads', 'cost_per_lead')
    list_filter = ('report_date', 'marketer', 'service')
    search_fields = ('marketer', 'service')
    date_hierarchy = 'report_date'

# 2. Quản lý Công việc (Task)
@admin.register(MarketingTask)
class MarketingTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'pic', 'deadline', 'status', 'is_overdue')
    list_filter = ('status', 'category', 'pic')
    search_fields = ('title', 'note')
    date_hierarchy = 'deadline'

    @admin.display(description='Quá hạn?', boolean=True)
    def is_overdue(self, obj):
        return obj.is_overdue

# 3. Quản lý Content Ads (Mới)
@admin.register(ContentAd)
class ContentAdAdmin(admin.ModelAdmin):
    list_display = ('title', 'ad_headline', 'content_creator', 'editor', 'marketer', 'created_at')
    list_filter = ('content_creator', 'editor', 'marketer', 'created_at')
    search_fields = ('title', 'ad_headline', 'post_content')
    date_hierarchy = 'created_at'