from django.contrib import admin
from .models import Appointment

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    # Các cột hiển thị trong danh sách
    list_display = ('customer', 'appointment_date', 'status', 'assigned_consultant', 'created_by')
    
    # --- THÊM DÒNG NÀY ĐỂ TẠO BỘ LỌC BÊN PHẢI ---
    list_filter = (
        'status',               # Lọc theo Trạng thái
        'appointment_date',     # Lọc theo Ngày hẹn
        'assigned_consultant',  # Lọc theo Bác sĩ/Nhân viên phụ trách
        'created_by'            # Lọc theo Người tạo (Telesale)
    )
    
    # Thanh tìm kiếm (nếu cần)
    search_fields = ('customer__name', 'customer__phone', 'note')