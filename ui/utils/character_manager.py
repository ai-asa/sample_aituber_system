import os
import configparser
import shutil
import logging
from src.prompt.get_prompt import GetPrompt

class CharacterManager:
    def __init__(self):
        """
        character_pageの各デフォルト値を定義。load_charactersでcharactersの辞書データを取得。
        """
        self.gp = GetPrompt()
        # assetsディレクトリが存在しない場合は作成
        if not os.path.exists("assets"):
            os.makedirs("assets")
            logging.debug("asssetsディレクトリが存在しないため作成")
        self.config = configparser.ConfigParser()
        self.DEFAULT_IMAGE = os.path.join("assets", "default_character.png")
        self.DEFAULT_FAMILY_NAME = "サンプル"
        self.DEFAULT_LAST_NAME = "キャラクター"
        self.DEFAULT_FAMILY_KANA_NAME = "さんぷる"
        self.DEFAULT_LAST_KANA_NAME = "きゃらくたー"
        self.DEFAULT_NAME = "名称未設定"
        self.DEFAULT_PROFILE_PROMPT = self.gp.default_profile_prompt()
        self.DEFAULT_SITUATION_PROMPT = self.gp.default_situation_prompt()
        self.DEFAULT_FORMAT_PROMPT = self.gp.default_format_prompt()
        self.DEFAULT_GUIDELINE_PROMPT = self.gp.default_guideline_prompt()
        self.DEFAULT_EXAMPLETOPIC_PROMPT = self.gp.default_exampleTopic_prompt()
        self.DEFAULT_THINKTOPIC_PROMPT = self.gp.default_thinkTopic_prompt()
        self.DEFAULT_PROMPT = "default"
        self.DEFAULT_VOICE_SERVICE = "VOICEVOX"
        self.DEFAULT_VOICE = "1"
        self.DEFAULT_WAIT = "20"
        self.DEFAULT_POSE = ""
        self.DEFAULT_HAPPY = ""
        self.DEFAULT_SAD = ""
        self.DEFAULT_SURPRISE = ""
        self.DEFAULT_ANGRY = ""
        self.DEFAULT_BLUE = ""
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
        assets_dir = "assets"
        new_file_path = os.path.join(assets_dir, file_name)
        shutil.copy2(source_path, new_file_path)
        return new_file_path

    def load_characters(self):
        """
        characters.iniがあれば読み込んでcharacters(dict)を返す。なければ1体目のデータを作成して返す。

        Args:
        
        Returns:

        """
        logging.debug("characters.iniファイルからキャラクターデータを読み込み")
        if os.path.exists("characters.ini"):
            self.config.read("characters.ini", encoding='utf-8')
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
                    "exampleTopic_prompt": self.config[section].get("exampleTopic_prompt", self.DEFAULT_EXAMPLETOPIC_PROMPT),
                    "thinkTopic_prompt": self.config[section].get("thinkTopic_prompt", self.DEFAULT_THINKTOPIC_PROMPT),
                    "voice_service": self.config[section].get("voice_service", self.DEFAULT_VOICE_SERVICE),
                    "voice": self.config[section].get("voice", self.DEFAULT_VOICE),
                    "wait": self.config[section].get("wait", self.DEFAULT_WAIT),
                    "pose": self.config[section].get("pose", self.DEFAULT_POSE),
                    "happy": self.config[section].get("happy", self.DEFAULT_HAPPY),
                    "sad": self.config[section].get("sad", self.DEFAULT_SAD),
                    "surprise": self.config[section].get("surprise", self.DEFAULT_SURPRISE),
                    "angry": self.config[section].get("angry", self.DEFAULT_ANGRY),
                    "blue": self.config[section].get("blue", self.DEFAULT_BLUE),
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
            "exampleTopic_prompt": self.DEFAULT_EXAMPLETOPIC_PROMPT,
            "thinkTopic_prompt": self.DEFAULT_THINKTOPIC_PROMPT,
            "voice_service": self.DEFAULT_VOICE_SERVICE,
            "voice": self.DEFAULT_VOICE,
            "wait": self.DEFAULT_WAIT,
            "pose": self.DEFAULT_POSE,
            "happy": self.DEFAULT_HAPPY,
            "sad": self.DEFAULT_SAD,
            "surprise": self.DEFAULT_SURPRISE,
            "angry": self.DEFAULT_ANGRY,
            "blue": self.DEFAULT_BLUE,
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
                "exampleTopic_prompt": char.get("exampleTopic_prompt", ""),
                "thinkTopic_prompt": char.get("thinkTopic_prompt", ""),
                "voice_service": char.get("voice_service", ""),
                "voice": char.get("voice", ""),
                "wait": char.get("wait", ""),
                "pose": char.get("pose", ""),
                "happy": char.get("happy", ""),
                "sad": char.get("sad", ""),
                "surprise": char.get("surprise", ""),
                "angry": char.get("angry", ""),
                "blue": char.get("blue", ""),
                "neutral": char.get("neutral", ""),
            }
        with open("characters.ini", "w", encoding='utf-8') as f:
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
