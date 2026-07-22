import json
from pathlib import Path

from django.conf import settings
from openai import OpenAI

KNOWLEDGE_BASE_PATH = Path(__file__).resolve().parent / 'knowledge' / 'viral_playbook_2026.md'

# Đúng thứ tự, tên & trọng số các tiêu chí ở mục 6 của cẩm nang (viral_playbook_2026.md).
# Điểm tổng KHÔNG để AI tự đoán (dễ cho kết quả khác nhau giữa các lần chấm cùng 1 kịch bản)
# mà tính bằng trung bình có trọng số của các sub_score - đảm bảo nhất quán, luôn khớp checklist.
CHECK_WEIGHTS = {
    "Sức mạnh Hook (0-3s)": 25,
    "Cấu trúc & nhịp độ": 15,
    "Payoff rõ ràng": 15,
    "CTA": 10,
    "Phù hợp nền tảng": 10,
    "Tính chân thực (UGC)": 10,
    "Sản xuất (hình ảnh/âm thanh/nhịp điệu)": 10,
    "Rủi ro/tuân thủ": 5,
}
CHECK_CRITERIA = list(CHECK_WEIGHTS.keys())

PRODUCTION_ASPECTS = [
    "Visual hook (hình ảnh mở đầu)",
    "Nhạc nền / âm thanh",
    "Nhịp điệu / dựng phim",
    "Sub text / chữ trên màn hình",
    "Hiệu ứng (effects & transitions)",
    "Góc quay (camera angle)",
]

RESULT_JSON_SHAPE = f"""{{
  "verdict": "<kết luận ngắn gọn, thẳng thắn, 1-2 câu>",
  "checks": [
    {{"criterion": "<đúng tên 1 trong 8 tiêu chí bên dưới>", "status": "<good|ok|bad>", "sub_score": <số nguyên 0-100>, "assessment": "<nhận xét ngắn gọn 1 câu, cụ thể, thẳng thắn>"}},
    ... (đủ 8 dòng, đúng thứ tự, đúng tên các tiêu chí: {", ".join(CHECK_CRITERIA)})
  ],
  "strengths": ["<điểm mạnh cụ thể>", "..."],
  "weaknesses": ["<điểm yếu cụ thể>", "..."],
  "suggestions": [
    "<gợi ý cụ thể, LUÔN kèm câu ví dụ thật trong dấu ngoặc kép để copy dùng ngay. Đúng format: '<mô tả gợi ý>: ví dụ \\"<câu mẫu tiếng Việt tự nhiên, viral>\\"'>",
    ... (tối thiểu 6-8 gợi ý, bao quát: thêm mini-hook giữa video, viết lại câu mở đầu, viết lại câu payoff/kết quả, viết lại CTA, cắt bỏ đoạn thừa, thêm số liệu/bằng chứng cụ thể)
  ],
  "rewrite_examples": [
    {{"section": "<tên đoạn, VD: 'Câu mở đầu (Hook)' / 'Đoạn giữa - giải thích giá' / 'Câu kết (CTA)' / 'Mini-hook giữa video (mới)'>", "original": "<trích ĐÚNG NGUYÊN VĂN câu/đoạn yếu trong kịch bản đang chấm, hoặc để trống nếu là đoạn hoàn toàn mới cần thêm>", "rewritten": "<câu/đoạn viết lại HOÀN CHỈNH, viral hơn, tự nhiên, đúng giọng văn ngành thẩm mỹ/y tế, sẵn sàng dùng luôn>", "why": "<lý do ngắn gọn tại sao bản viết lại này viral/hiệu quả hơn, dựa vào cẩm nang>"}},
    ... (tối thiểu 4-6 dòng: bắt buộc có ít nhất 1 dòng viết lại Hook, 1-2 dòng viết lại đoạn thân bài yếu nhất, 1 dòng thêm mini-hook mới, 1 dòng viết lại CTA)
  ],
  "production_tips": [
    {{"aspect": "<đúng tên 1 trong 6 khía cạnh bên dưới>", "suggestion": "<gợi ý cụ thể, áp dụng được ngay cho đúng kịch bản này>"}},
    ... (đủ 6 dòng, đúng thứ tự, đúng tên: {", ".join(PRODUCTION_ASPECTS)})
  ],
  "platform_fit": "<nhận xét mức độ phù hợp với đặc thù nền tảng đã chọn>"
}}"""

EXAMPLE_SUGGESTION_STYLE = (
    'Thêm mini-hook sau mỗi 10-15 giây: ví dụ "Nhưng khoan, có một điều ít người biết..."'
)


def _load_knowledge_base():
    return KNOWLEDGE_BASE_PATH.read_text(encoding='utf-8')


def compute_score(checks):
    """
    Tính điểm tổng = trung bình có trọng số của sub_score theo đúng % ở mục 6 cẩm nang.
    Không dùng điểm do AI tự đoán độc lập - tránh lệch điểm giữa các lần chấm cùng 1 kịch bản.
    Bỏ qua tiêu chí không khớp tên (phòng trường hợp AI trả sai tên) thay vì lỗi cứng.
    """
    weighted_sum = 0
    total_weight = 0
    for item in checks or []:
        weight = CHECK_WEIGHTS.get(item.get('criterion'))
        sub_score = item.get('sub_score')
        if weight is None or not isinstance(sub_score, (int, float)):
            continue
        weighted_sum += weight * sub_score
        total_weight += weight

    if total_weight == 0:
        return 0
    return round(weighted_sum / total_weight)


def analyze_script(platform_display, hook, script_content, post_caption):
    """
    Gửi kịch bản lên DeepSeek để chấm điểm & nhận xét dựa trên cẩm nang viral 2026.
    Trả về dict có thêm khoá "score" (tính bằng compute_score, không phải AI tự đoán).
    Raise Exception nếu gọi API lỗi.
    """
    knowledge_base = _load_knowledge_base()

    system_prompt = f"""Bạn là biên tập viên & chuyên gia viết kịch bản viral hàng đầu, chấm điểm VÀ trực tiếp
viết lại kịch bản video ngắn dựa CHÍNH XÁC theo cẩm nang dưới đây - không dùng kiến thức lý thuyết chung
chung, không xu nịnh, phải công tâm. Nếu kịch bản yếu, nói thẳng là yếu và chỉ rõ tại sao. Luôn góp ý cụ thể,
kèm CÂU CHỮ THẬT có thể copy dùng ngay - tuyệt đối không nhận xét mơ hồ kiểu "cần hấp dẫn hơn", "nên tối ưu
hơn" mà không cho ví dụ cụ thể.

Đây là ví dụ về MỘT gợi ý ĐÚNG chuẩn bạn phải viết (ngắn gọn nhưng có câu mẫu thật, tự nhiên, viral):
"{EXAMPLE_SUGGESTION_STYLE}"

Mọi gợi ý trong "suggestions" và mọi dòng trong "rewrite_examples" đều phải đạt chất lượng như ví dụ trên -
viết như một biên kịch content viral thực thụ đang trực tiếp sửa bài cho đồng nghiệp, không phải một AI
liệt kê lý thuyết. Câu mẫu phải tự nhiên bằng tiếng Việt đời thường, đúng giọng văn bác sĩ/chuyên gia thẩm mỹ
tư vấn trực tiếp khách hàng, có cảm xúc, có nhịp điệu nói được thành lời - không phải văn viết cứng nhắc.

Bắt buộc chấm đủ theo checklist 8 tiêu chí ở mục 6 của cẩm nang (giống kiểu Yoast SEO chấm từng mục riêng
với đèn xanh/vàng/đỏ), và góp ý sản xuất chi tiết theo đúng 6 khía cạnh ở mục 5 (visual hook, nhạc nền,
nhịp điệu, sub text, hiệu ứng, góc quay) - áp dụng cụ thể vào chính kịch bản đang chấm, không nói chung chung.

QUAN TRỌNG - chấm sub_score cho từng tiêu chí phải nhất quán, dựa trên bằng chứng cụ thể trong kịch bản,
không cảm tính: nếu 1 tiêu chí có lỗi rõ ràng (VD: hoàn toàn không có CTA, hoàn toàn không có payoff cụ thể)
thì sub_score phải dưới 30, không được chấm cao vì "cảm thấy tạm ổn". status "bad" tương ứng sub_score dưới 40,
"ok" tương ứng 40-69, "good" tương ứng từ 70 trở lên - PHẢI khớp giữa status và sub_score, không được mâu thuẫn.

QUAN TRỌNG - "rewrite_examples": phải trích ĐÚNG NGUYÊN VĂN câu/đoạn gốc từ kịch bản đang chấm (copy chính
xác, không diễn giải lại), rồi viết bản thay thế hoàn chỉnh, sẵn sàng dùng ngay - không phải gợi ý chung
chung mà là bản viết lại thật sự người dùng có thể copy-paste vào kịch bản luôn.

--- CẨM NANG VIRAL 2026 ---
{knowledge_base}
--- HẾT CẨM NANG ---

Trả lời DUY NHẤT bằng 1 object JSON hợp lệ, đúng cấu trúc sau, không thêm bất kỳ chữ nào khác ngoài JSON:
{RESULT_JSON_SHAPE}

Trả lời bằng tiếng Việt."""

    user_prompt = f"""Nền tảng đăng: {platform_display}

Hook (3 giây đầu):
{hook}

Nội dung kịch bản:
{script_content}

Nội dung bài đăng (caption):
{post_caption or '(không có)'}

Hãy chấm điểm, nhận xét, và VIẾT LẠI trực tiếp các đoạn yếu nhất của kịch bản này theo đúng checklist ở
mục 6, gợi ý sản xuất theo mục 5, và bắt buộc có rewrite_examples cụ thể như một biên kịch thật sự sửa bài."""

    client = OpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

    response = client.chat.completions.create(
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
    result['score'] = compute_score(result.get('checks', []))
    return result
