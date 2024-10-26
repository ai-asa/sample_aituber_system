import logging

def subprocess_playsound(queue_playsound,queue_subtitle_emotion,queue_flag,exit_event):
    from src.voice.play_sound import PlaySound
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