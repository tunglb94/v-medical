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
  "suggestions": ["<gợi ý chỉnh sửa nội dung/lời thoại cụ thể, áp dụng được ngay>", "..."],
  "production_tips": [
    {{"aspect": "<đúng tên 1 trong 6 khía cạnh bên dưới>", "suggestion": "<gợi ý cụ thể, áp dụng được ngay cho đúng kịch bản này>"}},
    ... (đủ 6 dòng, đúng thứ tự, đúng tên: {", ".join(PRODUCTION_ASPECTS)})
  ],
  "platform_fit": "<nhận xét mức độ phù hợp với đặc thù nền tảng đã chọn>"
}}"""


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

    system_prompt = f"""Bạn là chuyên gia phân tích nội dung mạng xã hội, chấm điểm kịch bản video ngắn dựa
CHÍNH XÁC theo cẩm nang dưới đây - không dùng kiến thức lý thuyết chung chung, không xu nịnh, phải công tâm.
Nếu kịch bản yếu, nói thẳng là yếu và chỉ rõ tại sao. Nếu tốt, chỉ rõ tốt ở điểm nào để người viết học lại
được công thức. Luôn góp ý cụ thể, có thể áp dụng ngay - không nhận xét mơ hồ chung chung.

Bắt buộc chấm đủ theo checklist 8 tiêu chí ở mục 6 của cẩm nang (giống kiểu Yoast SEO chấm từng mục riêng
với đèn xanh/vàng/đỏ), và góp ý sản xuất chi tiết theo đúng 6 khía cạnh ở mục 5 (visual hook, nhạc nền,
nhịp điệu, sub text, hiệu ứng, góc quay) - áp dụng cụ thể vào chính kịch bản đang chấm, không nói chung chung.

QUAN TRỌNG - chấm sub_score cho từng tiêu chí phải nhất quán, dựa trên bằng chứng cụ thể trong kịch bản,
không cảm tính: nếu 1 tiêu chí có lỗi rõ ràng (VD: hoàn toàn không có CTA, hoàn toàn không có payoff cụ thể)
thì sub_score phải dưới 30, không được chấm cao vì "cảm thấy tạm ổn". status "bad" tương ứng sub_score dưới 40,
"ok" tương ứng 40-69, "good" tương ứng từ 70 trở lên - PHẢI khớp giữa status và sub_score, không được mâu thuẫn.

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

Hãy chấm điểm và nhận xét kịch bản này theo đúng checklist ở mục 6 và góp ý sản xuất theo mục 5 của cẩm nang."""

    client = OpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

    response = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=4096,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    result = json.loads(response.choices[0].message.content)
    result['score'] = compute_score(result.get('checks', []))
    return result
