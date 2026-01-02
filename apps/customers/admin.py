from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms
from django.utils import timezone
from datetime import datetime
import csv
import io

# Import thêm các model mới
from .models import Customer, Fanpage, CustomerSource, Service

# --- ĐĂNG KÝ CÁC MODEL CẤU HÌNH ---
@admin.register(Fanpage)
class FanpageAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')
    search_fields = ('name',)
    list_editable = ('status',)

@admin.register(CustomerSource)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')
    search_fields = ('name',)
    list_editable = ('status',)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')
    search_fields = ('name',)
    list_editable = ('status',)

# --- FORM IMPORT ---
class CsvImportForm(forms.Form):
    csv_file = forms.FileField(label="Chọn file CSV")

# --- CUSTOMER ADMIN ---
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'customer_code', 'name', 'phone', 'get_fanpage',
        'get_service', 'get_source', 'assigned_telesale',
        'ranking', 'created_at'
    )
    
    # ForeignKey cần lọc theo ID hoặc dùng autocomplete
    list_filter = (
        'fanpage', 'skin_condition', 'source', 
        'ranking', 'gender', 'city', 'assigned_telesale'
    )
    
    search_fields = ('name', 'phone', 'customer_code', 'address')
    readonly_fields = ('created_at',)
    
    # Dùng autocomplete cho các trường Foreign Key để load nhanh hơn nếu list dài
    autocomplete_fields = ['fanpage', 'source', 'skin_condition', 'assigned_telesale']

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

    # Hiển thị tên thay vì Object ID trong list
    def get_fanpage(self, obj): return obj.fanpage.name if obj.fanpage else '-'
    get_fanpage.short_description = 'Fanpage'
    
    def get_service(self, obj): return obj.skin_condition.name if obj.skin_condition else '-'
    get_service.short_description = 'Dịch vụ'

    def get_source(self, obj): return obj.source.name if obj.source else '-'
    get_source.short_description = 'Nguồn'

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
                        clean_row = {}
                        for k, v in row.items():
                            if k and v:
                                clean_row[k.strip().upper()] = v.strip()
                        
                        # 1. XỬ LÝ SĐT
                        phone_raw = clean_row.get('SĐT') or clean_row.get('SDT') or clean_row.get('PHONE')
                        if not phone_raw: continue
                        phone = ''.join(filter(str.isdigit, phone_raw))
                        if len(phone) < 8: continue
                        if not phone.startswith('0'): phone = '0' + phone

                        # 2. XỬ LÝ CÁC TRƯỜNG CƠ BẢN
                        name = clean_row.get('TÊN KHÁCH HÀNG') or clean_row.get('TÊN') or clean_row.get('HỌ TÊN') or "Khách hàng"
                        address_raw = clean_row.get('VỊ TRÍ') or clean_row.get('ĐỊA CHỈ') or clean_row.get('TỈNH THÀNH') or ''

                        # 3. XỬ LÝ NGUỒN (Tự động tìm trong DB hoặc tạo mới)
                        source_str = clean_row.get('NGUỒN') or clean_row.get('SOURCE')
                        source_obj = None
                        if source_str:
                            # get_or_create trả về (object, created)
                            source_obj, _ = CustomerSource.objects.get_or_create(name=source_str.strip())

                        # 4. XỬ LÝ FANPAGE (Tự động tìm hoặc tạo mới)
                        fanpage_str = clean_row.get('FANPAGE') or clean_row.get('PAGE')
                        fanpage_obj = None
                        if fanpage_str:
                            fanpage_obj, _ = Fanpage.objects.get_or_create(name=fanpage_str.strip())

                        # 5. XỬ LÝ DỊCH VỤ (Tự động tìm hoặc tạo mới)
                        service_str = clean_row.get('DV QUAN TÂM') or clean_row.get('SERVICE') or clean_row.get('SKIN')
                        service_obj = None
                        if service_str:
                            service_obj, _ = Service.objects.get_or_create(name=service_str.strip())

                        # 6. XỬ LÝ NGÀY TẠO
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

                        # 7. GỘP GHI CHÚ
                        notes = []
                        if clean_row.get('GHI CHÚ'): notes.append(clean_row['GHI CHÚ'])
                        if clean_row.get('LINK FB'): notes.append(f"FB: {clean_row['LINK FB']}")
                        if clean_row.get('SALE'): notes.append(f"Sale cũ: {clean_row['SALE']}")
                        full_note = " | ".join(notes)

                        # 8. LƯU DATA (Gán Object thay vì String)
                        obj, created = Customer.objects.get_or_create(
                            phone=phone,
                            defaults={
                                'name': name,
                                'city': address_raw,     
                                'address': address_raw,
                                'note_telesale': full_note,
                                'source': source_obj,       # <--- Gán Object
                                'fanpage': fanpage_obj,     # <--- Gán Object
                                'skin_condition': service_obj, # <--- Gán Object
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