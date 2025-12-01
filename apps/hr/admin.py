from django.contrib import admin
from .models import EmployeeContract, Attendance, SalarySlip

@admin.register(EmployeeContract)
class EmployeeContractAdmin(admin.ModelAdmin):
    list_display = ('user', 'base_salary', 'allowance', 'commission_rate', 'start_date')
    search_fields = ('user__username', 'user__last_name', 'user__email')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    # Cập nhật hiển thị theo model mới (bỏ check_in, check_out cũ)
    list_display = ('user', 'date', 'is_present', 'created_at')
    list_filter = ('date', 'is_present')
    search_fields = ('user__username', 'user__last_name')

@admin.register(SalarySlip)
class SalarySlipAdmin(admin.ModelAdmin):
    # Cập nhật hiển thị (bỏ is_finalized cũ)
    list_display = ('user', 'month', 'actual_work_days', 'sales_revenue', 'total_salary', 'created_at')
    list_filter = ('month',)
    search_fields = ('user__username', 'user__last_name')