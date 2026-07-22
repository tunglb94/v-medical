import json
from pathlib import Path

from django.conf import settings
from openai import OpenAI

KNOWLEDGE_BASE_PATH = Path(__file__).resolve().parent / 'knowledge' / 'viral_playbook_2026.md'

RESULT_JSON_SHAPE = """{
  "score": <số nguyên 0-100>,
  "verdict": "<kết luận ngắn gọn, thẳng thắn, 1-2 câu>",
  "strengths": ["<điểm mạnh cụ thể>", "..."],
  "weaknesses": ["<điểm yếu cụ thể>", "..."],
  "suggestions": ["<gợi ý chỉnh sửa cụ thể, áp dụng được ngay>", "..."],
  "platform_fit": "<nhận xét mức độ phù hợp với đặc thù nền tảng đã chọn>"
}"""


def _load_knowledge_base():
    return KNOWLEDGE_BASE_PATH.read_text(encoding='utf-8')


def analyze_script(platform_display, hook, script_content, post_caption):
    """
    Gửi kịch bản lên DeepSeek để chấm điểm & nhận xét dựa trên cẩm nang viral 2026.
    Trả về dict theo RESULT_JSON_SHAPE. Raise Exception nếu gọi API lỗi.
    """
    knowledge_base = _load_knowledge_base()

    system_prompt = f"""Bạn là chuyên gia phân tích nội dung mạng xã hội, chấm điểm kịch bản video ngắn dựa
CHÍNH XÁC theo cẩm nang dưới đây - không dùng kiến thức lý thuyết chung chung, không xu nịnh, phải công tâm.
Nếu kịch bản yếu, nói thẳng là yếu và chỉ rõ tại sao. Nếu tốt, chỉ rõ tốt ở điểm nào để người viết học lại
được công thức. Luôn góp ý cụ thể, có thể áp dụng ngay - không nhận xét mơ hồ chung chung.

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

Hãy chấm điểm và nhận xét kịch bản này theo đúng tiêu chí ở mục 5 của cẩm nang."""

    client = OpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

    response = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=4096,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return json.loads(response.choices[0].message.content)
