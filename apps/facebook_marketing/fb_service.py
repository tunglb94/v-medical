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
        
        # Nếu có hẹn giờ
        if scheduled_time:
            payload['published'] = 'false'
            payload['scheduled_publish_time'] = scheduled_time

        # Logic đăng nhiều ảnh (Multi-photo)
        if files and len(files) > 1:
            media_ids = []
            for f in files:
                # Upload ảnh tạm (chưa publish)
                res = requests.post(f"{self.base_url}/photos", 
                                    data={'access_token': self.token, 'published': 'false'}, 
                                    files={'source': f}).json()
                if "id" in res:
                    media_ids.append({"media_fbid": res["id"]})
            
            payload['message'] = message
            payload['attached_media'] = json.dumps(media_ids)
            return requests.post(f"{self.base_url}/feed", data=payload).json()
        
        # Logic đăng 1 ảnh hoặc Text
        elif files and len(files) == 1:
            payload['caption'] = message
            return requests.post(f"{self.base_url}/photos", data=payload, files={'source': files[0]}).json()

        payload['message'] = message
        return requests.post(f"{self.base_url}/feed", data=payload).json()