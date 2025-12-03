from django.core.management.base import BaseCommand
from apps.resources.models import ProductDocument

class Command(BaseCommand):
    help = 'Tự động tạo dữ liệu tài liệu sản phẩm chuẩn y khoa'

    def handle(self, *args, **kwargs):
        data = [
            {
                "title": "Trẻ hoá da bằng Ultherapy Prime",
                "category": "MACHINE",
                "image_url": "https://lasercare.vn/wp-content/uploads/2020/09/Ultherapy-1.jpg",
                "content": """
1. CƠ CHẾ HOẠT ĐỘNG (MFU):
- Sử dụng sóng siêu âm hội tụ vi điểm (Micro Focused Ultrasound).
- Tác động chính xác vào lớp cân cơ nông (SMAS) ở độ sâu 4.5mm - đây là lớp cơ được can thiệp trong phẫu thuật căng da mặt.
- Nhiệt độ đạt mức lý tưởng 60-70 độ C, gây biến tính collagen già cỗi và kích thích tăng sinh collagen, elastin mới mạnh mẽ.

2. CÔNG NGHỆ PRIME MỚI NHẤT:
- Màn hình See & Treat: Cho phép bác sĩ quan sát trực tiếp lớp cơ dưới da theo thời gian thực, đảm bảo năng lượng đi đúng đích, an toàn tuyệt đối, không gây bỏng.
- Tốc độ xử lý nhanh hơn 20% so với thế hệ cũ.

3. HIỆU QUẢ LÂM SÀNG:
- Nâng cơ, thon gọn hàm, xóa nọng cằm.
- Nâng cung mày, giảm sụp mí.
- Hiệu quả thấy ngay 10-20% sau khi làm, đạt đỉnh sau 3-6 tháng và duy trì 1-2 năm.
"""
            },
            {
                "title": "Trẻ hoá da toàn diện Thermage FLX",
                "category": "MACHINE",
                "image_url": "https://vmedical.com.vn/wp-content/uploads/2023/10/Thermage-FLX.jpg", 
                "content": """
1. NGUYÊN LÝ CÔNG NGHỆ (RF Đơn Cực):
- Sử dụng sóng vô tuyến đơn cực (Capacitive Monopolar Radiofrequency).
- Tác động nhiệt khối (Bulk Heating) lan tỏa đều từ lớp biểu bì xuống trung bì và hạ bì.
- Giúp co thắt các bó sợi collagen ngay lập tức, làm da săn chắc.

2. ĐIỂM KHÁC BIỆT CỦA FLX 4.0:
- Đầu Tip 4.0 cm2: Diện tích tiếp xúc lớn hơn, rút ngắn 25% thời gian điều trị.
- Thuật toán AccuREP: Tự động đo trở kháng của da trước mỗi xung bắn để điều chỉnh năng lượng phù hợp nhất cho từng vùng da (trán, má, cằm).
- Chế độ rung đa chiều + Phun lạnh Cryogen: Giảm cảm giác đau tối đa, tạo sự thoải mái.

3. CHỈ ĐỊNH:
- Da mặt chùng nhão, nhiều nếp nhăn li ti quanh mắt, miệng.
- Bàn tay nhăn nheo, da cổ chảy xệ.
"""
            },
            {
                "title": "Giảm béo quang đông CoolTech Define",
                "category": "SERVICE",
                "image_url": "https://theaestheticsolutions.com/wp-content/uploads/2020/06/cooltech-define.jpg",
                "content": """
1. CƠ CHẾ KHOA HỌC (Cryolipolysis):
- Tế bào mỡ cực kỳ nhạy cảm với nhiệt độ lạnh (trong khi da, cơ, mạch máu thì không).
- Máy Cooltech sử dụng nhiệt độ lạnh sâu (-8 độ C đến -10 độ C) để "đóng băng" các tế bào mỡ thừa.
- Tế bào mỡ bị kết tinh sẽ chết theo chương trình sinh học (Apoptosis).

2. QUÁ TRÌNH ĐÀO THẢI:
- Sau trị liệu, hệ bạch huyết (thực bào) sẽ dọn dẹp các xác tế bào mỡ và đào thải tự nhiên qua đường bài tiết.
- Quá trình này diễn ra từ từ trong 4-8 tuần, giúp cơ thể không bị sốc.

3. HIỆU QUẢ:
- Giảm 25-30% lượng mỡ thừa tại vùng điều trị chỉ sau 1 lần (60-70 phút).
- An toàn, không xâm lấn, không cần nghỉ dưỡng.
"""
            },
            {
                "title": "Nâng cơ siêu tốc Lifting MPT 5.0",
                "category": "MACHINE",
                "image_url": "https://image.made-in-china.com/202f0j00sQGlEaWdCokP/Ultraformer-MPT-Hifu-Machine-High-Intensity-Focused-Ultrasound-Face-Lifting-Skin-Tightening.jpg",
                "content": """
1. CÔNG NGHỆ MICRO-PULSED (MPT):
- Đây là thế hệ nâng cấp của Ultraformer III.
- Thay vì bắn từng điểm nhiệt rời rạc, chế độ MPT bắn ra 417 điểm nhiệt liên tiếp tạo thành một đường thẳng (Linear) dày đặc năng lượng.
- Giúp tăng hiệu quả kích thích collagen lên gấp 2.5 lần.

2. ƯU ĐIỂM VƯỢT TRỘI:
- Không đau: Do tốc độ bắn siêu nhanh và năng lượng được chia nhỏ mịn.
- Tác động kép: Vừa nâng cơ (Lifting) vừa làm tan mỡ mặt (Contouring) nhờ các đầu típ chuyên dụng.
- Thời gian làm chỉ mất 15-20 phút cho toàn mặt.

3. ỨNG DỤNG:
- Thon gọn mặt V-line.
- Giảm mỡ má bầu, nọng cằm nhẹ.
- Làm sáng và căng bóng da tức thì (Booster).
"""
            },
            {
                "title": "Laser trị nám Revlite SI Cynosure",
                "category": "MACHINE",
                "image_url": "https://cynosure.com.vn/wp-content/uploads/2021/05/Revlite-SI.png",
                "content": """
1. CÔNG NGHỆ PTP ĐỘC QUYỀN:
- Revlite SI sử dụng công nghệ PTP (PhotoAcoustic Technology Pulse) - Xung quang âm.
- Phát ra 2 xung cực ngắn liên tiếp nhau, tạo ra hiệu ứng rung lắc mạnh mẽ để phá vỡ hạt sắc tố melanin thành các mảnh nhỏ li ti.

2. CƠ CHẾ ĐIỀU TRỊ:
- Các mảnh sắc tố nhỏ sau khi bị phá vỡ sẽ được cơ thể hấp thụ và đào thải ra ngoài.
- Không gây tổn thương nhiệt: Không làm bong tróc, không đóng vảy, không cần nghỉ dưỡng (với chế độ Toning).

3. CHỈ ĐỊNH ĐIỀU TRỊ:
- Nám mảng, nám chân sâu, tàn nhang, đồi mồi.
- Xóa xăm (xăm đen, xanh, đỏ).
- Trẻ hóa da (Laser Toning): Se khít lỗ chân lông, làm đều màu da, sáng da.
"""
            }
        ]

        for item in data:
            doc, created = ProductDocument.objects.get_or_create(
                title=item['title'],
                defaults={
                    'category': item['category'],
                    'image_url': item['image_url'],
                    'content': item['content']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Đã tạo: {doc.title}'))
            else:
                self.stdout.write(self.style.WARNING(f'Đã tồn tại: {doc.title}'))