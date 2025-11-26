import csv
import os
from django.core.management.base import BaseCommand
from apps.customers.models import Customer
from django.utils.dateparse import parse_date
import datetime

class Command(BaseCommand):
    help = 'Import customer data from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The path to the CSV file')

    def handle(self, *args, **kwargs):
        csv_file_path = kwargs['csv_file']

        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {csv_file_path}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Starting import from {csv_file_path}...'))

        count_created = 0
        count_exist = 0
        
        # Ánh xạ nguồn dữ liệu (Mặc định là Khác hoặc Facebook tùy bạn chọn)
        # Dựa trên file của bạn có cột "Link FB", tôi sẽ để mặc định là FACEBOOK
        
        with open(csv_file_path, 'r', encoding='utf-8-sig') as file:
            # Sử dụng DictReader để đọc theo tên cột
            reader = csv.DictReader(file)
            
            for row in reader:
                try:
                    # 1. Lấy Số điện thoại (Key này phải khớp với header trong CSV của bạn)
                    phone = row.get('SĐT', '').strip()
                    
                    # Bỏ qua nếu không có SĐT
                    if not phone:
                        continue

                    # 2. Lấy Tên
                    name = row.get('Tên Facebook', 'Khách hàng').strip()
                    if not name:
                        name = "Khách hàng (No Name)"

                    # 3. Lấy Tỉnh thành
                    city = row.get('Địa chỉ', '').strip()

                    # 4. Xử lý Ghi chú tổng hợp
                    # Gộp nhiều cột vào ghi chú để telesale đọc lại lịch sử cũ
                    raw_notes = []
                    if row.get('Link FB'): raw_notes.append(f"FB: {row['Link FB']}")
                    if row.get('Trạng Thái'): raw_notes.append(f"Trạng thái cũ: {row['Trạng Thái']}")
                    if row.get('TELE'): raw_notes.append(f"Sale cũ: {row['TELE']}")
                    
                    # Gộp lịch sử gọi
                    call_history = []
                    if row.get('Gọi lần 1 '): call_history.append(f"L1: {row.get('Gọi lần 1 ')}")
                    if row.get('Gọi lần 2 '): call_history.append(f"L2: {row.get('Gọi lần 2 ')}")
                    
                    full_note = " | ".join(raw_notes)
                    if call_history:
                        full_note += "\n--- Lịch sử gọi cũ ---\n" + "\n".join(call_history)

                    # 5. Thực hiện lưu vào Database
                    # Dùng get_or_create để tránh trùng lặp SĐT
                    customer, created = Customer.objects.get_or_create(
                        phone=phone,
                        defaults={
                            'name': name,
                            'city': city,
                            'note_telesale': full_note,
                            'source': 'FACEBOOK', # Mặc định nguồn
                            'address': row.get('Địa chỉ', '') # Lưu địa chỉ vào đây luôn nếu cần
                        }
                    )

                    if created:
                        count_created += 1
                        self.stdout.write(f"Created: {name} - {phone}")
                    else:
                        count_exist += 1
                        # Nếu muốn cập nhật data cũ vào data mới thì viết code update ở đây
                        # Ví dụ: customer.note_telesale += full_note; customer.save()
                
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Lỗi dòng {row}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f'Import hoàn tất!'))
        self.stdout.write(self.style.SUCCESS(f'- Thêm mới: {count_created}'))
        self.stdout.write(self.style.SUCCESS(f'- Đã tồn tại (Bỏ qua): {count_exist}'))