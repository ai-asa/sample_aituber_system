# %%
import json
import requests
import io
import soundfile as sf

class VoicevoxAdapter:
    def __init__(self, host="127.0.0.1", port=50021):
        self.base_url = f"http://{host}:{port}"

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

    def get_voice_data(self, text: str, speaker=1):
        audio_query = self.get_audio_query(text, speaker)
        audio_bytes = self.get_synthesis(audio_query, speaker)
        audio_stream = io.BytesIO(audio_bytes)
        data, sample_rate = sf.read(audio_stream)
        return data, sample_rate
    
    def get_voice_id(self,name):
        id_data = {"四国めたん(ノーマル)":2,
                   "四国めたん(あまあま)":0,
                   "四国めたん(ツンツン)":6,
                   "四国めたん(セクシー)":4,
                   "四国めたん(ささやき)":36,
                   "四国めたん(ヒソヒソ)":37,
                   "ずんだもん(ノーマル)":3,
                   "ずんだもん(あまあま)":1,
                   "ずんだもん(ツンツン)":7,
                   "ずんだもん(セクシー)":5,
                   "ずんだもん(ささやき)":22,
                   "ずんだもん(ひそひそ)":38,
                   "春日部つむぎ(ノーマル)":8,
                   "雨晴はう(ノーマル)":10,
                   "波音リツ(ノーマル)":9,
                   "玄野武宏(ノーマル)":11,
                   "玄野武宏(喜び)":39,
                   "玄野武宏(ツンギレ)":40,
                   "玄野武宏(悲しみ)":41,
                   "白上虎太郎(ふつう)":12,
                   "白上虎太郎(わーい)":32,
                   "白上虎太郎(びくびく)":33,
                   "白上虎太郎(おこ)":34,
                   "白上虎太郎(びえーん)":35,
                   "青山龍星(ノーマル)":13,
                   "冥鳴ひまり(ノーマル)":14,
                   "九州そら(ノーマル)":16,
                   "九州そら(あまあま)":15,
                   "九州そら(ツンツン)":18,
                   "九州そら(セクシー)":17,
                   "九州そら(ささやき)":19,
                   "もち子さん(ノーマル)":20,
                   "剣崎雌雄(ノーマル)":21,
                   "WhiteCUL(ノーマル)":23,
                   "WhiteCUL(たのしい)":24,
                   "WhiteCUL(かなしい)":25,
                   "WhiteCUL(びえーん)":26,
                   "後鬼(人間ver.)":27,
                   "後鬼(ぬいぐるみver.)":28,
                   "No.7(ノーマル)":29,
                   "No.7(アナウンス)":30,
                   "No.7(読み聞かせ)":31,
                   "ちび式じい(ノーマル)":42,
                   "櫻歌ミコ(ノーマル)":43,
                   "櫻歌ミコ(第二形態)":44,
                   "櫻歌ミコ(ロリ)":45,
                   "小夜/SAYO(ノーマル)":46,
                   "ナースロボ＿タイプT(ノーマル)":47,
                   "ナースロボ＿タイプT(楽々)":48,
                   "ナースロボ＿タイプT(恐怖)":49,
                   "ナースロボ＿タイプT(内緒話)":50}
        return id_data[name]


# %%
