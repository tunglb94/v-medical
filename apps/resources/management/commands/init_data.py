from django.core.management.base import BaseCommand
from apps.resources.models import ProductDocument

class Command(BaseCommand):
    help = 'Khởi tạo danh mục tài liệu (Trỏ tới file HTML)'

    def handle(self, *args, **kwargs):
        ProductDocument.objects.all().delete()
        
        data = [
            {
                "title": "Ultherapy Prime - Giáo trình chuyên sâu",
                "category": "MACHINE",
                "image_url": "https://vmedical.com.vn/wp-content/uploads/2023/10/Ultherapy-Prime.jpg",
                "template_name": "ultherapy.html", # Tên file HTML bạn tạo ở Bước 1
                "desc": "Tài liệu chuẩn y khoa về công nghệ nâng cơ MFU-V."
            },
            {
                "title": "Thermage FLX - Giáo trình chuyên sâu",
                "category": "MACHINE",
                "image_url": "https://vmedical.com.vn/wp-content/uploads/2023/10/Thermage-FLX.jpg",
                "template_name": "thermage.html",
                "desc": "Phân tích công nghệ RF đơn cực thế hệ 4.0."
            },
            # ... Thêm tương tự cho Cooltech, MPT, Revlite ...
        ]

        for item in data:
            ProductDocument.objects.create(
                title=item['title'],
                category=item['category'],
                image_url=item['image_url'],
                template_name=item['template_name'],
                short_description=item['desc']
            )
            self.stdout.write(self.style.SUCCESS(f'Đã tạo: {item["title"]}'))