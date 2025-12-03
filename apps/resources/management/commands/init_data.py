from django.core.management.base import BaseCommand
from apps.resources.models import ProductDocument

class Command(BaseCommand):
    help = 'Tự động tạo dữ liệu tài liệu sản phẩm chuẩn y khoa (Professional Version)'

    def handle(self, *args, **kwargs):
        # Xóa dữ liệu cũ để tránh trùng lặp
        ProductDocument.objects.all().delete()
        self.stdout.write(self.style.WARNING('Đã xóa dữ liệu cũ để cập nhật bản chuyên sâu...'))

        data = [
            {
                "title": "Ultherapy Prime - Tiêu chuẩn vàng nâng cơ không xâm lấn",
                "category": "MACHINE",
                "image_url": "https://vmedical.com.vn/wp-content/uploads/2023/10/Ultherapy-Prime.jpg",
                "content": """
<div class="alert alert-info">
    <i class="bi bi-info-circle-fill me-2"></i><strong>Tóm tắt công nghệ:</strong> Ultherapy là công nghệ duy nhất được FDA Hoa Kỳ chứng nhận có khả năng nâng cơ (Lifting) tương đương phẫu thuật căng da mặt nhờ tác động chính xác vào lớp cân cơ nông (SMAS).
</div>

<h3>1. CƠ CHẾ HOẠT ĐỘNG (MFU-V)</h3>
<p>Ultherapy sử dụng sóng siêu âm hội tụ vi điểm (Micro Focused Ultrasound) kết hợp hình ảnh trực quan (Visualization). Cơ chế tác động dựa trên 3 yếu tố:</p>
<ul>
    <li><strong>Độ sâu chính xác:</strong> Năng lượng hội tụ tại 3 độ sâu: 
        <ul>
            <li><strong>4.5mm (Lớp SMAS):</strong> Lớp cân cơ nông - đích đến của phẫu thuật căng da. Nhiệt độ làm đông vón các điểm nhiệt (TCPs), gây co rút lớp cơ tức thì -> Hiệu quả nâng cơ.</li>
            <li><strong>3.0mm (Hạ bì sâu):</strong> Kích thích tăng sinh collagen cấu trúc.</li>
            <li><strong>1.5mm (Hạ bì nông):</strong> Xóa nhăn bề mặt, làm mịn da.</li>
        </ul>
    </li>
    <li><strong>Nhiệt độ tối ưu:</strong> Đạt mức <strong>60-70°C</strong>. Đây là "ngưỡng cửa sổ" khởi động quá trình tân tạo Collagen (Neocollagenesis) mạnh mẽ nhất mà không gây hoại tử mô xung quanh.</li>
    <li><strong>Chính xác từng điểm:</strong> Tạo ra hàng ngàn điểm nhiệt đông vón (TCP) có kích thước đồng nhất, khoảng cách đều nhau.</li>
</ul>

<h3>2. CÔNG NGHỆ PRIME 2024 CÓ GÌ MỚI?</h3>
<table class="table table-bordered table-sm">
    <thead class="table-light">
        <tr><th>Tính năng</th><th>Lợi ích lâm sàng</th></tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>Màn hình See & Treat (DeepSEE)</strong></td>
            <td>Cho phép bác sĩ quan sát lớp da thực tế (biểu bì, trung bì, cơ, xương) theo thời gian thực. Giúp tránh bắn vào xương (gây đau buốt) hoặc mạch máu lớn.</td>
        </tr>
        <tr>
            <td><strong>Tốc độ xử lý nhanh hơn 20%</strong></td>
            <td>Rút ngắn thời gian điều trị toàn mặt chỉ còn 45-60 phút.</td>
        </tr>
        <tr>
            <td><strong>Giao diện trực quan</strong></td>
            <td>Hiển thị sơ đồ điều trị (Protocol) chuẩn hóa ngay trên màn hình.</td>
        </tr>
    </tbody>
</table>

<h3>3. CHỈ ĐỊNH ĐIỀU TRỊ</h3>
<ul>
    <li><strong>Vùng mặt:</strong> Nâng cung mày sa trễ, giảm sụp mí, làm rõ đường viền hàm (Jawline), xóa nọng cằm.</li>
    <li><strong>Vùng cổ & ngực:</strong> Cải thiện nếp nhăn vùng cổ và vùng ngực trên (Décolletage).</li>
    <li><strong>Đối tượng:</strong> Nam/Nữ từ 30 tuổi, da chùng nhão mức độ trung bình (Mild to Moderate).</li>
</ul>

<h3>4. PHÁC ĐỒ & HIỆU QUẢ</h3>
<ul>
    <li><strong>Liệu trình:</strong> Chỉ cần <strong>1 lần duy nhất</strong>.</li>
    <li><strong>Kết quả:</strong> 
        <ul>
            <li>Ngay sau làm: Cải thiện 10-20% do co rút nhiệt.</li>
            <li>Sau 3-6 tháng: Kết quả đạt đỉnh do collagen mới được hình thành.</li>
            <li>Duy trì: 1-2 năm tùy cơ địa.</li>
        </ul>
    </li>
    <li><strong>Chăm sóc sau điều trị:</strong> Không cần nghỉ dưỡng. Có thể trang điểm ngay. Hạn chế xông hơi, massage mặt trong 2 tuần đầu.</li>
</ul>
"""
            },
            {
                "title": "Thermage FLX - Trẻ hóa da đa tầng & Xóa nhăn",
                "category": "MACHINE",
                "image_url": "https://vmedical.com.vn/wp-content/uploads/2023/10/Thermage-FLX.jpg",
                "content": """
<h3>1. NGUYÊN LÝ CÔNG NGHỆ (RF Đơn Cực)</h3>
<p>Thermage FLX sử dụng sóng vô tuyến đơn cực (Capacitive Monopolar Radiofrequency) với tần số 6.78 MHz. Khác với Ultherapy (hội tụ điểm), Thermage tác động theo cơ chế <strong>Nhiệt khối (Bulk Heating)</strong>.</p>
<ul>
    <li>Năng lượng RF đi từ bề mặt da xuống sâu lớp trung bì và mỡ dưới da.</li>
    <li>Tạo ra cột nhiệt đồng nhất 55-60°C làm biến tính các sợi collagen già cỗi (co lại ngay lập tức) và kích thích nguyên bào sợi sản sinh collagen mới.</li>
    <li><strong>Cơ chế làm lạnh (Cryogen):</strong> Đầu tip phun khí lạnh Cryogen liên tục (trước - trong - sau xung bắn) giúp bảo vệ lớp thượng bì hoàn toàn, không gây bỏng, tạo cảm giác dễ chịu.</li>
</ul>

<h3>2. GIẢI MÃ CÔNG NGHỆ FLX 4.0</h3>
<p>FLX là viết tắt của 3 cải tiến đột phá so với dòng CPT cũ:</p>
<ul>
    <li><strong>F - FASTER (Nhanh hơn):</strong> Đầu Tip Total 4.0 cm² (màu tím) có diện tích tiếp xúc lớn hơn đầu tip cũ (3.0 cm²), giúp rút ngắn 25% thời gian điều trị.</li>
    <li><strong>L - ALGORITHM (Thuật toán thông minh):</strong> Công nghệ <strong>AccuREP™</strong> tự động đo trở kháng của da trước mỗi xung bắn (Shot) và tinh chỉnh năng lượng phát ra cho phù hợp nhất với vùng da đó. Đảm bảo năng lượng đồng nhất 100%.</li>
    <li><strong>X - EXPERIENCE (Trải nghiệm):</strong> Chế độ rung đa chiều (Comfort Pulse Technology) đánh lừa xúc giác, giảm tín hiệu đau truyền lên não -> Khách hàng cảm thấy êm ái hơn.</li>
</ul>

<h3>3. CÁC LOẠI ĐẦU TIP ĐIỀU TRỊ</h3>
<ul>
    <li><strong>Total Tip 4.0 (Màu tím):</strong> Dùng cho mặt, cổ, cơ thể. (Tip đa năng nhất).</li>
    <li><strong>Eye Tip 0.25 (Màu xanh lá):</strong> Chuyên dụng cho vùng mắt (mí trên, mí dưới). <em>Lưu ý: Cần đeo kính áp tròng bảo vệ mắt (Plastic Eye Shield) khi làm vùng này.</em></li>
    <li><strong>Body Tip 16.0 (Màu cam):</strong> Dùng cho vùng bụng, đùi, mông.</li>
</ul>

<h3>4. CHỈ ĐỊNH & CHỐNG CHỈ ĐỊNH</h3>
<p><strong>Chỉ định:</strong></p>
<ul>
    <li>Da mặt nhiều nếp nhăn li ti, lỗ chân lông to, bề mặt da thô ráp.</li>
    <li>Mí mắt sụp, da thừa vùng mắt.</li>
    <li>Da bụng chùng nhão sau sinh.</li>
</ul>
<p><strong>Chống chỉ định:</strong></p>
<ul>
    <li>Người mang máy tạo nhịp tim (Pacemaker) hoặc thiết bị điện tử cấy ghép (Do dùng sóng RF đơn cực sẽ chạy qua cơ thể).</li>
    <li>Phụ nữ mang thai.</li>
</ul>
"""
            },
            {
                "title": "CoolTech Define - Giảm béo quang đông (Cryolipolysis)",
                "category": "SERVICE",
                "image_url": "https://theaestheticsolutions.com/wp-content/uploads/2020/06/cooltech-define.jpg",
                "content": """
<h3>1. CƠ CHẾ KHOA HỌC: ĐÔNG HỦY MỠ (Cryolipolysis)</h3>
<p>Công nghệ này dựa trên phát hiện khoa học: <strong>Tế bào mỡ nhạy cảm với nhiệt độ lạnh hơn các tế bào khác</strong> (da, cơ, thần kinh). Khi bị làm lạnh xuống mức nhiệt âm sâu, tế bào mỡ sẽ bị tổn thương không hồi phục.</p>
<ul>
    <li><strong>Quy trình:</strong> Máy sử dụng lực hút chân không để cô lập khối mỡ vào tay cầm, sau đó hạ nhiệt độ xuống <strong>-8°C đến -10°C</strong> liên tục trong 70 phút.</li>
    <li><strong>Phản ứng sinh học:</strong> Tế bào mỡ bị kết tinh (đông cứng) -> Kích hoạt quá trình chết theo chương trình (Apoptosis).</li>
</ul>

<h3>2. QUÁ TRÌNH ĐÀO THẢI TỰ NHIÊN</h3>
<p>Khác với hút mỡ (lấy mỡ ra ngay), CoolTech giảm mỡ theo cơ chế sinh lý:</p>
<ol>
    <li><strong>Ngày 1-3:</strong> Vùng điều trị có thể hơi sưng, đỏ, tê bì nhẹ. Các tế bào mỡ bắt đầu phân hủy.</li>
    <li><strong>Tuần 2-4:</strong> Các đại thực bào (Hệ miễn dịch) đến "dọn dẹp" xác tế bào mỡ chết.</li>
    <li><strong>Tuần 4-12:</strong> Mỡ được đào thải ra ngoài qua hệ bài tiết và chuyển hóa qua gan. Lớp mỡ mỏng dần đi.</li>
</ol>

<h3>3. ƯU ĐIỂM CỦA COOLTECH DEFINE (THẾ HỆ MỚI)</h3>
<ul>
    <li><strong>360° Cooling:</strong> Tấm làm lạnh bao quanh 100% diện tích tay cầm (thế hệ cũ chỉ có 2 tấm 2 bên), giúp tăng hiệu quả hủy mỡ lên 20%.</li>
    <li><strong>4 tay cầm hoạt động cùng lúc:</strong> Có thể làm 4 vùng (ví dụ: 2 đùi + 2 bắp tay) trong 1 phiên điều trị -> Tiết kiệm thời gian.</li>
    <li><strong>9 loại tay cầm:</strong> Phù hợp mọi vị trí (nọng cằm, nách, bụng, đùi, đầu gối).</li>
</ul>

<h3>4. HIỆU QUẢ LÂM SÀNG</h3>
<ul>
    <li>Giảm trung bình <strong>20-25% bề dày lớp mỡ</strong> tại vùng điều trị sau 1 lần.</li>
    <li>Hiệu quả nhất với "mỡ cứng đầu" (Stubborn Fat) - loại mỡ khó giảm dù ăn kiêng hay tập luyện.</li>
    <li>Không xâm lấn, không cần nghỉ dưỡng.</li>
</ul>
"""
            },
            {
                "title": "Ultraformer MPT (Lifting MPT 5.0) - Nâng cơ siêu tốc",
                "category": "MACHINE",
                "image_url": "https://image.made-in-china.com/202f0j00sQGlEaWdCokP/Ultraformer-MPT-Hifu-Machine-High-Intensity-Focused-Ultrasound-Face-Lifting-Skin-Tightening.jpg",
                "content": """
<h3>1. MPT LÀ GÌ? (Micro-Pulsed Technology)</h3>
<p>Ultraformer MPT là thế hệ nâng cấp toàn diện của dòng máy HIFU Ultraformer III nổi tiếng. MPT mang đến cuộc cách mạng về tốc độ và mật độ năng lượng.</p>
<ul>
    <li><strong>Chế độ Normal (Dot Mode):</strong> Bắn ra 17 điểm nhiệt rời rạc trong 1 line (giống HIFU cũ). Dùng để nâng cơ.</li>
    <li><strong>Chế độ MP (Linear Mode - ĐỘC QUYỀN):</strong> Bắn ra <strong>417 điểm nhiệt siêu nhỏ</strong> liên tiếp tạo thành 1 đường thẳng năng lượng dày đặc. Giúp làm tan mỡ và săn chắc da cực mạnh (Contouring).</li>
</ul>

<h3>2. ĐẦU TIP "ULTRA BOOSTER" - VŨ KHÍ BÍ MẬT</h3>
<p>Ngoài các đầu tip tiêu chuẩn (1.5, 3.0, 4.5mm), MPT có thêm tay cầm dạng bút (Pen-type) với đầu tip tròn xoay:</p>
<ul>
    <li>Dễ dàng đi vào các vùng cong, nhỏ hẹp: Rãnh mũi má, quanh mắt, vùng quanh miệng.</li>
    <li>Tác động kép: Vừa nâng cơ, vừa đẩy tinh chất (HIFU dẫn xuất) thẩm thấu sâu vào da, giúp da căng bóng (Glowy skin) ngay sau làm.</li>
</ul>

<h3>3. SO SÁNH VỚI HIFU TRUYỀN THỐNG</h3>
<table class="table table-bordered">
    <thead class="table-light">
        <tr><th>Đặc điểm</th><th>HIFU Cũ</th><th>Ultraformer MPT</th></tr>
    </thead>
    <tbody>
        <tr><td><strong>Tốc độ bắn</strong></td><td>Chậm (2-3s/shot)</td><td>Siêu nhanh (0.4s/shot) -> Ít đau hơn.</td></tr>
        <tr><td><strong>Mật độ nhiệt</strong></td><td>Thấp (17 điểm)</td><td>Cao gấp 25 lần (417 điểm).</td></tr>
        <tr><td><strong>Cảm giác</strong></td><td>Khá đau, buốt xương</td><td>Êm ái, châm chích nhẹ.</td></tr>
        <tr><td><strong>Thời gian làm</strong></td><td>45-60 phút</td><td>15-20 phút (Full face).</td></tr>
    </tbody>
</table>

<h3>4. ỨNG DỤNG ĐIỀU TRỊ</h3>
<ul>
    <li>Thon gọn mặt V-line, giảm má bầu, nọng cằm.</li>
    <li>Nâng cơ chảy xệ nhẹ đến trung bình.</li>
    <li>Trẻ hóa da tức thì (Red Carpet Treatment) trước các sự kiện quan trọng.</li>
</ul>
"""
            },
            {
                "title": "Laser Revlite SI Cynosure - Chuẩn mực trị nám & Sắc tố",
                "category": "MACHINE",
                "image_url": "https://cynosure.com.vn/wp-content/uploads/2021/05/Revlite-SI.png",
                "content": """
<h3>1. CÔNG NGHỆ PTP (PhotoAcoustic Technology Pulse)</h3>
<p>Revlite SI là hệ thống Laser Nd:YAG Q-Switched cao cấp. Điểm khác biệt nằm ở công nghệ PTP - Xung quang âm:</p>
<ul>
    <li>Thay vì phát ra 1 xung năng lượng lớn (dễ gây tổn thương nhiệt, tăng sắc tố dội ngược), Revlite SI phát ra <strong>2 xung cực ngắn</strong> (độ rộng xung nano giây) liên tiếp nhau.</li>
    <li>Tạo ra hiệu ứng "rung lắc" quang âm cực mạnh, phá vỡ hạt sắc tố thành các mảnh nhỏ li ti như bụi mịn mà không gây nóng rát da.</li>
</ul>

<h3>2. CƠ CHẾ ĐIỀU TRỊ</h3>
<ul>
    <li><strong>Bước sóng 1064nm:</strong> Tác động sâu xuống trung bì, điều trị nám chân sâu, Nevus Hori, xóa xăm màu đen/xanh. Nó không bị hấp thụ bởi nước và hemoglobin nên rất an toàn, không gây chảy máu.</li>
    <li><strong>Bước sóng 532nm:</strong> Tác động nông ở thượng bì, điều trị tàn nhang, đồi mồi, xóa xăm màu đỏ.</li>
</ul>

<h3>3. CÁC ỨNG DỤNG LÂM SÀNG</h3>
<ul>
    <li><strong>Trị nám (Melasma):</strong> Là lựa chọn hàng đầu cho nám hỗn hợp, nám mảng. Kiểm soát sắc tố an toàn, ít nguy cơ PIH (tăng sắc tố sau viêm).</li>
    <li><strong>Xóa xăm:</strong> Xóa sạch các hình xăm không để lại sẹo.</li>
    <li><strong>Laser Toning (Trẻ hóa da):</strong> Đi laser năng lượng thấp toàn mặt giúp:
        <ul>
            <li>Làm đồng đều màu da, sáng da.</li>
            <li>Se khít lỗ chân lông (nhờ kích thích collagen nhẹ).</li>
            <li>Giảm dầu nhờn, giảm mụn cám.</li>
            <li>Làm mờ lông tơ (Vellus hair).</li>
        </ul>
    </li>
</ul>

<h3>4. LIỆU TRÌNH GỢI Ý</h3>
<ul>
    <li><strong>Trị nám:</strong> 10-15 buổi, khoảng cách 1-2 tuần/lần.</li>
    <li><strong>Laser Toning:</strong> Có thể làm duy trì hàng tháng như một phương pháp skincare cao cấp.</li>
    <li><strong>Lưu ý:</strong> Chống nắng kỹ sau điều trị là bắt buộc.</li>
</ul>
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
                self.stdout.write(self.style.SUCCESS(f'Đã tạo mới: {doc.title}'))
            else:
                self.stdout.write(self.style.WARNING(f'Đã cập nhật: {doc.title}'))