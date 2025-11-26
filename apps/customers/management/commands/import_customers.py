import csv
import os
from datetime import datetime
from django.utils import timezone
from django.core.management.base import BaseCommand
from apps.customers.models import Customer

class Command(BaseCommand):
    help = 'Import customer data from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The path to the CSV file')

    def handle(self, *args, **kwargs):
        csv_file_path = kwargs['csv_file']

        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {csv_file_path}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Đang đọc file: {csv_file_path}...'))

        count_created = 0
        count_exist = 0
        
        with open(csv_file_path, 'r', encoding='utf-8-sig') as file:
            # 1. Tự động nhận diện dấu phân cách
            try:
                first_line = file.readline()
                file.seek(0)
                delimiter = ';' if ';' in first_line else ','
            except:
                delimiter = ','
            
            reader = csv.DictReader(file, delimiter=delimiter)

            for i, row in enumerate(reader):
                # Làm sạch data
                clean_row = {}
                for k, v in row.items():
                    if k and v:
                        clean_row[k.strip().upper()] = v.strip()
                
                try:
                    # 2. Tìm cột SĐT
                    phone = clean_row.get('SĐT') or clean_row.get('SDT') or clean_row.get('PHONE')
                    if not phone or len(phone) < 8: continue

                    # 3. Tìm cột Tên
                    name = clean_row.get('TÊN KHÁCH HÀNG') or clean_row.get('TÊN FB') or clean_row.get('HỌ TÊN') or clean_row.get('NAME') or "Khách hàng"

                    # 4. Tìm cột Địa chỉ
                    address_raw = clean_row.get('VỊ TRÍ') or clean_row.get('ĐỊA CHỈ') or clean_row.get('TỈNH THÀNH') or ''

                    # 5. XỬ LÝ NGÀY TẠO (MỚI THÊM) ---
                    created_at = timezone.now() # Mặc định là hôm nay
                    date_str = clean_row.get('NGÀY') or clean_row.get('DATE') or clean_row.get('CREATED_AT')
                    
                    if date_str:
                        try:
                            # Thử parse các định dạng ngày phổ biến
                            if '/' in date_str:
                                # Dạng 26/11/2025
                                dt = datetime.strptime(date_str, '%d/%m/%Y')
                            elif '-' in date_str:
                                # Dạng 2025-11-26
                                dt = datetime.strptime(date_str, '%Y-%m-%d')
                            else:
                                dt = timezone.now()

                            # Gán giờ hiện tại để tránh tất cả đều là 00:00:00
                            current_time = timezone.now().time()
                            created_at = datetime.combine(dt.date(), current_time)
                            created_at = timezone.make_aware(created_at)
                        except Exception as e:
                            # Nếu lỗi ngày tháng thì bỏ qua, lấy ngày hiện tại
                            pass
                    # --------------------------------

                    # 6. Gộp ghi chú
                    notes = []
                    if clean_row.get('LINK FB'): notes.append(f"FB: {clean_row['LINK FB']}")
                    if clean_row.get('DV QUAN TÂM'): notes.append(f"Quan tâm: {clean_row['DV QUAN TÂM']}")
                    if clean_row.get('TRẠNG THÁI'): notes.append(f"TT cũ: {clean_row['TRẠNG THÁI']}")
                    if clean_row.get('TELESALE'): notes.append(f"Sale cũ: {clean_row['TELESALE']}")
                    
                    for key in clean_row:
                        if 'GỌI LẦN' in key:
                            notes.append(f"{key}: {clean_row[key]}")

                    full_note = " | ".join(notes)

                    # 7. Lưu vào DB
                    # Dùng get_or_create nhưng cập nhật luôn created_at nếu tạo mới
                    obj, created = Customer.objects.get_or_create(
                        phone=phone,
                        defaults={
                            'name': name,
                            'city': address_raw,     
                            'address': address_raw,
                            'note_telesale': full_note,
                            'source': 'FACEBOOK',
                            'created_at': created_at # <--- Lưu ngày cũ vào đây
                        }
                    )

                    if created:
                        count_created += 1
                    else:
                        count_exist += 1
                
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Lỗi dòng {i+2}: {e}"))

        self.stdout.write(self.style.SUCCESS(f'NHẬP LIỆU HOÀN TẤT!'))
        self.stdout.write(self.style.SUCCESS(f'- Mới thêm (đúng ngày): {count_created}'))
        self.stdout.write(self.style.SUCCESS(f'- Đã có (Bỏ qua): {count_exist}'))