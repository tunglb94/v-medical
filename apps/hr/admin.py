from django.contrib import admin
from .models import EmployeeContract, Attendance, SalarySlip

@admin.register(EmployeeContract)
class EmployeeContractAdmin(admin.ModelAdmin):
    list_display = ('user', 'base_salary', 'allowance', 'start_date')
    search_fields = ('user__username', 'user__first_name')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'check_in', 'check_out', 'ip_address')
    list_filter = ('date', 'user')
    date_hierarchy = 'date'

@admin.register(SalarySlip)
class SalarySlipAdmin(admin.ModelAdmin):
    list_display = ('user', 'month', 'actual_work_days', 'total_salary', 'is_finalized')
    list_filter = ('month', 'is_finalized')