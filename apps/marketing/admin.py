from django.contrib import admin
from django.utils import timezone
from .models import DailyCampaignStat, MarketingTask

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
    # Cập nhật hiển thị theo các trường mới
    list_display = ('title', 'platform', 'pic_content', 'deadline', 'status', 'is_overdue_display')
    list_filter = ('status', 'platform', 'pic_content', 'pic_ads')
    search_fields = ('title', 'content')
    date_hierarchy = 'deadline'

    @admin.display(description='Quá hạn?', boolean=True)
    def is_overdue_display(self, obj):
        if obj.deadline and obj.status != 'COMPLETED':
            return obj.deadline < timezone.now().date()
        return False