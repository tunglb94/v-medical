from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    # 1. Các cột hiển thị danh sách (Thêm Fanpage, Mã KH, Sale...)
    list_display = (
        'customer_code', 
        'name', 
        'phone', 
        'fanpage',          # <--- Mới thêm
        'skin_condition', 
        'source', 
        'assigned_telesale',
        'ranking',
        'created_at'
    )
    
    # 2. Bộ lọc bên phải (Lọc theo Fanpage, Dịch vụ, Nguồn...)
    list_filter = (
        'fanpage',          # <--- Lọc theo Fanpage
        'skin_condition',   # <--- Lọc theo Dịch vụ
        'source', 
        'ranking', 
        'gender',
        'city',
        'assigned_telesale'
    )
    
    # 3. Tìm kiếm (Thêm tìm theo Mã KH)
    search_fields = ('name', 'phone', 'customer_code', 'address')
    
    # 4. Trường chỉ đọc (Ngày tạo không sửa được)
    readonly_fields = ('created_at',)

    # 5. Phân nhóm form nhập liệu cho gọn
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': (
                'customer_code', 
                'name', 
                'phone', 
                'gender', 
                'dob', 
                'address', 
                'city'
            )
        }),
        ('Marketing & Nhu cầu', {
            'fields': (
                'source', 
                'fanpage',          # <--- Input chọn Fanpage ở đây
                'skin_condition'    # <--- Input chọn Dịch vụ ở đây
            )
        }),
        ('Quản lý nội bộ', {
            'fields': (
                'assigned_telesale', 
                'ranking', 
                'note_telesale', 
                'created_at'
            )
        }),
    )