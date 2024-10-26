import os
import configparser
import shutil
import logging
from src.prompt.get_prompt import GetPrompt

class CharacterManager:
    def __init__(self,base_dir):
        """
        character_pageの各デフォルト値を定義。load_charactersでcharactersの辞書データを取得。
        """
        self.base_dir = base_dir
        self.gp = GetPrompt(base_dir)
        self.config = configparser.ConfigParser()
        images_path = os.path.join(base_dir, 'images')
        self.DEFAULT_IMAGE = os.path.join(images_path, "default_character.png")
        self.DEFAULT_FAMILY_NAME = "サンプル"
        self.DEFAULT_LAST_NAME = "キャラクター"
        self.DEFAULT_FAMILY_KANA_NAME = "さんぷる"
        self.DEFAULT_LAST_KANA_NAME = "きゃらくたー"
        self.DEFAULT_NAME = "名称未設定"
        self.DEFAULT_PROFILE_PROMPT = self.gp.default_profile_prompt()
        self.DEFAULT_SITUATION_PROMPT = self.gp.default_situation_prompt()
        self.DEFAULT_FORMAT_PROMPT = self.gp.default_format_prompt()
        self.DEFAULT_GUIDELINE_PROMPT = self.gp.default_guideline_prompt()
        self.DEFAULT_VOICE_PROMPT = self.gp.default_voice_prompt()
        self.DEFAULT_EXAMPLETOPIC_PROMPT = self.gp.default_exampleTopic_prompt()
        self.DEFAULT_THINKTOPIC_PROMPT = self.gp.default_thinkTopic_prompt()
        self.DEFAULT_PROMPT = "default"
        self.DEFAULT_VOICE_SERVICE = "VOICEVOX"
        self.DEFAULT_VOICE = "1"
        self.DEFAULT_CHANGE_TONE = "False"
        self.DEFAULT_WAIT = "20"
        self.DEFAULT_HAPPY = ""
        self.DEFAULT_SAD = ""
        self.DEFAULT_FUN = ""
        self.DEFAULT_ANGRY = ""
        self.DEFAULT_NEUTRAL = ""
        self.characters = self.load_characters()

    def copy_image(self, source_path, file_name):
        """
        画像ファイルをassetsディレクトリにコピーし、新しいパスを返す。

        Args:
            source_path(str): コピー元の画像ファイルのパス
            file_name(str): コピー先のファイル名
        
        Returns:
            str: コピー先の新しいファイルパス
        
        """
        images_path = os.path.join(self.base_dir, 'images')
        new_file_path = os.path.join(images_path, file_name)
        shutil.copy2(source_path, new_file_path)
        return new_file_path

    def load_characters(self):
        """
        characters.iniがあれば読み込んでcharacters(dict)を返す。なければ1体目のデータを作成して返す。

        Args:
        
        Returns:

        """
        logging.debug("characters.iniファイルからキャラクターデータを読み込み")
        scharacters_path = os.path.join(self.base_dir, 'characters', 'characters.ini')
        if os.path.exists(scharacters_path):
            self.config.read(scharacters_path, encoding='utf-8')
            characters = []
            for section in self.config.sections():
                characters.append({
                    "family_name": self.config[section].get("family_name", self.DEFAULT_FAMILY_NAME),
                    "last_name": self.config[section].get("last_name", self.DEFAULT_LAST_NAME),
                    "family_name_kana": self.config[section].get("family_name_kana", self.DEFAULT_FAMILY_KANA_NAME),
                    "last_name_kana": self.config[section].get("last_name_kana", self.DEFAULT_LAST_KANA_NAME),
                    "name": self.config[section].get("name", self.DEFAULT_NAME),
                    "image": self.config[section].get("image", self.DEFAULT_IMAGE),
                    "profile_prompt": self.config[section].get("profile_prompt", self.DEFAULT_PROFILE_PROMPT),
                    "situation_prompt": self.config[section].get("situation_prompt", self.DEFAULT_SITUATION_PROMPT),
                    "format_prompt": self.config[section].get("format_prompt", self.DEFAULT_FORMAT_PROMPT),
                    "guideline_prompt": self.config[section].get("guideline_prompt", self.DEFAULT_GUIDELINE_PROMPT),
                    "voice_prompt": self.config[section].get("voice_prompt", self.DEFAULT_VOICE_PROMPT),
                    "exampleTopic_prompt": self.config[section].get("exampleTopic_prompt", self.DEFAULT_EXAMPLETOPIC_PROMPT),
                    "thinkTopic_prompt": self.config[section].get("thinkTopic_prompt", self.DEFAULT_THINKTOPIC_PROMPT),
                    "voice_service": self.config[section].get("voice_service", self.DEFAULT_VOICE_SERVICE),
                    "voice": self.config[section].get("voice", self.DEFAULT_VOICE),
                    "change_tone" : self.config[section].get("change_tone", self.DEFAULT_CHANGE_TONE),
                    "wait": self.config[section].get("wait", self.DEFAULT_WAIT),
                    "happy": self.config[section].get("happy", self.DEFAULT_HAPPY),
                    "sad": self.config[section].get("sad", self.DEFAULT_SAD),
                    "fun": self.config[section].get("fun", self.DEFAULT_FUN),
                    "angry": self.config[section].get("angry", self.DEFAULT_ANGRY),
                    "neutral": self.config[section].get("neutral", self.DEFAULT_NEUTRAL),
                })
            logging.debug(f"{len(characters)}個のキャラクターを読み込みました")
            return characters
        logging.debug("characters.iniファイルが見つかりません。デフォルトキャラクターを作成")
        return [{
            "family_name": self.DEFAULT_FAMILY_NAME,
            "last_name": self.DEFAULT_LAST_NAME,
            "family_name_kana": self.DEFAULT_FAMILY_KANA_NAME,
            "last_name_kana": self.DEFAULT_LAST_KANA_NAME,
            "name": self.DEFAULT_NAME,
            "image": self.DEFAULT_IMAGE,
            "profile_prompt": self.DEFAULT_PROFILE_PROMPT,
            "situation_prompt": self.DEFAULT_SITUATION_PROMPT,
            "format_prompt": self.DEFAULT_FORMAT_PROMPT,
            "guideline_prompt": self.DEFAULT_GUIDELINE_PROMPT,
            "voice_prompt" : self.DEFAULT_VOICE_PROMPT,
            "exampleTopic_prompt": self.DEFAULT_EXAMPLETOPIC_PROMPT,
            "thinkTopic_prompt": self.DEFAULT_THINKTOPIC_PROMPT,
            "voice_service": self.DEFAULT_VOICE_SERVICE,
            "voice": self.DEFAULT_VOICE,
            "change_tone" : self.DEFAULT_CHANGE_TONE,
            "wait": self.DEFAULT_WAIT,
            "happy": self.DEFAULT_HAPPY,
            "sad": self.DEFAULT_SAD,
            "fun": self.DEFAULT_FUN,
            "angry": self.DEFAULT_ANGRY,
            "neutral": self.DEFAULT_NEUTRAL,
        }]

    def save_characters(self):
        """
        現在のself.charactersをcharacters.iniに書き出す。

        Args:
        
        Returns:

        """
        logging.debug(f"{len(self.characters)}個のキャラクターを保存中")
        self.config.clear()
        for i, char in enumerate(self.characters):
            section = f"Character{i}"
            self.config[section] = {
                "family_name": char["family_name"],
                "last_name": char["last_name"],
                "family_name_kana": char["family_name_kana"],
                "last_name_kana": char["last_name_kana"],
                "name": char["name"],
                "image": char["image"],
                "profile_prompt": char.get("profile_prompt", ""),
                "situation_prompt": char.get("situation_prompt", ""),
                "format_prompt": char.get("format_prompt", ""),
                "guideline_prompt": char.get("guideline_prompt", ""),
                "voice_prompt": char.get("voice_prompt", ""),
                "exampleTopic_prompt": char.get("exampleTopic_prompt", ""),
                "thinkTopic_prompt": char.get("thinkTopic_prompt", ""),
                "voice_service": char.get("voice_service", ""),
                "voice": char.get("voice", ""),
                "change_tone": char.get("change_tone", ""),
                "wait": char.get("wait", ""),
                "happy": char.get("happy", ""),
                "sad": char.get("sad", ""),
                "fun": char.get("fun", ""),
                "angry": char.get("angry", ""),
                "neutral": char.get("neutral", ""),
            }
        # 書き出し
        characters_path = os.path.join(self.base_dir, 'characters', 'characters.ini')
        with open(characters_path, "w", encoding='utf-8') as f:
            self.config.write(f)
        logging.debug("キャラクターをファイルに保存しました")

    def get_character(self, index):
        """
        self.charactersからインデックス値を指定したキャラクターのデータ(dict)を返す。

        Args:
            index(int): キャラクターのインデックス値
        
        Returns:
            dict: キャラクター設定の辞書データ
        """
        return self.characters[index] if 0 <= index < len(self.characters) else None

    def add_character(self, character_data):
        """
        self.charactersに新たなキャラクターデータ(dict)を追加。characters.iniファイルの保存

        Args:
            character_data(dict): キャラクター設定の辞書データ
        
        Returns:
            
        """
        if not character_data.get("name"):
            character_data["name"] = self.DEFAULT_NAME
        self.characters.append(character_data)
        self.save_characters()

    def update_character(self, index, character_data):
        """
        self.charactersのインデックス値を指定したデータを更新する。characters.iniを保存する

        Args:
            index(int): キャラクターのインデックス値
            character_data(dict): キャラクターの設定データ

        Returns:

        """
        if 0 <= index < len(self.characters):
            self.characters[index] = character_data
            self.save_characters()

    def delete_character(self, index):
        """
        
        """
        logging.debug(f"インデックス値 {index}のキャラクターデータの削除を試みます")
        if 0 <= index < len(self.characters):
            deleted_character = self.characters.pop(index)
            logging.debug(f"削除したキャラクター名: {deleted_character['name']}")
            if deleted_character["image"] != self.DEFAULT_IMAGE:
                try:
                    os.remove(deleted_character["image"])
                    logging.debug(f"削除したイメージ名: {deleted_character['image']}")
                except OSError:
                    logging.debug(f"エラー: イメージを削除できません。 {deleted_character['image']}")
            self.save_characters()
        else:
            logging.debug(f"無効なインデックス値: {index}。削除するキャラクターが存在しません。")
