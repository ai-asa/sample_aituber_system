import configparser
import os
import time
import logging

def subprocess_main_loop(base_dir,queue_flag,queue_onecomme,queue_streaming,exit_event,selected_character_name,gen_ai_service,gen_ai_model):
    from ai_vtuber_system import AITuberSystem
    from src.onecomme.onecomme_adapter import CollectComment
    cc = CollectComment(base_dir)
    config = configparser.ConfigParser()
    characters_path = os.path.join(base_dir, 'characters', 'characters.ini')
    config.read(characters_path, encoding='utf-8')
    at = AITuberSystem(base_dir,queue_streaming,selected_character_name,gen_ai_service,gen_ai_model)
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
            data_list = cc.collect_queue(queue_onecomme)
            data = data_list[0] if data_list else None
            at.talk_with_comment(data)
        except Exception as e:
            logging.error("An error occurred in subprocess_main_loop: %s", e)