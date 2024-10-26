import os
import configparser
import re
import logging

def subprocess_streaming(base_dir,queue_streaming, queue_playsound,exit_event,selected_character_name):
    from src.voice.voicevox_adapter import VoicevoxAdapter
    va = VoicevoxAdapter()
    config = configparser.ConfigParser()
    characters_path = os.path.join(base_dir, 'characters', 'characters.ini')
    config.read(characters_path, encoding='utf-8')
    characters = []
    voice_tone = "ノーマル"
    for section in config.sections():
        characters.append({
            "name": config[section].get("name", "テスト"),
            "voice": config[section].get("voice", ""),
            "change_tone": config[section].get("change_tone", "False"),
            "first_name": config[section].get("first_name", ""),
            "last_name": config[section].get("last_name", ""),
            "first_name_kana": config[section].get("first_name_kana", ""),
            "last_name_kana": config[section].get("last_name_kana", ""),
        })
    selected_character = next((char for char in characters if char["name"] == selected_character_name), None)
    voice_name = selected_character["voice"]
    change_tone = selected_character["change_tone"]
    _,voice_ids = va.fetch_voice_id()
    voice_id = voice_ids[voice_name]

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
            if isinstance(chunk, dict):
                voice_tone = chunk['voice_tone']
                continue
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
                # content 内に [emotion] 形式が存在する場合、それを削除
                content = re.sub(r'\[[a-z]+\]', '', content).strip()
                conv_text = convert_text(content)
                data, sample_rate = va.get_voice_data(change_tone,voice_tone,conv_text,voice_id)
                queue_data = {"text":content,"data":data,"sample_rate":sample_rate,"emotion":emotion}
                queue_playsound.put(queue_data)
            except Exception as e:
                logging.error("Error in get_voice_data: %s", e)
                logging.info("content: %s, Emotion: %s", content, emotion)
        except Exception as e:
            logging.error("An error occurred: %s", e)
            logging.info("content: %s", content)