from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms
from django.utils import timezone
from datetime import datetime
import csv
import io

from .models import Customer, Fanpage

# Form để upload file CSV
class CsvImportForm(forms.Form):
    csv_file = forms.FileField(label="Chọn file CSV")

# --- ĐĂNG KÝ MODEL FANPAGE (Để sửa lỗi Not Found) ---
@admin.register(Fanpage)
class FanpageAdmin(admin.ModelAdmin):
    # Hiển thị các cột: Mã, Tên và Marketer phụ trách
    list_display = ('code', 'name', 'assigned_marketer')
    # Cho phép sửa nhanh tên và người phụ trách ngay tại danh sách
    list_editable = ('name', 'assigned_marketer')
    search_fields = ('name', 'code')

# --- ĐĂNG KÝ MODEL CUSTOMER VỚI CHỨC NĂNG IMPORT CSV ---
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    # --- CẤU HÌNH GIAO DIỆN ---
    list_display = (
        'customer_code', 'name', 'phone', 'fanpage',
        'skin_condition', 'source', 'assigned_telesale',
        'ranking', 'created_at'
    )
    list_filter = (
        'fanpage', 'skin_condition', 'source', 
        'ranking', 'gender', 'city', 'assigned_telesale'
    )
    search_fields = ('name', 'phone', 'customer_code', 'address')
    readonly_fields = ('created_at',)
    
    # [CẬP NHẬT] Thêm trường fanpages (ManyToMany) vào giao diện
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('customer_code', 'name', 'phone', 'gender', 'dob', 'address', 'city')
        }),
        ('Marketing & Nhu cầu', {
            'fields': ('source', 'fanpages', 'fanpage', 'skin_condition')
        }),
        ('Quản lý nội bộ', {
            'fields': ('assigned_telesale', 'ranking', 'note_telesale', 'created_at')
        }),
    )
    
    # Cho phép chọn nhiều Fanpage trong giao diện admin
    filter_horizontal = ('fanpages',)

    # --- PHẦN IMPORT CSV ---
    change_list_template = "admin/customers/customer/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv_view, name='import-csv'),
        ]
        return my_urls + urls

    def import_csv_view(self, request):
        if request.method == "POST":
            form = CsvImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = request.FILES["csv_file"]
                
                if not csv_file.name.endswith('.csv'):
                    messages.error(request, 'Vui lòng chỉ tải lên file .csv')
                    return redirect("..")

                try:
                    data_set = csv_file.read().decode('utf-8-sig')
                    io_string = io.StringIO(data_set)
                    
                    first_line = io_string.readline()
                    io_string.seek(0)
                    delimiter = ';' if ';' in first_line else ','
                    
                    reader = csv.DictReader(io_string, delimiter=delimiter)
                    
                    count_created = 0
                    count_exist = 0
                    
                    for row in reader:
                        clean_row = {k.strip().upper(): v.strip() for k, v in row.items() if k and v}
                        
                        # 1. Xử lý SĐT
                        phone_raw = clean_row.get('SĐT') or clean_row.get('SDT') or clean_row.get('PHONE')
                        if not phone_raw: continue
                        phone = ''.join(filter(str.isdigit, phone_raw))
                        if len(phone) < 8: continue
                        if not phone.startswith('0'): phone = '0' + phone

                        # 2. Xử lý Tên
                        name = clean_row.get('TÊN KHÁCH HÀNG') or clean_row.get('TÊN') or "Khách hàng"
                        
                        # 3. Xử lý Địa chỉ
                        address_raw = clean_row.get('ĐỊA CHỈ') or clean_row.get('VỊ TRÍ') or ''

                        # 4. Xử lý Nguồn
                        source_raw = clean_row.get('NGUỒN') or 'OTHER'
                        source_upper = source_raw.upper()
                        if 'FACEBOOK' in source_upper: source_code = 'FACEBOOK'
                        elif 'GOOGLE' in source_upper: source_code = 'GOOGLE'
                        else: source_code = 'FACEBOOK'

                        # 5. Xử lý Ngày
                        created_at = timezone.now()
                        date_str = clean_row.get('NGÀY') or clean_row.get('DATE')
                        if date_str:
                            try:
                                if '/' in date_str: dt = datetime.strptime(date_str.split()[0], '%d/%m/%Y')
                                elif '-' in date_str: dt = datetime.strptime(date_str.split()[0], '%Y-%m-%d')
                                else: dt = timezone.now()
                                created_at = timezone.make_aware(datetime.combine(dt.date(), timezone.now().time()))
                            except: pass

                        # 6. Ghi chú
                        notes = [f"{k}: {v}" for k, v in clean_row.items() if v]
                        full_note = " | ".join(notes)

                        # 7. Lưu
                        obj, created = Customer.objects.get_or_create(
                            phone=phone,
                            defaults={
                                'name': name,
                                'city': address_raw,     
                                'address': address_raw,
                                'note_telesale': full_note,
                                'source': source_code,
                                'created_at': created_at
                            }
                        )
                        if created: count_created += 1
                        else: count_exist += 1

                    self.message_user(request, f"Kết quả: Thêm mới {count_created}, Tồn tại {count_exist}.", level=messages.SUCCESS)
                    return redirect("..")
                    
                except Exception as e:
                    self.message_user(request, f"Lỗi: {str(e)}", level=messages.ERROR)

        form = CsvImportForm()
        return render(request, "admin/customers/customer/import_form.html", {"form": form})