import hashlib
import requests
import time
import re
import unicodedata
from django.conf import settings

def remove_accents(input_str):
    """Loại bỏ dấu tiếng Việt để Meta dễ dàng so khớp (ví dụ: 'Hồ Chí Minh' -> 'ho chi minh')"""
    if not input_str:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', str(input_str))
    cleaned_str = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return cleaned_str.lower().strip()

def hash_data(data_string):
    """Hàm băm dữ liệu chuẩn SHA256"""
    if not data_string:
        return ""
    return hashlib.sha256(str(data_string).encode('utf-8')).hexdigest()

def clean_phone(phone_str):
    """Chuẩn hoá số điện thoại: Chỉ giữ số, đổi đầu 0 thành 84"""
    if not phone_str:
        return ""
    phone = re.sub(r'\D', '', str(phone_str))
    if phone.startswith('0'):
        phone = '84' + phone[1:]
    return phone

def split_vietnamese_name(full_name):
    """Tách Họ (ln) và Tên (fn) từ tên đầy đủ"""
    if not full_name:
        return "", ""
    name_clean = remove_accents(full_name)
    parts = name_clean.split()
    if len(parts) == 1:
        return parts[0], parts[0]
    
    first_name = parts[-1] # Tên (Ví dụ: 'tung')
    last_name = " ".join(parts[:-1]) # Họ và tên đệm (Ví dụ: 'le ba')
    return first_name, last_name

def send_purchase_event_to_meta(customer, amount, event_time=None):
    """
    Hàm gửi sự kiện Purchase chuẩn 10/10 về Meta
    """
    # Chỉ gửi nếu khách từ Facebook
    if customer.source != 'FACEBOOK':
        return False

    url = f"https://graph.facebook.com/v25.0/{settings.META_DATASET_ID}/events"
    user_data = {}

    # 1. Băm Số điện thoại (ph)
    hashed_phone = hash_data(clean_phone(customer.phone))
    if hashed_phone:
        user_data["ph"] = [hashed_phone]

    # 2. Băm Tên (fn) và Họ (ln)
    first_name, last_name = split_vietnamese_name(customer.name)
    if first_name:
        user_data["fn"] = [hash_data(first_name)]
    if last_name:
        user_data["ln"] = [hash_data(last_name)]

    # 3. Băm Giới tính (ge) - Định dạng: 'f' (Nữ), 'm' (Nam)
    if customer.gender:
        gender_map = {'FEMALE': 'f', 'MALE': 'm'}
        gender_val = gender_map.get(customer.gender)
        if gender_val:
            user_data["ge"] = [hash_data(gender_val)]

    # 4. Băm Ngày sinh (db) - Định dạng: YYYYMMDD
    if customer.dob:
        dob_str = customer.dob.strftime('%Y%m%d')
        user_data["db"] = [hash_data(dob_str)]

    # 5. Băm Tỉnh/Thành phố (ct)
    if customer.city:
        city_clean = remove_accents(customer.city)
        user_data["ct"] = [hash_data(city_clean)]

    # 6. ID khách hàng Facebook (lead_id) - Không cần băm
    if getattr(customer, 'fb_lead_id', None):
        user_data["lead_id"] = customer.fb_lead_id

    # Thời gian sự kiện
    if not event_time:
        event_time = int(time.time())
    else:
        event_time = int(event_time.timestamp())

    payload = {
        "data": [{
            "event_name": "Purchase",
            "event_time": event_time,
            "action_source": "physical_store", # Đổi thành physical_store (Cửa hàng thực tế) sẽ tối ưu hơn cho CRM phòng khám
            "user_data": user_data,
            "custom_data": {
                "currency": "VND",
                "value": float(amount)
            }
        }],
        "access_token": settings.META_ACCESS_TOKEN
    }
    
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Lỗi gửi Meta CAPI: {e}")
        return None