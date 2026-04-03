import requests
import json
import time

class FBGraphService:
    def __init__(self, page_id, token):
        self.page_id = page_id
        self.token = token
        self.base_url = f"https://graph.facebook.com/v22.0/{self.page_id}"

    def post_to_facebook(self, message, files=None, scheduled_time=None):
        """
        scheduled_time: Unix timestamp (phải cách hiện tại ít nhất 10 phút và tối đa 75 ngày)
        """
        payload = {'access_token': self.token}
        
        # Xử lý trạng thái công khai hay hẹn giờ
        if scheduled_time:
            payload['published'] = 'false'
            payload['scheduled_publish_time'] = scheduled_time
        else:
            payload['published'] = 'true'

        if not files:
            payload['message'] = message
            return requests.post(f"{self.base_url}/feed", data=payload).json()

        # Phân loại file tải lên (dựa vào content_type của Django)
        video_files = [f for f in files if f.content_type.startswith('video/')]
        photo_files = [f for f in files if f.content_type.startswith('image/')]

        # Logic 1: Đăng Video (Gửi tới endpoint /videos)
        if video_files:
            v_file = video_files[0] 
            payload['description'] = message # API video dùng 'description' thay vì 'message'
            return requests.post(f"{self.base_url}/videos", data=payload, files={'source': v_file}).json()

        # Logic 2: Đăng nhiều ảnh (Multi-photo)
        elif len(photo_files) > 1:
            media_ids = []
            for f in photo_files:
                # Upload ảnh tạm (buộc phải published=false khi upload mảng ảnh)
                res = requests.post(f"{self.base_url}/photos", 
                                    data={'access_token': self.token, 'published': 'false'}, 
                                    files={'source': f}).json()
                if "id" in res:
                    media_ids.append({"media_fbid": res["id"]})
            
            payload['message'] = message
            payload['attached_media'] = json.dumps(media_ids)
            return requests.post(f"{self.base_url}/feed", data=payload).json()
        
        # Logic 3: Đăng 1 ảnh
        elif len(photo_files) == 1:
            payload['caption'] = message
            return requests.post(f"{self.base_url}/photos", data=payload, files={'source': photo_files[0]}).json()

        # Fallback an toàn
        payload['message'] = message
        return requests.post(f"{self.base_url}/feed", data=payload).json()