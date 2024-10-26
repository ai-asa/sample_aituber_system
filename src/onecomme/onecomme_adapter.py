# %%
import configparser
import json
import websocket
import logging
import pandas as pd
import os

class OnecommeAdapter:

    def __init__(self,base_dir):
        config = configparser.ConfigParser()
        settings_path = os.path.join(base_dir, 'settings', 'settings.ini')
        config.read(settings_path, encoding='utf-8')
        self.comment_id = config.get('ONECOMME', 'onecomme_id')
        self.onecomme_ws_host = config.get('ONECOMME', 'onecomme_ws_host', fallback='127.0.0.1')
        self.onecomme_ws_port = config.get('ONECOMME', 'onecomme_ws_port', fallback='11180')
        self.WS_URL = 'ws://' + self.onecomme_ws_host + ':'+ self.onecomme_ws_port

    def on_open(self):
        pass

    def on_message(self, queue_data, msg):
        try:
            data = json.loads(msg)
        except json.JSONDecodeError as e:
            logging.info(f"JSON decode error: {e}")
            return
        event_type = data.get("type")

        if event_type == "comments":
            comments = data.get("data", {}).get("comments", [])
            if comments:
                for item in comments:
                    comment_data = item.get("data", {})
                    service_id = item.get("id","")
                    if not service_id == self.comment_id:
                        listener = comment_data.get("displayName", "")
                        comment = comment_data.get("comment", "")
                        queue_data.put((listener,comment))
                        logging.info(f"Listener, Comment: {listener}, {comment}")
                        break
            else:
                logging.info("None")

    def on_error(self, error):
        logging.info(f"Error: {error}")

    def on_close(self):
        logging.info("Connection closed")

    def run_websocket(self, queue_data):
        # websocket setting
        ws = websocket.WebSocketApp(self.WS_URL + "/sub",
                                            on_open=lambda ws:self.on_open(),
                                            on_message=lambda ws,msg:self.on_message(queue_data,msg),
                                            on_error=lambda ws,error:self.on_error(error),
                                            on_close=lambda ws:self.on_close())
        ws.run_forever()

class CollectComment:

    def __init__(self,base_dir):
        settings_path = os.path.join(base_dir, 'settings', 'settings.ini')
        ini_prohibited_path = os.path.join(base_dir, 'ng', '禁止ワード', '禁止ワード.csv')
        ini_ng_path = os.path.join(base_dir, 'ng', 'NG変換ワード', 'NG変換ワード.csv')
        config = configparser.ConfigParser()
        config.read(settings_path, encoding='utf-8')
        self.get_comment_timeout  = int(config.get('ONECOMME', 'get_comment_timeout',fallback=5))
        ng_word_path = config.get('NGWORD', 'prohibited_file_path', fallback=ini_prohibited_path)
        if not ng_word_path:
            ng_word_path = ini_prohibited_path
        conversion_table_path = config.get('NGWORD', 'ngword_file_path', fallback=ini_ng_path)
        if not conversion_table_path:
            conversion_table_path = ini_ng_path
        # NGワードの読み込み
        ng_words_df = pd.read_csv(ng_word_path)
        self.ng_words = set(ng_words_df['禁止ワード'].tolist())
        # 変換テーブルの読み込み
        conversion_table = pd.read_csv(conversion_table_path)
        self.conversion_dict = dict(zip(conversion_table['NGワード'], conversion_table['変換ワード']))

    def get_documents_dir(self):
        # Windows のドキュメントフォルダを取得
        return os.path.join(os.environ['USERPROFILE'], 'Documents')

    def get_base_documents_dir(self):
        # ドキュメント内の AIVTuberSystem フォルダを取得
        return os.path.join(self.get_documents_dir(), 'AIVTuberSystem')

    def apply_conversion(self,text):
        for original, safe in self.conversion_dict.items():
            text = text.replace(original, safe)
        return text

    def collect_queue(self,queue):
        items = []
        try:
            items.append(queue.get(timeout=self.get_comment_timeout))
            while not queue.empty():
                try:
                    item = queue.get_nowait()
                    items.append(item)
                except queue.Empty:
                    break
        except:
            pass

        # NGワードの排除と変換テーブルの適用
        filtered_items = []
        for item in items:
            listener, comment = item
            if not any(ng_word in comment for ng_word in self.ng_words):
                # NGワードを含まないコメントに対して変換テーブルを適用
                converted_comment = self.apply_conversion(comment)
                filtered_items.append((listener, converted_comment))

        return filtered_items

# if __name__ == "__main__":
#     queue_data = multiprocessing.Queue()
#     p = multiprocessing.Process(target=subprocess_onecomme,args=(queue_data,))
#     p.start()
#     #run_subprocess(queue_data)
#     while True:
#         data_list = collect_queue(queue_data)
#         data = data_list[0] if data_list else print("No comment")
#         if data:
#             print(data)
#         time.sleep(5)
# %%
