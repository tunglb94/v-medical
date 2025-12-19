from django.contrib import admin
from django.utils.html import format_html
from .models import CallLog

@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    # 1. Các cột hiển thị trên danh sách
    list_display = (
        'get_customer_name', 
        'get_customer_phone', 
        'get_customer_fanpage',   # <--- Hiển thị Fanpage
        'get_customer_service',   # <--- Hiển thị Dịch vụ
        'status_colored',         # <--- Trạng thái có màu
        'caller', 
        'call_time',
        'callback_time'
    )

    # 2. Các bộ lọc bên tay phải
    list_filter = (
        'status', 
        'caller', 
        'call_time',
        'customer__fanpage',       # <--- Lọc theo Fanpage
        'customer__skin_condition' # <--- Lọc theo Dịch vụ
    )

    # 3. Ô tìm kiếm (Tìm theo thông tin khách hàng)
    search_fields = (
        'customer__name', 
        'customer__phone', 
        'customer__customer_code', 
        'note'
    )

    # 4. Tối ưu query (Tránh lỗi N+1 query khi load customer)
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer', 'caller')

    # --- CÁC HÀM LẤY DỮ LIỆU TỪ BẢNG CUSTOMER ---

    @admin.display(description='Khách hàng', ordering='customer__name')
    def get_customer_name(self, obj):
        # Bấm vào tên để sang trang sửa khách hàng
        return format_html(
            '<a href="/admin/customers/customer/{}/change/"><b>{}</b></a>',
            obj.customer.id,
            obj.customer.name
        )

    @admin.display(description='SĐT', ordering='customer__phone')
    def get_customer_phone(self, obj):
        return obj.customer.phone

    @admin.display(description='Fanpage', ordering='customer__fanpage')
    def get_customer_fanpage(self, obj):
        # Hiển thị label (Tên đầy đủ) thay vì key
        return obj.customer.get_fanpage_display()

    @admin.display(description='Dịch vụ quan tâm', ordering='customer__skin_condition')
    def get_customer_service(self, obj):
        return obj.customer.get_skin_condition_display()

    # --- TRANG TRÍ MÀU SẮC CHO TRẠNG THÁI ---
    @admin.display(description='Trạng thái', ordering='status')
    def status_colored(self, obj):
        color = 'black'
        if obj.status == 'BOOKED':
            color = 'green'
        elif obj.status == 'FOLLOW_UP':
            color = 'blue'
        elif obj.status in ['WRONG_NUMBER', 'SPAM']:
            color = 'red'
        elif obj.status == 'NEW':
            color = 'gray'
            
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )

    # Cho phép chỉnh sửa nhanh trạng thái ngay trên danh sách (Tùy chọn)
    # list_editable = ('status',)