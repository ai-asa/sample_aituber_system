# %%
import json
import requests
import io
import soundfile as sf

class VoicevoxAdapter:
    def __init__(self, host="127.0.0.1", port=50021):
        self.base_url = f"http://{host}:{port}"
        self.special_speaker = [2,3,10,11,12,13,16,20,23]

    def get_audio_query(self, text, speaker=1):
        # audio_queryの取得
        query_payload = {"text": text, "speaker": speaker}
        r = requests.post(f"{self.base_url}/audio_query", params=query_payload)
        return r.json()

    def get_synthesis(self, audio_query, speaker=1):
        # 音声合成
        synthesis_payload = {"speaker": speaker}
        r = requests.post(f"{self.base_url}/synthesis", params=synthesis_payload, data=json.dumps(audio_query))
        return r.content

    @staticmethod
    def get_audio_duration(audio_bytes):
        # 音声データの長さを取得
        with io.BytesIO(audio_bytes) as f:
            with sf.SoundFile(f) as sound_file:
                return sound_file.frames / sound_file.samplerate

    def get_voice_data(self, change_tone, voice_tone: str, text: str, speaker=1):
        if change_tone == "True":
            if speaker in self.special_speaker:
                speaker = self._fetch_speaker(speaker,voice_tone)
        audio_query = self.get_audio_query(text, speaker)
        audio_bytes = self.get_synthesis(audio_query, speaker)
        audio_stream = io.BytesIO(audio_bytes)
        data, sample_rate = sf.read(audio_stream)
        return data, sample_rate
    
    def fetch_voice_id(self):
        r = requests.get(f"{self.base_url}/speakers")
        if r.status_code == 200:
            speakers = r.json()
            dropdown_options = []
            id_dict = {}

            for speaker in speakers:
                for style in speaker['styles']:
                    option = f"{speaker['name']}({style['name']})"
                    dropdown_options.append(option)
                    id_dict[option] = style['id']
            return dropdown_options, id_dict
        else:
            print("Failed to retrieve speakers")
            return [], {}

    def _fetch_speaker(self,speaker,voice_tone):
        if speaker == 2:
            if voice_tone == "[あまあま]":
               return 0
            elif voice_tone == "[ツンツン]":
               return 6
            elif voice_tone == "[セクシー]":
                return 4
            elif voice_tone == "[ささやき]":
                return 36
            else:
                return speaker
        elif speaker == 3:
            if voice_tone == "[あまあま]":
               return 1
            elif voice_tone == "[ツンツン]":
               return 7
            elif voice_tone == "[セクシー]":
                return 5
            elif voice_tone == "[ささやき]":
                return 22
            elif voice_tone == "[ヘロヘロ]":
                return 75
            elif voice_tone == "[なみだめ]":
                return 76
            else:
                return speaker
        elif speaker == 11:
            if voice_tone == "[喜び]":
               return 39
            elif voice_tone == "[ツンギレ]":
               return 40
            elif voice_tone == "[悲しみ]":
                return 41
            else:
                return speaker
        elif speaker == 12:
            if voice_tone == "[わーい]":
               return 32
            elif voice_tone == "[びくびく]":
               return 33
            elif voice_tone == "[おこ]":
                return 34
            elif voice_tone == "[びえーん]":
                return 35
            else:
                return speaker
        elif speaker == 13:
            if voice_tone == "[熱血]":
               return 81
            elif voice_tone == "[不機嫌]":
               return 82
            elif voice_tone == "[喜び]":
                return 83
            elif voice_tone == "[しっとり]":
                return 84
            elif voice_tone == "[かなしみ]":
                return 85
            elif voice_tone == "[囁き]":
                return 86
            else:
                return speaker
        elif speaker == 16:
            if voice_tone == "[あまあま]":
               return 15
            elif voice_tone == "[ツンツン]":
               return 18
            elif voice_tone == "[セクシー]":
                return 17
            elif voice_tone == "[ささやき]":
                return 19
            else:
                return speaker
        elif speaker == 20:
            if voice_tone == "[セクシー／あん子]":
                return 66
            elif voice_tone == "[泣き]":
                return 77
            elif voice_tone == "[怒り]":
                return 78
            elif voice_tone == "[喜び]":
                return 79
            elif voice_tone == "[のんびり]":
                return 80
            else:
                return speaker
        elif speaker == 23:
            if voice_tone == "[たのしい]":
                return 24
            elif voice_tone == "[かなしい]":
                return 25
            elif voice_tone == "[びえーん]":
                return 26
            else:
                return speaker

if __name__ == "__main__":
    try:
        va = VoicevoxAdapter()
        _, id_dict = va.fetch_voice_id()
        print(id_dict)
    except Exception as e:
        print(f"An error occurred: {e}")

# %%
