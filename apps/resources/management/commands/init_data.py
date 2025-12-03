from django.core.management.base import BaseCommand
from apps.resources.models import ProductDocument

class Command(BaseCommand):
    help = 'Khởi tạo dữ liệu tài liệu sản phẩm chuẩn Y khoa (Medical Grade)'

    def handle(self, *args, **kwargs):
        # Xóa dữ liệu cũ để nạp dữ liệu mới
        ProductDocument.objects.all().delete()
        self.stdout.write(self.style.WARNING('Đang xóa dữ liệu cũ và nạp bộ tài liệu chuyên sâu...'))

        data = [
            {
                "title": "Ultherapy Prime - Hệ thống Nâng cơ Vi điểm MFU-V (Medical Guide)",
                "category": "MACHINE",
                "image_url": "https://vmedical.com.vn/wp-content/uploads/2023/10/Ultherapy-Prime.jpg",
                "content": """
<div class="doc-medical-content">
    <div class="alert alert-primary shadow-sm">
        <h5 class="alert-heading fw-bold"><i class="bi bi-info-circle-fill me-2"></i>TỔNG QUAN CÔNG NGHỆ</h5>
        <p class="mb-0">Ultherapy Prime là thế hệ mới nhất của hệ thống nâng cơ không xâm lấn đạt chuẩn vàng (Gold Standard), sử dụng sóng siêu âm hội tụ vi điểm kết hợp hình ảnh trực quan (MFU-V: Micro-Focused Ultrasound with Visualization). Đây là thiết bị duy nhất được FDA Hoa Kỳ cấp phép nâng cơ (Lifting) cho vùng: Cung mày, Cổ, Cằm và Ngực trên.</p>
    </div>

    <h3 class="text-primary mt-4 border-bottom pb-2">1. CƠ CHẾ SINH HỌC & VẬT LÝ (MECHANISM OF ACTION)</h3>
    <div class="row mt-3">
        <div class="col-md-12">
            <p><strong>Nguyên lý MFU (Micro-Focused Ultrasound):</strong></p>
            <p>Ultherapy phát ra sóng siêu âm hội tụ năng lượng cao tại một điểm đích chính xác dưới da mà không gây tổn thương bề mặt. Quá trình này tạo ra các <strong>Điểm đông nhiệt (TCPs - Thermal Coagulation Points)</strong>.</p>
            <ul>
                <li><strong>Nhiệt độ mục tiêu:</strong> 60°C - 70°C. Đây là nhiệt độ lý tưởng để phá vỡ các liên kết hydro trong phân tử collagen (biến tính collagen) và kích thích phản ứng chữa lành vết thương (Wound Healing Response).</li>
                <li><strong>Thể tích điểm nhiệt:</strong> Mỗi điểm TCP có kích thước < 1mm³, đảm bảo sự chính xác tuyệt đối.</li>
            </ul>
            
            <p><strong>Quá trình Tân tạo Collagen (Neocollagenesis):</strong></p>
            <ol>
                <li><strong>Giai đoạn Viêm (0-48h):</strong> Nhiệt độ làm co rút tức thì các sợi collagen (Co nhiệt), bệnh nhân cảm thấy da săn lại ngay lập tức. Các tế bào miễn dịch (bạch cầu, đại thực bào) được huy động để dọn dẹp các mô bị tổn thương nhiệt.</li>
                <li><strong>Giai đoạn Tăng sinh (2 ngày - 6 tuần):</strong> Các nguyên bào sợi (Fibroblasts) được kích hoạt mạnh mẽ, tổng hợp Collagen Type III (collagen non).</li>
                <li><strong>Giai đoạn Tái cấu trúc (3 tuần - 1 năm):</strong> Collagen Type III dần chuyển hóa thành Collagen Type I bền vững hơn. Liên kết ngang giữa các sợi collagen được củng cố, tạo nên mạng lưới nâng đỡ da vững chắc.</li>
            </ol>
        </div>
    </div>

    <h3 class="text-primary mt-4 border-bottom pb-2">2. ĐẦU DÒ & ĐỘ SÂU ĐIỀU TRỊ (TRANSDUCERS)</h3>
    <table class="table table-bordered table-striped mt-3 small">
        <thead class="table-dark">
            <tr>
                <th>Tên Đầu Dò</th>
                <th>Tần số (MHz)</th>
                <th>Độ sâu (mm)</th>
                <th>Mục tiêu giải phẫu (Target Tissue)</th>
                <th>Ứng dụng lâm sàng</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>DS 4-4.5</strong></td>
                <td>4 MHz</td>
                <td>4.5 mm</td>
                <td>Lớp cân cơ nông (SMAS) / Platysma</td>
                <td>Nâng cơ, làm thon gọn hàm, xóa nọng cằm. Tác động vào lớp cơ được phẫu thuật căng da mặt can thiệp.</td>
            </tr>
            <tr>
                <td><strong>DS 7-3.0</strong></td>
                <td>7 MHz</td>
                <td>3.0 mm</td>
                <td>Lớp Hạ bì sâu / Lớp mỡ dưới da</td>
                <td>Làm săn chắc (Tightening), kích thích tăng sinh collagen cấu trúc, giảm mỡ nhẹ.</td>
            </tr>
            <tr>
                <td><strong>DS 10-1.5</strong></td>
                <td>10 MHz</td>
                <td>1.5 mm</td>
                <td>Lớp Hạ bì nông (Superficial Dermis)</td>
                <td>Xóa nhăn bề mặt, làm mịn lỗ chân lông, điều trị vùng da mỏng (quanh mắt, trán).</td>
            </tr>
        </tbody>
    </table>

    <h3 class="text-primary mt-4 border-bottom pb-2">3. CÔNG NGHỆ PRIME (THẾ HỆ MỚI)</h3>
    <ul>
        <li><strong>Real-time Visualization (DeepSEE™):</strong> Công nghệ hiển thị hình ảnh siêu âm thời gian thực. Bác sĩ nhìn thấy rõ lớp da, mỡ, cơ và xương.
            <br><em>-> Ý nghĩa lâm sàng:</em> Đảm bảo đầu dò tiếp xúc tốt (Coupling), tránh bắn vào xương (gây đau), tránh mạch máu/thần kinh, xác định chính xác độ dày da để chọn đầu tip phù hợp.</li>
        <li><strong>Faster Processing:</strong> Tốc độ bắn nhanh hơn 20% so với dòng Classic, giảm thời gian điều trị, tăng sự thoải mái cho bệnh nhân.</li>
    </ul>

    <h3 class="text-primary mt-4 border-bottom pb-2">4. CHỈ ĐỊNH & CHỐNG CHỈ ĐỊNH (INDICATIONS)</h3>
    <div class="row">
        <div class="col-md-6">
            <div class="card h-100 border-success">
                <div class="card-header bg-success text-white fw-bold">CHỈ ĐỊNH (TỐT NHẤT)</div>
                <div class="card-body">
                    <ul>
                        <li>Da chùng nhão mức độ nhẹ đến trung bình (Mild to Moderate Laxity).</li>
                        <li>Đường viền hàm (Jawline) không rõ nét, chảy xệ.</li>
                        <li>Nếp nhăn rãnh mũi má sâu.</li>
                        <li>Cung mày sa trễ, sụp mí mắt trên.</li>
                        <li>Da cổ chùng, da ngực nhăn nheo.</li>
                        <li>Độ tuổi lý tưởng: 30 - 60 tuổi.</li>
                    </ul>
                </div>
            </div>
        </div>
        <div class="col-md-6">
            <div class="card h-100 border-danger">
                <div class="card-header bg-danger text-white fw-bold">CHỐNG CHỈ ĐỊNH</div>
                <div class="card-body">
                    <ul>
                        <li>Vết thương hở hoặc tổn thương viêm nhiễm tại vùng điều trị.</li>
                        <li>Mụn trứng cá dạng nang nặng (Cystic Acne).</li>
                        <li>Cấy chỉ vàng/kim loại tại vùng điều trị (Chống chỉ định tương đối).</li>
                        <li>Phụ nữ mang thai hoặc cho con bú.</li>
                        <li>Bệnh lý tự miễn (Lupus, Xơ cứng bì) - Cần thận trọng do đáp ứng collagen kém.</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</div>
"""
            },
            {
                "title": "Thermage FLX - Radiofrequency Đơn cực (Technical Specification)",
                "category": "MACHINE",
                "image_url": "https://vmedical.com.vn/wp-content/uploads/2023/10/Thermage-FLX.jpg",
                "content": """
<div class="doc-medical-content">
    <div class="alert alert-info shadow-sm">
        <h5 class="alert-heading fw-bold"><i class="bi bi-cpu-fill me-2"></i>GIỚI THIỆU CHUNG</h5>
        <p class="mb-0">Thermage FLX (Faster - Algorithm - Experience) là thế hệ thứ 4 của công nghệ RF đơn cực (Monopolar Radiofrequency). Đây là tiêu chuẩn vàng trong điều trị xóa nhăn, trẻ hóa da bề mặt và tăng độ đàn hồi cho da.</p>
    </div>

    <h3 class="text-primary mt-4 border-bottom pb-2">1. CƠ CHẾ VẬT LÝ: NHIỆT KHỐI ĐẢO NGƯỢC (REVERSE THERMAL GRADIENT)</h3>
    <p>Khác với các công nghệ RF thông thường, Thermage sử dụng cơ chế truyền nhiệt đặc biệt:</p>
    <ul>
        <li><strong>Năng lượng RF (6.78 MHz):</strong> Đi sâu vào da theo cơ chế dung kháng (Capacitive Coupling), tạo ra nhiệt lượng khối (Bulk Heating) đồng nhất tại lớp trung bì và mô dưới da (lên đến 60°C).</li>
        <li><strong>Làm lạnh bề mặt (Cryogen Cooling):</strong> Đầu tip phun khí lạnh liên tục trước, trong và sau mỗi xung bắn.</li>
    </ul>
    <div class="p-3 bg-light border rounded">
        <strong>💡 Kết quả:</strong> Bề mặt da được bảo vệ ở nhiệt độ mát, trong khi lớp sâu bên dưới được nung nóng mạnh mẽ. Điều này cho phép đưa một lượng nhiệt cực lớn vào sâu trong da mà không gây bỏng biểu bì.
    </div>

    <h3 class="text-primary mt-4 border-bottom pb-2">2. CÔNG NGHỆ ACCUREP™ (ALGORITHM)</h3>
    <p>Đây là cải tiến đột phá nhất của dòng FLX so với CPT:</p>
    <ul>
        <li><strong>Tự động hiệu chỉnh (Auto-Calibration):</strong> Trước mỗi shot bắn (xung), máy sẽ đo trở kháng (Impedance) của da bệnh nhân.</li>
        <li><strong>Tối ưu hóa năng lượng:</strong> Máy tự động điều chỉnh điện áp phát ra để đảm bảo năng lượng hấp thụ thực tế tại mô đúng bằng mức năng lượng bác sĩ cài đặt, bất kể độ ẩm hay độ dày da thay đổi.</li>
        <li><strong>Lợi ích:</strong> Kết quả điều trị đồng nhất trên mọi vùng da, giảm nguy cơ bỏng.</li>
    </ul>

    <h3 class="text-primary mt-4 border-bottom pb-2">3. THÔNG SỐ KỸ THUẬT ĐẦU TIP (TREATMENT TIPS)</h3>
    <table class="table table-bordered table-hover mt-3 small">
        <thead class="table-primary">
            <tr>
                <th>Loại Tip</th>
                <th>Diện tích (cm²)</th>
                <th>Số Shots</th>
                <th>Độ sâu tác động</th>
                <th>Vùng chỉ định</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>Total Tip 4.0 (Tím)</strong></td>
                <td>4.0 cm²</td>
                <td>300 / 600 / 900</td>
                <td>4.3 mm</td>
                <td>Mặt, Cổ, Một số vùng cơ thể nhỏ. (Tip phổ biến nhất).</td>
            </tr>
            <tr>
                <td><strong>Eye Tip 0.25 (Xanh)</strong></td>
                <td>0.25 cm²</td>
                <td>225 / 450</td>
                <td>1.1 mm</td>
                <td>Mí mắt trên, Mí mắt dưới. (Yêu cầu dùng kính bảo vệ mắt).</td>
            </tr>
            <tr>
                <td><strong>Body Tip 16.0 (Cam)</strong></td>
                <td>16.0 cm²</td>
                <td>500</td>
                <td>4.3 mm (Rộng hơn)</td>
                <td>Bụng, Đùi, Mông, Bắp tay. (Có chế độ rung).</td>
            </tr>
        </tbody>
    </table>

    <h3 class="text-primary mt-4 border-bottom pb-2">4. TIẾN TRÌNH LÂM SÀNG (CLINICAL COURSE)</h3>
    <ul>
        <li><strong>Immediate Response (Tức thì):</strong> Các sợi collagen già cỗi bị nhiệt làm co rút (denaturation), da săn lại ngay lập tức sau khi làm 1 bên mặt (Half-face demo).</li>
        <li><strong>Delayed Response (Dài hạn):</strong> Quá trình sửa chữa mô kích thích sản sinh collagen mới. Da tiếp tục săn chắc và mượt mà hơn trong 2-6 tháng tiếp theo.</li>
        <li><strong>Vector căng da:</strong> Thermage làm săn chắc da theo chiều ngang (Tightening) và chiều dọc (Contouring), giúp khuôn mặt thon gọn hơn.</li>
    </ul>
</div>
"""
            },
            {
                "title": "CoolTech Define - Cryolipolysis: Cơ chế & Phác đồ Giảm mỡ",
                "category": "SERVICE",
                "image_url": "https://theaestheticsolutions.com/wp-content/uploads/2020/06/cooltech-define.jpg",
                "content": """
<div class="doc-medical-content">
    <div class="alert alert-warning shadow-sm">
        <h5 class="alert-heading fw-bold"><i class="bi bi-snow me-2"></i>GIẢM BÉO NHIỆT LẠNH (QUANG ĐÔNG)</h5>
        <p class="mb-0">CoolTech Define sử dụng công nghệ Cryolipolysis (Phân hủy mỡ bằng nhiệt lạnh) để tiêu diệt tế bào mỡ vĩnh viễn mà không cần phẫu thuật hút mỡ.</p>
    </div>

    <h3 class="text-primary mt-4 border-bottom pb-2">1. CƠ SỞ KHOA HỌC: APOPTOSIS (CHẾT THEO CHƯƠNG TRÌNH)</h3>
    <p>Công nghệ dựa trên đặc tính sinh học khác biệt giữa tế bào mỡ (Adipocyte) và các tế bào khác:</p>
    <ul>
        <li><strong>Độ nhạy cảm nhiệt:</strong> Tế bào mỡ giàu lipid, sẽ bị kết tinh (crystallize) và tổn thương ở nhiệt độ từ +4°C đến -10°C. Trong khi đó, da, cơ, thần kinh, mạch máu chịu được nhiệt độ lạnh tốt hơn nhiều.</li>
        <li><strong>Cơ chế Apoptosis:</strong> Khi bị làm lạnh sâu có kiểm soát, tế bào mỡ không chết ngay lập tức (Necrosis - Hoại tử) mà kích hoạt tín hiệu chết tự nhiên (Apoptosis). Tế bào teo nhỏ, màng tế bào vỡ ra từ từ.</li>
    </ul>

    <h3 class="text-primary mt-4 border-bottom pb-2">2. QUY TRÌNH SINH LÝ BỆNH (PATHOPHYSIOLOGY)</h3>
    <div class="timeline-steps">
        <ul>
            <li><strong>Trong khi điều trị (70 phút):</strong> Lực hút chân không cô lập mô mỡ, tấm làm lạnh hạ nhiệt độ mô xuống -8°C đến -10°C. Máu lưu thông bị hạn chế tạm thời (Ischemia).</li>
            <li><strong>Ngay sau điều trị:</strong> Khối mỡ đông cứng (Butter stick). Cần massage ngay lập tức để phá vỡ các tinh thể băng, tái tưới máu (Reperfusion) và gia tăng hiệu quả hủy mỡ (Reperfusion Injury).</li>
            <li><strong>Ngày 1 - 3:</strong> Phản ứng viêm bắt đầu. Các tế bào miễn dịch (Neutrophils, Macrophages) di chuyển đến vùng mô mỡ bị tổn thương.</li>
            <li><strong>Ngày 14 - 90:</strong> Đại thực bào "ăn" (thực bào) các tế bào mỡ chết và các giọt lipid giải phóng. Lipid được vận chuyển qua hệ bạch huyết về gan và chuyển hóa năng lượng bình thường.</li>
        </ul>
    </div>

    <h3 class="text-primary mt-4 border-bottom pb-2">3. TAY CẦM ĐIỀU TRỊ & VÙNG CHỈ ĐỊNH</h3>
    <p>CoolTech Define sở hữu 9 loại tay cầm (Applicators) phù hợp mọi đường cong cơ thể:</p>
    <table class="table table-sm table-bordered mt-2">
        <tr>
            <td width="30%"><strong>Straight HP</strong></td>
            <td>Vùng phẳng: Bụng trên, Bụng dưới.</td>
        </tr>
        <tr>
            <td><strong>Curved HP</strong></td>
            <td>Vùng cong: Eo (Hông), Lưng, Đùi.</td>
        </tr>
        <tr>
            <td><strong>Tight HP</strong></td>
            <td>Vùng mỡ nhỏ, khó kẹp: Nách, Mỡ nếp lằn mông.</td>
        </tr>
        <tr>
            <td><strong>Double HP</strong></td>
            <td>Vùng bụng lớn (Diện tích điều trị lớn).</td>
        </tr>
        <tr>
            <td><strong>Oval Curved HP</strong></td>
            <td>Đùi ngoài, Hông lớn (Yên ngựa).</td>
        </tr>
        <tr>
            <td><strong>Tiny HP</strong></td>
            <td>Vùng nọng cằm (Submental fat).</td>
        </tr>
    </table>

    <h3 class="text-primary mt-4 border-bottom pb-2">4. TÁC DỤNG PHỤ & XỬ TRÍ</h3>
    <ul>
        <li><strong>Thường gặp:</strong> Đỏ da, bầm tím (do lực hút chân không), tê bì (mất cảm giác) vùng điều trị. Tự hết sau 1-3 tuần.</li>
        <li><strong>Đau muộn (Late-onset Pain):</strong> Đau nhói, buốt sau 3-5 ngày làm. Xử trí: Thuốc giảm đau thần kinh (Gabapentin) hoặc chườm ấm.</li>
        <li><strong>Tăng sản mỡ nghịch lý (PAH):</strong> Rất hiếm gặp (< 0.05%). Vùng mỡ to lên và cứng lại thay vì nhỏ đi. Xử trí: Hút mỡ.</li>
    </ul>
</div>
"""
            },
            {
                "title": "Ultraformer MPT (Lifting MPT 5.0) - Micro-Pulsed Technology",
                "category": "MACHINE",
                "image_url": "https://image.made-in-china.com/202f0j00sQGlEaWdCokP/Ultraformer-MPT-Hifu-Machine-High-Intensity-Focused-Ultrasound-Face-Lifting-Skin-Tightening.jpg",
                "content": """
<div class="doc-medical-content">
    <div class="alert alert-success shadow-sm">
        <h5 class="alert-heading fw-bold"><i class="bi bi-lightning-charge-fill me-2"></i>CÔNG NGHỆ MICRO-PULSED (MPT)</h5>
        <p class="mb-0">Ultraformer MPT là bước tiến vượt bậc của công nghệ HIFU (High Intensity Focused Ultrasound). Chuyển từ dạng điểm (Dot) sang dạng đường (Linear) với tốc độ siêu nhanh.</p>
    </div>

    <h3 class="text-primary mt-4 border-bottom pb-2">1. SO SÁNH CHẾ ĐỘ PHÁT XUNG (EMISSION MODES)</h3>
    <table class="table table-bordered text-center small">
        <thead class="table-light">
            <tr>
                <th>Chế độ</th>
                <th>Normal Mode (Truyền thống)</th>
                <th>MP Mode (Micro-Pulsed) - MỚI</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td class="fw-bold text-start">Dạng năng lượng</td>
                <td>Chuỗi các điểm nhiệt rời rạc (Dots)</td>
                <td>Chuỗi điểm siêu nhỏ, liên tiếp tạo thành 1 đường thẳng (Linear)</td>
            </tr>
            <tr>
                <td class="fw-bold text-start">Số điểm nhiệt (TCPs)</td>
                <td>17 - 25 điểm / shot</td>
                <td><strong>417 điểm</strong> / shot (Gấp 25 lần)</td>
            </tr>
            <tr>
                <td class="fw-bold text-start">Thời gian phát xung</td>
                <td>1.5 - 2 giây</td>
                <td><strong>0.4 giây</strong> (Siêu nhanh)</td>
            </tr>
            <tr>
                <td class="fw-bold text-start">Cảm giác đau</td>
                <td>Đau, buốt (do nhiệt tích tụ lâu tại 1 điểm)</td>
                <td>Êm dịu, ít đau (do nhiệt phân tán nhanh và mịn)</td>
            </tr>
            <tr>
                <td class="fw-bold text-start">Ứng dụng chính</td>
                <td>Nâng cơ (Lifting), Treo cơ</td>
                <td>Làm tan mỡ (Lipolysis), Săn chắc (Tightening), Contouring</td>
            </tr>
        </tbody>
    </table>

    <h3 class="text-primary mt-4 border-bottom pb-2">2. ĐẦU TIP ULTRA BOOSTER (PEN-TYPE)</h3>
    <p>Điểm độc đáo nhất của MPT là tay cầm dạng bút tròn xoay:</p>
    <ul>
        <li><strong>Thiết kế:</strong> Đầu típ nhỏ, hình tròn, diện tích tiếp xúc linh hoạt.</li>
        <li><strong>Vùng điều trị:</strong> Tiếp cận hoàn hảo các vùng cong, gồ ghề mà đầu típ thẳng (Linear) không làm được: Quanh mắt, Rãnh mũi má, Vùng quanh miệng, Viền hàm.</li>
        <li><strong>HIFU Dẫn xuất:</strong> Kết hợp với Serum chuyên dụng (như DSB - Deep Synergy Booster chứa PDRN, Glutathione...). Sóng siêu âm giúp mở đường dẫn, đẩy tinh chất thấm sâu vào da -> Hiệu quả căng bóng (Glow) tức thì.</li>
    </ul>

    <h3 class="text-primary mt-4 border-bottom pb-2">3. PHÁC ĐỒ ĐIỀU TRỊ ĐA TẦNG</h3>
    <p>Một liệu trình MPT chuẩn (Full Face) thường phối hợp 3 lớp:</p>
    <ul>
        <li><strong>Bước 1 (Lớp sâu 4.5mm):</strong> Dùng chế độ Normal (Dot) để treo cơ SMAS, định hình khung mặt.</li>
        <li><strong>Bước 2 (Lớp giữa 3.0mm):</strong> Dùng chế độ MP (Linear) để làm săn chắc mô mỡ, giảm nọng cằm, giảm má bầu.</li>
        <li><strong>Bước 3 (Lớp nông 1.5mm - Booster):</strong> Dùng đầu Pen đi xoắn ốc toàn mặt để xóa nhăn nông, làm sáng da và se khít lỗ chân lông.</li>
    </ul>
</div>
"""
            },
            {
                "title": "Revlite SI - Laser Q-Switched Nd:YAG & Công nghệ PTP",
                "category": "MACHINE",
                "image_url": "https://cynosure.com.vn/wp-content/uploads/2021/05/Revlite-SI.png",
                "content": """
<div class="doc-medical-content">
    <div class="alert alert-dark shadow-sm text-white bg-dark">
        <h5 class="alert-heading fw-bold"><i class="bi bi-lightbulb-fill me-2 text-warning"></i>CÔNG NGHỆ QUANG ÂM (PHOTO-ACOUSTIC)</h5>
        <p class="mb-0">Revlite SI là tiêu chuẩn vàng trong điều trị sắc tố da nhờ công nghệ xung quang âm PTP, giúp phá vỡ sắc tố mạnh mẽ mà giảm thiểu tổn thương nhiệt.</p>
    </div>

    <h3 class="text-primary mt-4 border-bottom pb-2">1. CÔNG NGHỆ PTP (PHOTOACOUSTIC TECHNOLOGY PULSE)</h3>
    <p><strong>Vấn đề của Laser cũ:</strong> Phát ra 1 xung đơn (Single Pulse) năng lượng cao. Để phá vỡ sắc tố sâu, cần năng lượng rất lớn -> Gây nóng, đau, dễ gây tăng sắc tố sau viêm (PIH).</p>
    <p><strong>Giải pháp của Revlite SI (PTP):</strong></p>
    <ul>
        <li>Thay vì 1 xung lớn, máy chia tách thành <strong>2 xung cực ngắn (nanosecond)</strong> liên tiếp nhau, cách nhau vài micro giây.</li>
        <li><strong>Hiệu ứng cộng hưởng:</strong> Xung thứ nhất làm rung chuyển hạt sắc tố. Xung thứ hai bồi thêm vào khi hạt sắc tố đang rung -> Tăng hiệu quả phá vỡ lên 60%.</li>
        <li><strong>An toàn:</strong> Đỉnh năng lượng của mỗi xung con thấp hơn -> Giảm tích nhiệt, giảm đau, an toàn cho da sẫm màu (Skin Type III-IV-V của người Việt Nam).</li>
    </ul>

    <h3 class="text-primary mt-4 border-bottom pb-2">2. THÔNG SỐ KỸ THUẬT & TƯƠNG TÁC MÔ</h3>
    <ul>
        <li><strong>Bước sóng 1064nm:</strong>
            <ul>
                <li>Hấp thụ mạnh bởi màu đen, xanh đen. Ít hấp thụ bởi Melanin (biểu bì) và Hemoglobin (máu).</li>
                <li>Xuyên sâu nhất vào da (đến lớp trung bì sâu).</li>
                <li><em>Chỉ định:</em> Nám chân sâu (Hori), Xóa xăm màu đen, Trẻ hóa da (Laser Toning), Nevus of Ota.</li>
            </ul>
        </li>
        <li><strong>Bước sóng 532nm:</strong>
            <ul>
                <li>Hấp thụ cực mạnh bởi Melanin và màu đỏ.</li>
                <li>Xuyên nông (chỉ ở thượng bì).</li>
                <li><em>Chỉ định:</em> Tàn nhang (Freckles), Đồi mồi (Lentigines), Nám mảng nông, Xóa xăm màu đỏ.</li>
            </ul>
        </li>
    </ul>

    <h3 class="text-primary mt-4 border-bottom pb-2">3. CLINICAL ENDPOINTS (ĐIỂM LÂM SÀNG CẦN ĐẠT)</h3>
    <p>Khi điều trị, bác sĩ/KTV cần quan sát phản ứng da để dừng lại đúng lúc:</p>
    <table class="table table-bordered mt-2 small">
        <thead class="table-secondary">
            <tr>
                <th>Dịch vụ</th>
                <th>Phản ứng da chuẩn (Endpoint)</th>
                <th>Lưu ý</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>Laser Toning (Trẻ hóa/Nám)</strong></td>
                <td>Hồng ban nhẹ (Erythema) thoáng qua. Lông tơ chuyển sang màu trắng hoặc cháy sém nhẹ.</td>
                <td>Tuyệt đối không bắn đến chảy máu (Petechiae) với nám Melasma -> Dễ gây dội ngược sắc tố.</td>
            </tr>
            <tr>
                <td><strong>Xóa tàn nhang/Đồi mồi (532nm)</strong></td>
                <td>Trắng sương nhẹ (Mild Frosting) hoặc xám màu thương tổn ngay lập tức.</td>
                <td>Vảy sẽ đóng sau 1-2 ngày và bong sau 5-7 ngày.</td>
            </tr>
            <tr>
                <td><strong>Xóa xăm</strong></td>
                <td>Trắng sương rõ rệt (Immediate Whitening) do hiện tượng bốc hơi nước trong tế bào. Có thể có điểm xuất huyết nhỏ.</td>
                <td>Cần chườm lạnh ngay sau bắn.</td>
            </tr>
        </tbody>
    </table>

    <h3 class="text-primary mt-4 border-bottom pb-2">4. PHÁC ĐỒ ĐIỀU TRỊ NÁM MELASMA</h3>
    <ul>
        <li><strong>Giai đoạn Tấn công (10 buổi đầu):</strong> 1 tuần/lần. Sử dụng chế độ Toning 1064nm, Spot size lớn (8mm), năng lượng thấp (1.4 - 2.0 J/cm²). Đi lướt đều toàn mặt 2-3 passes.</li>
        <li><strong>Giai đoạn Duy trì:</strong> 2-4 tuần/lần. Giãn cách để da phục hồi.</li>
        <li><strong>Kết hợp:</strong> Mesotherapy (Tiêm nám), Peel da, Thuốc bôi (Hydroquinone/Arbutin) để tăng hiệu quả.</li>
    </ul>
</div>
"""
            }
        ]

        for item in data:
            doc, created = ProductDocument.objects.update_or_create(
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