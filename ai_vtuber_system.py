import configparser
import re
from typing import Generator
from src.prompt.get_prompt import GetPrompt
from src.chat.gemini_adapter import GeminiAdapter
from src.chat.openai_adapter import OpenaiAdapter
from src.onecomme.post_send_comment import OnecommePost
from src.obs.obs_websocket_adapter import OBSAdapter
from src.vtubestudio.hotkeys import GetHotkeyId
from src.voice.play_sound import PlaySound
from src.vtubestudio.vtubestudio_adapter import VtubeStudioAdapter
import pandas as pd
import logging
import time

class AITuberSystem:
    config = configparser.ConfigParser()
    config.read("settings.ini", encoding='utf-8')
    history_limit = int(config.get('SYSTEM', 'history_limit',fallback=6))
    comment_id = config.get('ONECOMME', 'onecomme_id',fallback='test_id')
    ng_word_path = config.get('NGWORD', 'prohibited_file_path', fallback='./data/ng/ng_words.csv')
    conversion_table_path = config.get('NGWORD', 'ngword_file_path', fallback='./data/ng/conversion_table.csv')

    def __init__(self,queue_streaming,selected_character_name,gen_ai_service,gen_ai_model) -> None:
        self.gp = GetPrompt(selected_character_name=selected_character_name)
        self.op = OnecommePost()
        self.oa = OBSAdapter()
        self.ts = TextSplitter()
        self.aituber_name = selected_character_name
        self.listener = ""
        self.comment = ""
        self.clean_response_text = "[neutral]これはテストです![happy]今日の配信も楽しいといいな～♪"
        self.historys_list = []
        self.queue_streaming = queue_streaming
        # NGワードの読み込み
        ng_words_df = pd.read_csv(self.ng_word_path)
        self.ng_words = set(ng_words_df['禁止ワード'].tolist())
        self.max_ng_word_length = max(len(word) for word in self.ng_words)
        # 変換テーブルの読み込み
        self.conversion_table = pd.read_csv(self.conversion_table_path)
        self.conversion_dict = dict(zip(self.conversion_table['NGワード'], self.conversion_table['変換ワード']))
        # AIモデルの選択と初期化
        self.gen_ai_service = gen_ai_service
        if self.gen_ai_service == 'OpenAI API':
            self.am = OpenaiAdapter()
        else:
            self.am = GeminiAdapter()
        self.selected_ai_model = gen_ai_model

    def _contains_ng_word(self, text):
        return any(ng_word in text for ng_word in self.ng_words)

    def _apply_conversion(self, text):
        for original, safe in self.conversion_dict.items():
            text = text.replace(original, safe)
        return text

    def _get_streaming_response(self, prompt):

        if self.gen_ai_service == 'OpenAI API':
            streaming_response = self.am.openai_streaming(prompt)
        else:
            streaming_response = self.am.gemini_streaming(prompt)
        
        self.ts.buffer = ""
        processed_chunk = ""
        for split_text in self.ts.process_stream(streaming_response):
            if split_text:
                print(split_text)
                if self._contains_ng_word(split_text):
                    print("NGワードを含む応答をスキップします")
                    self.queue_streaming.put("END")
                    return None, None
                safe_text = self._apply_conversion(split_text)
                if safe_text:
                    self.queue_streaming.put(safe_text)
                processed_chunk += safe_text
        self.queue_streaming.put("END")
            
        # タグを除去し、テキストをクリーニング
        clean_output_content = re.sub(r'<output>|</output>', '', processed_chunk).strip()
        clean_ai_text = re.sub(r'\[.*?\]', '', clean_output_content)

        return clean_output_content, clean_ai_text

    def _update_historys(self,option="listener"):
        if self.history_limit == 0:
            self.historys_list = ["会話履歴はありません。"]
        else:
            if option == "listener":
                self.historys_list.append((self.listener,self.comment))
            elif option == "assistant":
                self.historys_list.append(("配信者",self.clean_response_text))
            self.historys_list = self.historys_list[-self.history_limit:]

    def talk_with_comment(self,data) -> bool:
        print("コメントを取得を待機中")
        if data != None:
            self.listener, self.comment = data
            print("取得したコメント", self.listener,self.comment)
            prompt = self.gp.get_analyze_prompt(self.historys_list,data)
            if self.gen_ai_service == 'OpenAI API':
                analyze_response = self.am.openai_chat(prompt)
            else:
                analyze_response = self.am.gemini_chat(prompt)
            prompt = self.gp.get_conversation_prompt(analyze_response,self.historys_list,data)
            print(prompt)
            self.oa.set_subtitle_listener(self.listener)
            self._update_historys(option="listener")
        else:
            talk_theme_prompt = self.gp.get_talkTheme_prompt(self.historys_list)
            if self.gen_ai_service == 'OpenAI API':
                talk_theme = self.am.openai_chat(talk_theme_prompt)
            else:
                talk_theme = self.am.gemini_chat(talk_theme_prompt)
            print(talk_theme)
            prompt = self.gp.get_monologue_prompt(self.historys_list,talk_theme)
        response_text,self.clean_response_text = self._get_streaming_response(prompt)
        print("response_text: ", response_text)
        if response_text == None and self.clean_response_text == None:
            return True
        self._update_historys(option="assistant")
        if self.comment:
            self.oa.set_subtitle_question(self.comment)
        self.op.post_comment(self.clean_response_text,self.comment_id,self.aituber_name)
        return True

def subprocess_streaming(queue_streaming, queue_playsound,exit_event,selected_character_name):
    from src.voice.voicevox_adapter import VoicevoxAdapter
    logging.basicConfig(filename='./log/streaming.log',
                    level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
    va = VoicevoxAdapter()
    config = configparser.ConfigParser()
    config.read("characters.ini", encoding='utf-8')
    characters = []
    for section in config.sections():
        characters.append({
            "name": config[section].get("name", "テスト"),
            "voice": config[section].get("voice", ""),
            "first_name": config[section].get("first_name", ""),
            "last_name": config[section].get("last_name", ""),
            "first_name_kana": config[section].get("first_name_kana", ""),
            "last_name_kana": config[section].get("last_name_kana", ""),
        })
    selected_character = next((char for char in characters if char["name"] == selected_character_name), None)
    voicevox_voice = selected_character["voice"]
    # logging.info("voicevox_voice: %s", voicevox_voice)
    voicevox_voice_id = va.get_voice_id(voicevox_voice)
    # logging.info("voicevox_voice_id: %s", voicevox_voice_id)

    def convert_text(text):
        conversion_rules = {
            selected_character["first_name"]: selected_character["first_name_kana"],
            selected_character["last_name"]: selected_character["last_name_kana"]
        }
        for original, converted in conversion_rules.items():
            text = text.replace(original, converted)
        return text

    while not exit_event.is_set():
        try:
            chunk = queue_streaming.get()
            chunk = re.sub(r'<output>|</output>', '', chunk).strip()
            if chunk == "END":
                queue_playsound.put("END")
                continue
            # 文字列の先頭に[...]の形式のタグがあるかチェック
            match = re.match(r'^\[([a-z]+)\](.+)', chunk)
            if match:
                emotion = match.group(1)
                content = match.group(2)
            else:
                emotion = None
                content = chunk
            try:
                print(chunk)
                conv_text = convert_text(content)
                print(conv_text)
                data, sample_rate = va.get_voice_data(conv_text,voicevox_voice_id)
                queue_data = {"text":content,"data":data,"sample_rate":sample_rate,"emotion":emotion}
                queue_playsound.put(queue_data)
            except Exception as e:
                logging.error("Error in get_voice_data: %s", e)
                logging.info("content: %s, Emotion: %s", content, emotion)
        except Exception as e:
            logging.error("An error occurred: %s", e)
            logging.info("content: %s", content)

def subprocess_playsound(queue_playsound,queue_subtitle_emotion,queue_flag,exit_event):
    logging.basicConfig(filename='./log/playsound.log',
                        level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    ps = PlaySound()
    while not exit_event.is_set():
        queue_data = queue_playsound.get()
        try:
            if queue_data == "END":
                queue_flag.put(1)
                queue_subtitle_emotion.put("END")
                continue
            else:
                data = queue_data["data"]
                sample_rate = queue_data["sample_rate"]
                text = queue_data["text"]
                emotion = queue_data["emotion"]
                subtitle_emotion_data = {"text":text,"emotion":emotion}
                queue_subtitle_emotion.put(subtitle_emotion_data)
                ps.play_sound(data,sample_rate)

        except Exception as e:
            # エラーをログに記録
            logging.info("Queue Data: %s", queue_data)
            logging.error("An error occurred in subprocess_playsound: %s", e)

def subprocess_subtitle_emotion(queue_subtitle_emotion,vts_allow_flag,exit_event,selected_character_name):
    logging.basicConfig(filename='./log/subtitle_emotion.log',
                        level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    config = configparser.ConfigParser()
    config.read("settings.ini", encoding='utf-8')
    subtitle_limite = int(config.get('OBS', 'obs_subtitle_limite',fallback=50))
    vs = VtubeStudioAdapter(vts_allow_flag)
    gh = GetHotkeyId(selected_character_name)
    oa = OBSAdapter()
    full_text = ""
    while not exit_event.is_set():
        try:
            queue_data = queue_subtitle_emotion.get()
            if queue_data == "END":
                full_text = ""
                pass
            else:
                text = queue_data["text"]
                if len(full_text) > subtitle_limite:
                    full_text = ""
                full_text += text
                emotion = queue_data["emotion"]
                try:
                    if emotion:
                        hotkeyId = gh.get_hotkeyId(emotion)
                        vs.ensure_connection()
                        vs.send_request(hotkeyId)
                except Exception as e:
                    logging.error("Error in VtubeStudioAdapter: %s", e)
                    logging.info("Emotion: %s, HotkeyId: %s", emotion, hotkeyId)
                oa.set_subtitle_answer(full_text)
        except Exception as e:
            # エラーをログに記録
            logging.error("An error occurred in subprocess_subtitle_emotion: %s", e)

def subprocess_main_loop(queue_flag,queue_onecomme,queue_streaming,exit_event,selected_character_name,gen_ai_service,gen_ai_model):
    from src.onecomme.onecomme_adapter import collect_queue
    logging.basicConfig(filename='./log/loop.log',
                        level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    config = configparser.ConfigParser()
    config.read("characters.ini", encoding='utf-8')
    at = AITuberSystem(queue_streaming,selected_character_name,gen_ai_service,gen_ai_model)
    characters = []
    for section in config.sections():
        name_value = config[section].get("name", "テスト")
        wait_value = config[section].get("wait", "20")
        characters.append({
            "name": name_value if name_value.strip() else "テスト",
            "wait": wait_value if wait_value.strip() else "20",
        })
    selected_character = next((char for char in characters if char["name"] == selected_character_name), None)
    wait_time = int(selected_character["wait"])
    queue_flag.put(1)
    while not exit_event.is_set():
        try:
            queue_flag.get()
            time.sleep(wait_time)
            data_list = collect_queue(queue_onecomme)
            data = data_list[0] if data_list else None
            print(data)
            at.talk_with_comment(data)
        except Exception as e:
            logging.error("An error occurred in subprocess_main_loop: %s", e)

class TextSplitter:
    def __init__(self):
        self.buffer = ""
        self.split_pattern = re.compile(r'([.,、。?!？！]+|\[)')

    def process_stream(self, stream: Generator[str, None, None]) -> Generator[str, None, None]:
        for chunk in stream:
            self.buffer += chunk
            yield from self.split_buffer()

        # Process any remaining text in the buffer
        if self.buffer:
            yield self.buffer.strip()
            self.buffer = ""

    def split_buffer(self) -> Generator[str, None, None]:
        last_end = 0

        for match in self.split_pattern.finditer(self.buffer):
            start, end = match.start(), match.end()
            
            if self.buffer[start] == '[':
                if last_end < start:
                    yield self.buffer[last_end:start].strip()
                last_end = start
            else:  # Punctuation
                yield self.buffer[last_end:end].strip()
                last_end = end

        if last_end < len(self.buffer):
            self.buffer = self.buffer[last_end:]
        else:
            self.buffer = ""