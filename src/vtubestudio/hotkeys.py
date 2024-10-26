import configparser
import os

"""
デフォルトで、笑い、悲しい、泣き、ショック、怒り、無表情の6つの表情に対応しています。
使用するモデルごとに、対応するキーバインドアクションのID(hotkey ID)を調べ、書き換えてください。
"""
# "Expressions" = "Hotkey ID"
class GetHotkeyId:
    def __init__(self,base_dir,selected_character_name):
        config = configparser.ConfigParser()
        characters_path = os.path.join(base_dir, 'characters', 'characters.ini')
        config.read(characters_path, encoding='utf-8')
        characters = []
        for section in config.sections():
            characters.append({
                "name": config[section].get("name", ""),
                "pose": config[section].get("pose", ""),
                "happy": config[section].get("happy", ""),
                "sad": config[section].get("sad", ""),
                "surprise": config[section].get("surprise", ""),
                "angry": config[section].get("angry", ""),
                "blue": config[section].get("blue", ""),
                "neutral": config[section].get("neutral", "")
            })
        self.selected_character = next((char for char in characters if char["name"] == selected_character_name), None)

    def get_hotkeyId(self,expressions):
        if expressions == "pose":
            return self.selected_character["pose"]
        elif expressions == "happy":
            return self.selected_character["happy"]
        elif expressions == "sad":
            return self.selected_character["sad"]
        elif expressions == "surprise":
            return self.selected_character["surprise"]
        elif expressions == "angry":
            return self.selected_character["angry"]
        elif expressions == "blue":
            return self.selected_character["blue"]
        else:
            return self.selected_character["neutral"]