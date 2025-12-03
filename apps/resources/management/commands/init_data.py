from django.core.management.base import BaseCommand
from apps.resources.models import ProductDocument

class Command(BaseCommand):
    help = 'Khởi tạo dữ liệu tài liệu (Kết nối với file HTML)'

    def handle(self, *args, **kwargs):
        # Xóa dữ liệu cũ
        ProductDocument.objects.all().delete()
        self.stdout.write(self.style.WARNING('Đang reset dữ liệu...'))

        data = [
            {
                "title": "Ultherapy Prime - Giáo trình đào tạo chuyên sâu",
                "category": "MACHINE",
                "image_url": "https://vmedical.com.vn/wp-content/uploads/2023/10/Ultherapy-Prime.jpg",
                "template_name": "ultherapy.html", # Tên file HTML bạn đã tạo
                "desc": "Tài liệu chuẩn y khoa về công nghệ nâng cơ MFU-V, phác đồ điều trị và xử lý biến chứng."
            },
            {
                "title": "Thermage FLX - Trẻ hóa da đa tầng",
                "category": "MACHINE",
                "image_url": "https://vmedical.com.vn/wp-content/uploads/2023/10/Thermage-FLX.jpg",
                "template_name": "thermage.html",
                "desc": "Phân tích công nghệ RF đơn cực thế hệ 4.0, kỹ thuật Vector và các loại đầu Tip."
            },
            {
                "title": "CoolTech Define - Giảm béo quang đông",
                "category": "SERVICE",
                "image_url": "https://theaestheticsolutions.com/wp-content/uploads/2020/06/cooltech-define.jpg",
                "template_name": "cooltech.html",
                "desc": "Cơ chế hủy mỡ nhiệt lạnh Cryolipolysis và quá trình đào thải mỡ tự nhiên."
            },
            {
                "title": "Ultraformer MPT - Nâng cơ siêu tốc",
                "category": "MACHINE",
                "image_url": "https://image.made-in-china.com/202f0j00sQGlEaWdCokP/Ultraformer-MPT-Hifu-Machine-High-Intensity-Focused-Ultrasound-Face-Lifting-Skin-Tightening.jpg",
                "template_name": "mpt.html",
                "desc": "Công nghệ Micro-Pulsed, chế độ Linear và ứng dụng đầu típ Ultra Booster."
            },
            {
                "title": "Revlite SI - Laser trị nám & sắc tố",
                "category": "MACHINE",
                "image_url": "https://cynosure.com.vn/wp-content/uploads/2021/05/Revlite-SI.png",
                "template_name": "revlite.html",
                "desc": "Công nghệ xung quang âm PTP, phác đồ trị nám Melasma và xóa xăm không sẹo."
            }
        ]

        for item in data:
            ProductDocument.objects.create(
                title=item['title'],
                category=item['category'],
                image_url=item['image_url'],
                template_name=item['template_name'],
                short_description=item['desc']
            )
            self.stdout.write(self.style.SUCCESS(f'Đã tạo kết nối: {item["title"]}'))