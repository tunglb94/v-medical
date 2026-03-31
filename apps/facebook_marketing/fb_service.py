import requests
import json

class FBGraphService:
    def __init__(self, page_id, token):
        self.page_id = page_id
        self.token = token
        self.base_url = f"https://graph.facebook.com/v22.0/{self.page_id}"

    def post_to_facebook(self, message, files=None):
        payload = {'access_token': self.token}
        
        # Xử lý nhiều ảnh
        if files and len(files) > 1:
            media_ids = []
            for f in files:
                res = requests.post(f"{self.base_url}/photos", 
                                    data={'access_token': self.token, 'published': 'false'}, 
                                    files={'source': f}).json()
                if "id" in res:
                    media_ids.append({"media_fbid": res["id"]})
            
            payload['message'] = message
            payload['attached_media'] = json.dumps(media_ids)
            return requests.post(f"{self.base_url}/feed", data=payload).json()
        
        # Xử lý 1 ảnh
        elif files and len(files) == 1:
            payload['caption'] = message
            return requests.post(f"{self.base_url}/photos", data=payload, files={'source': files[0]}).json()

        # Xử lý Text thuần
        payload['message'] = message
        return requests.post(f"{self.base_url}/feed", data=payload).json()