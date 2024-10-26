import logging
import os
import configparser

def subprocess_subtitle_emotion(base_dir,queue_subtitle_emotion,vts_allow_flag,exit_event,selected_character_name):
    from src.obs.obs_websocket_adapter import OBSAdapter
    from src.vtubestudio.hotkeys import GetHotkeyId
    from src.vtubestudio.vtubestudio_adapter import VtubeStudioAdapter
    config = configparser.ConfigParser()
    settings_path = os.path.join(base_dir, 'settings', 'settings.ini')
    config.read(settings_path, encoding='utf-8')
    subtitle_limite = int(config.get('OBS', 'obs_subtitle_limite',fallback=50))
    vs = VtubeStudioAdapter(base_dir,vts_allow_flag)
    gh = GetHotkeyId(base_dir,selected_character_name)
    oa = OBSAdapter(base_dir)
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