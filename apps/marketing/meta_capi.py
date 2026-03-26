import hashlib
import requests
import time
from django.conf import settings

def hash_data(data_string):
    """Băm số điện thoại/email theo chuẩn SHA256 của Meta"""
    if not data_string:
        return ""
    # Chuyển thành chuỗi, xoá khoảng trắng, đưa về chữ thường
    clean_string = str(data_string).strip().lower()
    # Nếu là số điện thoại VN, có thể cần đổi đầu 0 thành 84 (tuỳ data của bạn)
    if clean_string.startswith('0'):
        clean_string = '84' + clean_string[1:]
        
    return hashlib.sha256(clean_string.encode('utf-8')).hexdigest()

def send_purchase_event_to_meta(customer, amount, event_time=None):
    """
    Hàm gửi sự kiện Purchase về Meta
    """
    # Chỉ gửi nếu khách từ Facebook
    if customer.source != 'FACEBOOK':
        return False

    url = f"https://graph.facebook.com/v25.0/{settings.META_DATASET_ID}/events"
    
    # Băm thông tin
    hashed_phone = hash_data(customer.phone)
    
    user_data = {}
    if hashed_phone:
        user_data["ph"] = [hashed_phone]
    # Dựa vào model của bạn không thấy trường email, nếu sau này có thì thêm vào đây:
    # if hasattr(customer, 'email') and customer.email:
    #     user_data["em"] = [hash_data(customer.email)]
    if getattr(customer, 'fb_lead_id', None):
        user_data["lead_id"] = customer.fb_lead_id

    # Thời gian sự kiện (Nếu đồng bộ quá khứ thì lấy giờ cũ, nếu auto thì lấy giờ hiện tại)
    if not event_time:
        event_time = int(time.time())
    else:
        event_time = int(event_time.timestamp())

    payload = {
        "data": [{
            "event_name": "Purchase",
            "event_time": event_time,
            "action_source": "system_generated", # Có thể để 'physical_store' nếu chốt tại phòng khám
            "user_data": user_data,
            "custom_data": {
                "currency": "VND",
                "value": float(amount) # Gửi theo doanh số chốt
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