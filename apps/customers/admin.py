from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms
from django.utils import timezone
from datetime import datetime
import csv
import io

from .models import Customer

# Form để upload file
class CsvImportForm(forms.Form):
    csv_file = forms.FileField(label="Chọn file CSV")

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    # --- CẤU HÌNH GIAO DIỆN CŨ (GIỮ NGUYÊN) ---
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
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('customer_code', 'name', 'phone', 'gender', 'dob', 'address', 'city')
        }),
        ('Marketing & Nhu cầu', {
            'fields': ('source', 'fanpage', 'skin_condition')
        }),
        ('Quản lý nội bộ', {
            'fields': ('assigned_telesale', 'ranking', 'note_telesale', 'created_at')
        }),
    )

    # --- PHẦN MỚI THÊM: CUSTOM URL VÀ VIEW IMPORT ---
    
    # Chỉ định template chứa nút bấm (File bạn vừa tạo ở Bước 2)
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
                    # Đọc file CSV
                    data_set = csv_file.read().decode('utf-8-sig')
                    io_string = io.StringIO(data_set)
                    
                    # Tự động nhận diện dấu phân cách (; hoặc ,)
                    first_line = io_string.readline()
                    io_string.seek(0)
                    delimiter = ';' if ';' in first_line else ','
                    
                    reader = csv.DictReader(io_string, delimiter=delimiter)
                    
                    count_created = 0
                    count_exist = 0
                    
                    for row in reader:
                        # Làm sạch tên cột
                        clean_row = {}
                        for k, v in row.items():
                            if k and v:
                                clean_row[k.strip().upper()] = v.strip()
                        
                        # 1. XỬ LÝ SĐT
                        phone_raw = clean_row.get('SĐT') or clean_row.get('SDT') or clean_row.get('PHONE') or clean_row.get('PHONENUMBER')
                        if not phone_raw: continue
                        phone = ''.join(filter(str.isdigit, phone_raw))
                        if len(phone) < 8: continue
                        if not phone.startswith('0'): phone = '0' + phone

                        # 2. XỬ LÝ TÊN
                        name = clean_row.get('TÊN KHÁCH HÀNG') or clean_row.get('TÊN') or clean_row.get('HỌ TÊN') or clean_row.get('NAME') or "Khách hàng"
                        
                        # 3. XỬ LÝ ĐỊA CHỈ
                        address_raw = clean_row.get('VỊ TRÍ') or clean_row.get('ĐỊA CHỈ') or clean_row.get('TỈNH THÀNH') or clean_row.get('ADDRESS') or ''

                        # 4. XỬ LÝ NGUỒN (Tự động map)
                        source_raw = clean_row.get('NGUỒN') or clean_row.get('SOURCE') or 'OTHER'
                        source_code = 'OTHER'
                        source_upper = source_raw.upper()
                        if 'FACEBOOK' in source_upper: source_code = 'FACEBOOK'
                        elif 'GOOGLE' in source_upper: source_code = 'GOOGLE'
                        elif 'TIKTOK' in source_upper: source_code = 'TIKTOK'
                        elif 'SEO' in source_upper or 'WEB' in source_upper: source_code = 'SEO'
                        elif 'REFERRAL' in source_upper: source_code = 'REFERRAL'
                        else: source_code = 'FACEBOOK'

                        # 5. XỬ LÝ NGÀY TẠO
                        created_at = timezone.now()
                        date_str = clean_row.get('NGÀY') or clean_row.get('DATE') or clean_row.get('CREATED_AT')
                        if date_str:
                            try:
                                if '/' in date_str: dt = datetime.strptime(date_str.split()[0], '%d/%m/%Y')
                                elif '-' in date_str: dt = datetime.strptime(date_str.split()[0], '%Y-%m-%d')
                                else: dt = timezone.now()
                                current_time = timezone.now().time()
                                created_at = timezone.make_aware(datetime.combine(dt.date(), current_time))
                            except: pass

                        # 6. GỘP GHI CHÚ
                        notes = []
                        if clean_row.get('GHI CHÚ'): notes.append(clean_row['GHI CHÚ'])
                        if clean_row.get('LINK FB'): notes.append(f"FB: {clean_row['LINK FB']}")
                        if clean_row.get('DV QUAN TÂM'): notes.append(f"Quan tâm: {clean_row['DV QUAN TÂM']}")
                        if clean_row.get('SALE'): notes.append(f"Sale cũ: {clean_row['SALE']}")
                        full_note = " | ".join(notes)

                        # 7. LƯU DATA
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

                    self.message_user(request, f"Kết quả Import: Thêm mới {count_created}, Đã tồn tại {count_exist}.", level=messages.SUCCESS)
                    return redirect("..")
                    
                except Exception as e:
                    self.message_user(request, f"Lỗi file: {str(e)}", level=messages.ERROR)

        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "admin/customers/customer/import_form.html", payload
        )