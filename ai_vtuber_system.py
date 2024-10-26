import configparser
import re
import os
from typing import Generator
import pandas as pd

class AITuberSystem:

    def __init__(self,base_dir,queue_streaming,selected_character_name,gen_ai_service,gen_ai_model) -> None:
        from src.obs.obs_websocket_adapter import OBSAdapter
        from src.onecomme.post_send_comment import OnecommePost
        from src.chat.gemini_adapter import GeminiAdapter
        from src.chat.openai_adapter import OpenaiAdapter
        from src.prompt.get_prompt import GetPrompt
        config = configparser.ConfigParser()
        settings_path = os.path.join(base_dir, 'settings', 'settings.ini')
        ini_prohibited_path = os.path.join(base_dir, 'ng', '禁止ワード', '禁止ワード.csv')
        ini_ng_path = os.path.join(base_dir, 'ng', 'NG変換ワード', 'NG変換ワード.csv')
        config.read(settings_path, encoding='utf-8')
        self.history_limit = int(config.get('SYSTEM', 'history_limit',fallback=6))
        self.comment_id = config.get('ONECOMME', 'onecomme_id',fallback='test_id')
        self.ng_word_path = config.get('NGWORD', 'prohibited_file_path', fallback=ini_prohibited_path)
        if not self.ng_word_path:
            self.ng_word_path = ini_prohibited_path
        self.conversion_table_path = config.get('NGWORD', 'ngword_file_path', fallback=ini_ng_path)
        if not self.conversion_table_path:
            self.conversion_table_path = ini_ng_path
        self.gp = GetPrompt(base_dir,selected_character_name=selected_character_name)
        self.op = OnecommePost()
        self.oa = OBSAdapter(base_dir)
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
            self.am = OpenaiAdapter(base_dir)
        else:
            self.am = GeminiAdapter(base_dir)
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
        for output in self.ts.process_stream(streaming_response):
            if isinstance(output, dict):
                # voice_toneをqueue_streamingに送信
                print("ストリーミングの値:",output)
                self.queue_streaming.put(output)
            elif isinstance(output, str):
                split_text = output
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
        clean_output_content = re.sub(r'<.*?>', '', processed_chunk).strip()
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
            self.oa.set_subtitle_listener(self.listener)
            self._update_historys(option="listener")
        else:
            talk_theme_prompt = self.gp.get_talkTheme_prompt(self.historys_list)
            if self.gen_ai_service == 'OpenAI API':
                talk_theme = self.am.openai_chat(talk_theme_prompt)
            else:
                talk_theme = self.am.gemini_chat(talk_theme_prompt)
            prompt = self.gp.get_monologue_prompt(self.historys_list,talk_theme)
        response_text,self.clean_response_text = self._get_streaming_response(prompt)
        if response_text == None and self.clean_response_text == None:
            return True
        self._update_historys(option="assistant")
        if self.comment:
            self.oa.set_subtitle_question(self.comment)
        self.op.post_comment(self.clean_response_text,self.comment_id,self.aituber_name)
        return True

class TextSplitter:
    def __init__(self):
        self.buffer = ""
        self.split_pattern = re.compile(r'([.,、。?!？！]+|\[)')
        self.voice_tone_pattern = re.compile(r'<voice_tone>(.*?)</voice_tone>', re.DOTALL)
        self.response_start_pattern = re.compile(r'<response>')
        self.response_end_pattern = re.compile(r'</response>')
        self.in_response = False  # responseタグ内かどうかのフラグ

    def process_stream(self, stream: Generator[str, None, None]) -> Generator[str, None, None]:
        for chunk in stream:
            self.buffer += chunk

            # voice_toneの処理
            voice_tone_match = self.voice_tone_pattern.search(self.buffer)
            if voice_tone_match:
                voice_tone_content = voice_tone_match.group(1).strip()
                # voice_toneを処理（例えば、別のキューに送信）
                yield {"voice_tone": voice_tone_content}
                # 処理済みの部分をバッファから削除
                self.buffer = self.buffer[voice_tone_match.end():]

            # responseの開始タグを検出
            if not self.in_response:
                response_start_match = self.response_start_pattern.search(self.buffer)
                if response_start_match:
                    self.in_response = True
                    # <response>タグを削除
                    self.buffer = self.buffer[response_start_match.end():]

            # responseの終了タグを検出
            if self.in_response:
                response_end_match = self.response_end_pattern.search(self.buffer)
                if response_end_match:
                    # response終了までのテキストを処理
                    response_text = self.buffer[:response_end_match.start()]
                    # テキストを分割して処理
                    yield from self.split_buffer(response_text)
                    # バッファを更新
                    self.buffer = self.buffer[response_end_match.end():]
                    self.in_response = False
                else:
                    # バッファ内のテキストを可能な限り処理
                    yield from self.split_buffer()
            else:
                # responseタグがまだ出現していないので、待機
                pass

        # ストリームの終了後、バッファに残ったテキストを処理
        if self.buffer:
            if self.in_response:
                yield from self.split_buffer()
            self.buffer = ""

    def split_buffer(self, text=None) -> Generator[str, None, None]:
        if text is not None:
            buffer = text
        else:
            buffer = self.buffer

        last_end = 0
        for match in self.split_pattern.finditer(buffer):
            start, end = match.start(), match.end()
            if buffer[start] == '[':
                if last_end < start:
                    yield buffer[last_end:start].strip()
                last_end = start
            else:  # 句読点
                yield buffer[last_end:end].strip()
                last_end = end

        # 未処理のテキストをバッファに残す
        if text is None:
            if last_end < len(buffer):
                self.buffer = buffer[last_end:]
            else:
                self.buffer = ""
