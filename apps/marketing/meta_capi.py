import hashlib
import requests
import time
import re
import unicodedata
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def remove_accents(input_str):
    if not input_str:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', str(input_str))
    cleaned_str = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return cleaned_str.lower().strip()

def hash_data(data_string):
    """Quy tắc Meta: Lowercase + Strip trước khi băm SHA256"""
    if not data_string:
        return ""
    clean_str = str(data_string).lower().strip()
    return hashlib.sha256(clean_str.encode('utf-8')).hexdigest()

def clean_phone(phone_str):
    """
    Chuẩn hoá SĐT cực kỳ quan trọng: 
    Bỏ mọi ký tự lạ, đổi 0... thành 84...
    Ví dụ: 0912345678 -> 84912345678
    """
    if not phone_str:
        return ""
    # Chỉ giữ lại chữ số
    phone = re.sub(r'\D', '', str(phone_str))
    # Chuyển đầu 0 thành 84
    if phone.startswith('0'):
        phone = '84' + phone[1:]
    # Nếu khách nhập thiếu đầu 0 (ví dụ 912345678), tự bù 84
    elif len(phone) == 9:
        phone = '84' + phone
    return phone

def split_vietnamese_name(full_name):
    if not full_name:
        return "", ""
    name_clean = remove_accents(full_name)
    parts = name_clean.split()
    if len(parts) == 1:
        return parts[0], ""
    first_name = parts[-1]
    last_name = " ".join(parts[:-1])
    return first_name, last_name

def send_purchase_event_to_meta(customer, amount, order_id=None, event_time=None):
    """
    Hàm gửi Purchase tối ưu cho dữ liệu SĐT + Tên khách hàng
    """
    url = f"https://graph.facebook.com/v25.0/{settings.META_DATASET_ID}/events"
    user_data = {}

    # 1. Số điện thoại (ph) - Trường quan trọng nhất của bạn
    hashed_phone = hash_data(clean_phone(customer.phone))
    if hashed_phone:
        user_data["ph"] = [hashed_phone]

    # 2. Họ và Tên (fn, ln) - Bổ trợ để Meta so khớp chéo
    first_name, last_name = split_vietnamese_name(customer.name)
    if first_name:
        user_data["fn"] = [hash_data(first_name)]
    if last_name:
        user_data["ln"] = [hash_data(last_name)]

    # 3. Thành phố (ct) - Nếu CRM có lưu tỉnh/thành
    if customer.city:
        user_data["ct"] = [hash_data(remove_accents(customer.city))]

    # 4. Giới tính (ge)
    if customer.gender:
        gender_val = 'f' if 'FEMALE' in customer.gender.upper() else 'm'
        user_data["ge"] = [hash_data(gender_val)]

    # 5. External ID: Cực kỳ quan trọng để Meta biết đây là khách hàng cũ hay mới
    user_data["external_id"] = [hash_data(str(customer.id))]

    # 6. THÔNG TIN QUAN TRỌNG: fb_lead_id
    # Nếu bạn chạy quảng cáo Form (Lead Ads), CRM cần lưu lại ID này khi khách đổ về.
    # Đây là cách khớp đơn hàng chính xác 100% kể cả khi SĐT khách dùng trên FB khác SĐT để lại.
    fb_lead_id = getattr(customer, 'fb_lead_id', None)
    if fb_lead_id:
        user_data["lead_id"] = fb_lead_id

    # Thời gian sự kiện
    event_time_ts = int(event_time.timestamp()) if event_time and hasattr(event_time, 'timestamp') else int(time.time())

    payload = {
        "data": [{
            "event_name": "Purchase",
            "event_time": event_time_ts,
            "action_source": "system_generated",
            "event_id": str(order_id) if order_id else f"order_{int(time.time())}",
            "user_data": user_data,
            "custom_data": {
                "currency": "VND",
                "value": float(amount)
            }
        }],
        "access_token": settings.META_ACCESS_TOKEN
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"Lỗi gửi CAPI: {e}")
        return None