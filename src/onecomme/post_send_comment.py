# %%
import requests

class OnecommePost:
    URL = "http://127.0.0.1:11180/api/"
    def __init__(self):
        self.comment_id = 0
        pass

    def _create_query(self,text:str,id:str,name:str):
        request_data = {
            "service": {
                "id": id,
                "write": True,
                "speech": False,
                "persist": False
            },
            "comment": {
                "id": str(self.comment_id),
                "userId": name,
                "name": name,
                "badges": [],
                "profileImage": "",
                "comment": text,
                "hasGift": False,
                "isOwner": False,
            }
        }
        return request_data
    
    def post_comment(self,text:str,id:str,name:str):
        request_data = self._create_query(text,id,name)
        headers = {'Content-Type': 'application/json'}
        response = requests.post(self.URL + 'comments', json=request_data,headers=headers)
        self.comment_id += 1
        return response
    
if __name__ == "__main__":
    op = OnecommePost()
    text_list = ["よし","これで","どうかな？"]
    channel_id = "fcc0dd03-3e42-40c0-9dd7-ea112c33a1ba"
    name = "Chat_AI"
    import time
    for text in text_list:
        response = op.post_comment(text,channel_id,name)
        print(response.text)
        time.sleep(5)
    
# %%
