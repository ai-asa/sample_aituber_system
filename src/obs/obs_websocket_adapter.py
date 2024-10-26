# %%
import obsws_python as obs
import configparser
import os

class OBSAdapter:
    
    def __init__(self,base_dir) -> None:
        config = configparser.ConfigParser()
        settings_path = os.path.join(base_dir, 'settings', 'settings.ini')
        config.read(settings_path, encoding='utf-8')
        self.host = config.get('OBS', 'obs_ws_host',fallback="")
        self.port = config.get('OBS', 'obs_ws_port',fallback="")
        self.password = config.get('OBS', 'obs_ws_password',fallback="")
        self.question = config.get('OBS', 'obs_subtitle_comment',fallback="COMMENT")
        self.answer = config.get('OBS', 'obs_subtitle_ai',fallback="AI")
        self.listener = config.get('OBS', 'obs_subtitle_name',fallback="NAME")
        # 設定されていない場合はエラー
        if(self.password == None or self.host == None or self.port == None):
            raise Exception("OBSの設定がされていません")
        self.ws = obs.ReqClient(host=self.host, port=self.port, password=self.password)
    
    def set_subtitle_question(self, text:str):
        self.ws.set_input_settings(name=self.question, settings={"text":text},overlay=True)

    def set_subtitle_answer(self, text:str):
        self.ws.set_input_settings(name=self.answer, settings={"text":text},overlay=True)
    
    def set_subtitle_listener(self, text:str):
        self.ws.set_input_settings(name=self.listener, settings={"text":text},overlay=True)

# if __name__=='__main__':
#     obsAdapter = OBSAdapter()
#     import random
#     text = "Questionの番号は" + str(random.randint(0,100))
#     obsAdapter.set_subtitle_question(text)
            

# %%
