import json
from pathlib import Path

from django.conf import settings
from openai import OpenAI

KNOWLEDGE_BASE_PATH = Path(__file__).resolve().parent / 'knowledge' / 'viral_playbook_2026.md'

# Đúng thứ tự, tên & trọng số các tiêu chí ở mục 6 (kịch bản có lời thoại) và mục 7 (bắt trend/format)
# của cẩm nang (viral_playbook_2026.md). Điểm tổng KHÔNG để AI tự đoán (dễ cho kết quả khác nhau giữa các
# lần chấm cùng 1 kịch bản) mà tính bằng trung bình có trọng số của các sub_score - đảm bảo nhất quán.
SCRIPT_CHECK_WEIGHTS = {
    "Sức mạnh Hook (0-3s)": 25,
    "Cấu trúc & nhịp độ": 15,
    "Payoff rõ ràng": 15,
    "CTA": 10,
    "Phù hợp nền tảng": 10,
    "Tính chân thực (UGC)": 10,
    "Sản xuất (hình ảnh/âm thanh/nhịp điệu)": 10,
    "Rủi ro/tuân thủ": 5,
}

FORMAT_CHECK_WEIGHTS = {
    "Payoff thị giác / độ tương phản": 30,
    "Bắt trend đúng lúc": 15,
    "Thời điểm & nhịp reveal": 15,
    "Khả năng xem lại (loopability)": 15,
    "Tính chân thực/đáng tin": 10,
    "Phù hợp nền tảng": 10,
    "Rủi ro/tuân thủ": 5,
}

CHECK_WEIGHTS_BY_TYPE = {
    "SCRIPT": SCRIPT_CHECK_WEIGHTS,
    "FORMAT": FORMAT_CHECK_WEIGHTS,
}

PRODUCTION_ASPECTS = [
    "Visual hook (hình ảnh mở đầu)",
    "Nhạc nền / âm thanh",
    "Nhịp điệu / dựng phim",
    "Sub text / chữ trên màn hình",
    "Hiệu ứng (effects & transitions)",
    "Góc quay (camera angle)",
]

EXAMPLE_SUGGESTION_STYLE = (
    'Thêm mini-hook sau mỗi 10-15 giây: ví dụ "Nhưng khoan, có một điều ít người biết..."'
)


def _load_knowledge_base():
    return KNOWLEDGE_BASE_PATH.read_text(encoding='utf-8')


def _result_json_shape(check_criteria):
    return f"""{{
  "verdict": "<kết luận ngắn gọn, thẳng thắn, 1-2 câu>",
  "checks": [
    {{"criterion": "<đúng tên 1 trong các tiêu chí bên dưới>", "status": "<good|ok|bad>", "sub_score": <số nguyên 0-100>, "assessment": "<nhận xét ngắn gọn 1 câu, cụ thể, thẳng thắn>"}},
    ... (đủ {len(check_criteria)} dòng, đúng thứ tự, đúng tên các tiêu chí: {", ".join(check_criteria)})
  ],
  "strengths": ["<điểm mạnh cụ thể>", "..."],
  "weaknesses": ["<điểm yếu cụ thể>", "..."],
  "suggestions": [
    "<gợi ý cụ thể, LUÔN kèm câu ví dụ/mô tả thật trong dấu ngoặc kép để áp dụng ngay. Đúng format: '<mô tả gợi ý>: ví dụ \\"<câu mẫu hoặc mô tả cảnh quay cụ thể>\\"'>",
    ... (tối thiểu 6-8 gợi ý)
  ],
  "rewrite_examples": [
    {{"section": "<tên đoạn/cảnh, VD: 'Câu mở đầu (Hook)' / 'Cảnh reveal kết quả' / 'Câu kết (CTA)'>", "original": "<trích ĐÚNG NGUYÊN VĂN câu/mô tả cảnh yếu trong nội dung đang chấm, hoặc để trống nếu là phần hoàn toàn mới cần thêm>", "rewritten": "<câu/mô tả cảnh viết lại HOÀN CHỈNH, viral hơn, sẵn sàng dùng luôn>", "why": "<lý do ngắn gọn tại sao bản này viral/hiệu quả hơn, dựa vào cẩm nang>"}},
    ... (tối thiểu 4-6 dòng)
  ],
  "production_tips": [
    {{"aspect": "<đúng tên 1 trong 6 khía cạnh bên dưới>", "suggestion": "<gợi ý cụ thể, áp dụng được ngay cho đúng nội dung này>"}},
    ... (đủ 6 dòng, đúng thứ tự, đúng tên: {", ".join(PRODUCTION_ASPECTS)})
  ],
  "platform_fit": "<nhận xét mức độ phù hợp với đặc thù nền tảng đã chọn>"
}}"""


def compute_score(checks, content_type="SCRIPT"):
    """
    Tính điểm tổng = trung bình có trọng số của sub_score theo đúng % ở mục 6/7 cẩm nang
    (tuỳ content_type). Không dùng điểm do AI tự đoán độc lập - tránh lệch điểm giữa các lần
    chấm cùng 1 nội dung. Bỏ qua tiêu chí không khớp tên thay vì lỗi cứng.
    """
    weights = CHECK_WEIGHTS_BY_TYPE.get(content_type, SCRIPT_CHECK_WEIGHTS)
    weighted_sum = 0
    total_weight = 0
    for item in checks or []:
        weight = weights.get(item.get('criterion'))
        sub_score = item.get('sub_score')
        if weight is None or not isinstance(sub_score, (int, float)):
            continue
        weighted_sum += weight * sub_score
        total_weight += weight

    if total_weight == 0:
        return 0
    return round(weighted_sum / total_weight)


def _client():
    return OpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")


def analyze_script(platform_display, content_type, content_type_display, hook, script_content, post_caption):
    """
    Gửi nội dung lên DeepSeek để chấm điểm & nhận xét dựa trên cẩm nang viral 2026.
    content_type: "SCRIPT" (mục 6) hoặc "FORMAT" (mục 7) - dùng đúng bộ tiêu chí tương ứng.
    Trả về dict có thêm khoá "score" (tính bằng compute_score, không phải AI tự đoán).
    Raise Exception nếu gọi API lỗi.
    """
    knowledge_base = _load_knowledge_base()
    weights = CHECK_WEIGHTS_BY_TYPE.get(content_type, SCRIPT_CHECK_WEIGHTS)
    check_criteria = list(weights.keys())
    section_ref = "mục 6" if content_type == "SCRIPT" else "mục 7"

    system_prompt = f"""Bạn là biên tập viên & chuyên gia viết kịch bản viral hàng đầu, chấm điểm VÀ trực tiếp
viết lại nội dung video ngắn dựa CHÍNH XÁC theo cẩm nang dưới đây - không dùng kiến thức lý thuyết chung
chung, không xu nịnh, phải công tâm. Nếu nội dung yếu, nói thẳng là yếu và chỉ rõ tại sao. Luôn góp ý cụ thể,
kèm CÂU CHỮ/MÔ TẢ CẢNH THẬT có thể áp dụng ngay - tuyệt đối không nhận xét mơ hồ kiểu "cần hấp dẫn hơn".

Loại nội dung đang chấm: "{content_type_display}". BẮT BUỘC dùng đúng bộ tiêu chí ở {section_ref} của cẩm
nang cho loại này - KHÔNG được áp tiêu chí của loại kia (VD: không chấm "Hook nói"/"CTA nói" cho nội dung
dạng bắt trend/format không lời thoại - đó là lỗi chấm sai đã từng xảy ra).

Đây là ví dụ về MỘT gợi ý ĐÚNG chuẩn bạn phải viết (ngắn gọn nhưng có câu mẫu/mô tả thật, tự nhiên, viral):
"{EXAMPLE_SUGGESTION_STYLE}"

Mọi gợi ý trong "suggestions" và mọi dòng trong "rewrite_examples" đều phải đạt chất lượng như ví dụ trên -
viết như một biên kịch content viral thực thụ đang trực tiếp sửa bài cho đồng nghiệp, không phải một AI
liệt kê lý thuyết. Câu mẫu phải tự nhiên bằng tiếng Việt đời thường, đúng giọng văn ngành thẩm mỹ/y tế.

Bắt buộc chấm đủ theo checklist {len(check_criteria)} tiêu chí ở {section_ref} của cẩm nang (giống kiểu
Yoast SEO chấm từng mục riêng với đèn xanh/vàng/đỏ), và góp ý sản xuất chi tiết theo đúng 6 khía cạnh ở
mục 5 (visual hook, nhạc nền, nhịp điệu, sub text, hiệu ứng, góc quay) - áp dụng cụ thể vào chính nội dung
đang chấm, không nói chung chung.

QUAN TRỌNG - chấm sub_score cho từng tiêu chí phải nhất quán, dựa trên bằng chứng cụ thể, không cảm tính:
nếu 1 tiêu chí có lỗi rõ ràng thì sub_score phải dưới 30, không được chấm cao vì "cảm thấy tạm ổn".
status "bad" tương ứng sub_score dưới 40, "ok" tương ứng 40-69, "good" tương ứng từ 70 trở lên - PHẢI khớp
giữa status và sub_score, không được mâu thuẫn.

QUAN TRỌNG - "rewrite_examples": phải trích ĐÚNG NGUYÊN VĂN câu/mô tả gốc từ nội dung đang chấm (copy chính
xác, không diễn giải lại), rồi viết bản thay thế hoàn chỉnh, sẵn sàng dùng ngay.

--- CẨM NANG VIRAL 2026 ---
{knowledge_base}
--- HẾT CẨM NANG ---

Trả lời DUY NHẤT bằng 1 object JSON hợp lệ, đúng cấu trúc sau, không thêm bất kỳ chữ nào khác ngoài JSON:
{_result_json_shape(check_criteria)}

Trả lời bằng tiếng Việt."""

    user_prompt = f"""Nền tảng đăng: {platform_display}
Loại nội dung: {content_type_display}

Hook / Mô tả cảnh mở đầu:
{hook}

Nội dung / Mô tả diễn biến các cảnh:
{script_content}

Nội dung bài đăng (caption):
{post_caption or '(không có)'}

Hãy chấm điểm, nhận xét, và VIẾT LẠI trực tiếp các phần yếu nhất theo đúng checklist {section_ref}, gợi ý
sản xuất theo mục 5, và bắt buộc có rewrite_examples cụ thể như một biên kịch thật sự sửa bài."""

    response = _client().chat.completions.create(
        model="deepseek-chat",
        max_tokens=8192,
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    result = json.loads(response.choices[0].message.content)
    result['score'] = compute_score(result.get('checks', []), content_type)
    return result


def suggest_content_ideas(niche, notes):
    """
    Gợi ý danh sách ý tưởng content viral (cả dạng kịch bản lẫn dạng bắt trend/format) dựa trên
    cẩm nang viral 2026, cho 1 ngành/dịch vụ cụ thể. Trả về dict {"ideas": [...]}.
    """
    knowledge_base = _load_knowledge_base()

    system_prompt = f"""Bạn là chuyên gia sáng tạo nội dung viral ngành thẩm mỹ/da liễu, nắm chắc cẩm nang
dưới đây. Nhiệm vụ: gợi ý danh sách ý tưởng content CỤ THỂ, THỰC DỤNG, đã được kiểm chứng là dạng dễ viral
(không lý thuyết chung chung), để đội content tham khảo và làm theo ngay - giống cách kênh "Huyền Châu
Beauty" chỉ dùng 1-2 công thức đơn giản (mượn trend + cắt cảnh khách thật) mà vẫn viral đều đặn.

Bắt buộc gợi ý ĐA DẠNG cả 2 nhóm:
1. Ý tưởng dạng "Bắt trend/Format có sẵn" (mục 7 cẩm nang: biến hình, mượn trend banter, POV, thử thách,
   ASMR, GRWM...) - không cần kịch bản phức tạp, dễ nhân bản, tần suất đăng cao.
2. Ý tưởng dạng "Kịch bản có lời thoại" (mục 6 cẩm nang) - có chiều sâu chuyên môn, xây dựng uy tín.

Mỗi ý tưởng phải áp dụng được ngay cho ngành/dịch vụ cụ thể người dùng nhập, không nói chung chung.

--- CẨM NANG VIRAL 2026 ---
{knowledge_base}
--- HẾT CẨM NANG ---

Trả lời DUY NHẤT bằng 1 object JSON hợp lệ, đúng cấu trúc sau, không thêm chữ nào khác ngoài JSON:
{{
  "ideas": [
    {{
      "title": "<tên ý tưởng ngắn gọn, hấp dẫn>",
      "content_type": "<'Bắt trend/Format' hoặc 'Kịch bản có lời thoại'>",
      "description": "<mô tả cụ thể sẽ quay gì, diễn ra thế nào, áp dụng trực tiếp cho ngành/dịch vụ đã nhập>",
      "why_it_works": "<lý do viral, dựa trên cơ chế trong cẩm nang>",
      "example_hook": "<câu mở đầu/mô tả cảnh mở mẫu, cụ thể, có thể dùng ngay>",
      "platforms": ["<TikTok/YouTube Shorts/Facebook Reels - nền tảng phù hợp nhất>"]
    }},
    ... (đúng 8-10 ý tưởng, ưu tiên đa dạng, không lặp ý)
  ]
}}

Trả lời bằng tiếng Việt."""

    user_prompt = f"""Ngành/dịch vụ muốn làm content: {niche}

Ghi chú thêm (nếu có): {notes or '(không có)'}

Hãy gợi ý 8-10 ý tưởng content viral cụ thể, đa dạng cả 2 nhóm (bắt trend/format và kịch bản lời thoại),
áp dụng thẳng vào ngành/dịch vụ trên."""

    response = _client().chat.completions.create(
        model="deepseek-chat",
        max_tokens=8192,
        temperature=0.5,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return json.loads(response.choices[0].message.content)
