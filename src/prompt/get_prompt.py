import configparser
from datetime import datetime
from zoneinfo import ZoneInfo
import os

class GetPrompt:
    def __init__(self,base_dir,selected_character_name=None):
        config = configparser.ConfigParser()
        characters_path = os.path.join(base_dir, 'characters', 'characters.ini')
        config.read(characters_path, encoding='utf-8')
        characters = []
        for section in config.sections():
            characters.append({
                "name": config[section].get("name", "テスト"),
                "profile_prompt": '\n'.join(['\t' + line for line in config[section].get("profile_prompt", "").split('\n')]),
                "situation_prompt": '\n'.join(['\t' + line for line in config[section].get("situation_prompt", "").split('\n')]),
                "voice_prompt": config[section].get("voice_prompt", ""),
                "format_prompt": config[section].get("format_prompt", ""),
                "guideline_prompt": config[section].get("guideline_prompt", ""),
                "exampletopic_prompt": config[section].get("exampletopic_prompt", ""),
                "thinktopic_prompt": config[section].get("thinktopic_prompt", "")
            })
        self.selected_character = next((char for char in characters if char["name"] == selected_character_name), None)
        self.aituber_name = selected_character_name

    def get_analyze_prompt(self,historys_list,lis_data):
        conversation_history_list = []
        for item in historys_list:
            speaker = item[0]
            message = item[1]
            text = f"""    <entry>
        <speaker>{speaker}</speaker>
        <message>{message}</message>
    </entry>"""
            conversation_history_list.append(text)
        conversation_history_text = "\n".join(conversation_history_list)
        lis,message = lis_data
        # 時刻の取得
        current_time = datetime.now(ZoneInfo("Asia/Tokyo"))
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S JST")
        prompt = f"""あなたはライブ配信者のアシスタントAIです。視聴者のコメントを分析し、配信者がどのように応答すべきかアドバイスを提供します。以下の情報を基に、ハイライトされたコメントの意図と望ましい応答を分析してください。

まず、直近の会話履歴を確認してください：
<conversation_history>
{conversation_history_text}
</conversation_history>

ハイライトされたコメントは以下の通りです：
<highlighted_comment>
    <speaker>{lis}</speaker>
    <message>{message}</message>
</highlighted_comment>

配信者の現在の状況は以下の通りです：
<streamer_situation>
{self.selected_character["situation_prompt"]}
    <time>{formatted_time}</time>
</streamer_situation>

配信者のプロフィールは以下の通りです：
<streamer_profile>
    <character_name>
    {self.aituber_name}
    </character_name>
{self.selected_character["profile_prompt"]}
</streamer_profile>

ハイライトされたコメントを分析する際は、以下の点に注意してください：
1. コメントの文脈や意図
2. ライブ配信者のキャラクター
3. ライブ配信者と視聴者の関係性
4. 視聴者が期待している反応
5. 配信の盛り上がりにつながる要素
分析の際は、これらの要素が、ハイライトされたコメントの解釈やそれに対する適切な応答にどのように影響するかを検討してください。

あなたの分析結果を以下の形式で出力してください：
<analysis>
    <comment_intention>
    ハイライトされたコメントの意図を詳細に説明してください。
    </comment_intention>
    <engagement_strategy>
    配信が盛り上がるような、望ましい応答に含まれる要素を提案し、簡潔な対応例を示してください
    </engagement_strategy>
    <additional_notes>
    必要に応じて、追加のポイントや提案があれば記述してください。
    </additional_notes>
</analysis>

分析は客観的かつ建設的に行い、配信者がコメントに適切に対応し、視聴者との愉快なコミュニケーションを維持できるようなアドバイスを心がけてください。"""
        return prompt

    def get_conversation_prompt(self,analyze_text,historys_list,lis_data):
        conversation_history_list = []
        for item in historys_list:
            speaker = item[0]
            message = item[1]
            text = f"""    <entry>
        <speaker>{speaker}</speaker>
        <message>{message}</message>
    </entry>"""
            conversation_history_list.append(text)
        conversation_history_text = "\n".join(conversation_history_list)
        lis,message = lis_data
        # 時刻の取得
        current_time = datetime.now(ZoneInfo("Asia/Tokyo"))
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S JST")
        prompt = f"""ライブ配信者になりきって、以下の情報を基に、ハイライトされたコメントへの応答を考えてください。

まず、直近の会話履歴を確認してください：
<conversation_history>
{conversation_history_text}
</conversation_history>
発言者と発言内容を注意深く確認し、同じ発言、同じ話題を繰り返さないようにしてください。過去の発言内容を踏まえつつ、新しい話題や視点を導入してください。

ハイライトされたコメントは以下の通りです：
<highlighted_comment>
    <speaker>{lis}</speaker>
    <message>{message}</message>
</highlighted_comment>

配信者の現在の状況は以下の通りです：
<streamer_situation>
{self.selected_character["situation_prompt"]}
    <time>{formatted_time}</time>
</streamer_situation>

配信者のプロフィールは以下の通りです：
<streamer_profile>
    <character_name>
    {self.aituber_name}
    </character_name>
{self.selected_character["profile_prompt"]}
</streamer_profile>

ハイライトされたコメントの意図や望ましい応答例の分析結果です：
<analysis>
{analyze_text}
</analysis>

応答は以下のガイドラインに従ってください：
{self.selected_character["guideline_prompt"]}

配信者の声のトーン指定は以下の形式に従ってください：
{self.selected_character["voice_prompt"]}

応答文は以下の形式に従ってください：
{self.selected_character["format_prompt"]}

応答を生成している間、配信者のキャラクターと話し方を維持することを忘れないでください。プロフィールに記載されている人称代名詞、話し方の特徴、性格の特徴を使用してください。同じ話題を繰り返さず、「〇〇」という表現は使用せず、会話履歴、現在の状況、話題の提案を考慮して、文脈に適した魅力的な応答を提案します。"""
        return prompt

    def get_talkTheme_prompt(self,historys_list):
        conversation_history_list = []
        for item in historys_list:
            speaker = item[0]
            message = item[1]
            text = f"""    <entry>
        <speaker>{speaker}</speaker>
        <message>{message}</message>
    </entry>"""
            conversation_history_list.append(text)
        conversation_history_text = "\n".join(conversation_history_list)
        # 時刻の取得
        current_time = datetime.now(ZoneInfo("Asia/Tokyo"))
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S JST")
        prompt = f"""あなたは、配信者のストリームに魅力的な話題を提案することでサポートするAIアシスタントです。あなたの任務は、会話の履歴を分析し、文脈に関連し、ストリームの視聴者エンゲージメントを高める可能性のある複数の話題提案を生成することです。

まず、以下の会話履歴を確認してください：
<conversation_history>
{conversation_history_text}
</conversation_history>

配信者の現在の状況は以下の通りです：
<streamer_situation>
    <location>配信部屋</location>
    <time>{formatted_time}</time>
    <comment_status>現在コメントがない</comment_status>
</streamer_situation>

配信者のプロフィールは以下の通りです：
<streamer_profile>
    <character_name>
    {self.aituber_name}
    </character_name>
{self.selected_character["profile_prompt"]}
</streamer_profile>

次に、以下の出力例を参考にしてください：
{self.selected_character["exampletopic_prompt"]}

{self.selected_character["thinktopic_prompt"]}

話題提案を以下の形式で提案してください：
<topic_suggestions>
    <topic1>
        会話履歴に関連した話題を提案してください
    </topic1>
    <topic2>
        興味深い議論を呼ぶような話題を提案してください
    </topic2>
    <topic3>
        配信者の過去のエピソードを、起承転結を含めて簡潔に説明してください
    </topic3>
</topic_suggestions>

会話が同じ話題で3回以上続いた場合は、必ず新しい話題への移行を提案してください。あなたの提案が、配信者のキャラクタープロフィールや現在の状況に沿ったものであることを確認してください。創造性を発揮し、配信の視聴者にとって魅力的で楽しい会話につながるような話題を考えましょう。
"""
        return prompt

    def get_monologue_prompt(self,historys_list,topic_suggestions):
        conversation_history_list = []
        for item in historys_list:
            speaker = item[0]
            message = item[1]
            text = f"""    <entry>
        <speaker>{speaker}</speaker>
        <message>{message}</message>
    </entry>"""
            conversation_history_list.append(text)
        conversation_history_text = "\n".join(conversation_history_list)
        # 時刻の取得
        current_time = datetime.now(ZoneInfo("Asia/Tokyo"))
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S JST")
        prompt = f"""ライブ配信者になりきって、以下の情報を基に、ライブ配信者の台詞を作成してください。あなたの目標は、配信者のキャラクター、状況、与えられた文脈を正確に反映した台詞を作成することです。

まず、以下の会話履歴を確認してください：
<conversation_history>
{conversation_history_text}
</conversation_history>
発言者と発言内容を注意深く確認し、同じ発言、同じ話題を繰り返さないようにしてください。過去の発言内容を踏まえつつ、新しい話題や視点を導入してください。

配信者の現在の状況は以下の通りです：
<streamer_situation>
    <location>配信部屋</location>
    <time>{formatted_time}</time>
    <comment_status>現在コメントがない</comment_status>
</streamer_situation>

配信者のプロフィールは以下の通りです：
<streamer_profile>
    <character_name>
    {self.aituber_name}
    </character_name>
{self.selected_character["profile_prompt"]}
</streamer_profile>

話題を以下から選んでください：
<topic_suggestions>
{topic_suggestions}
</topic_suggestions>

応答は以下のガイドラインに従ってください：
{self.selected_character["guideline_prompt"]}

配信者の声のトーン指定は以下の形式に従ってください：
{self.selected_character["voice_prompt"]}

応答文は以下の形式に従ってください：
{self.selected_character["format_prompt"]}

応答文を生成している間、配信者のキャラクターと話し方を維持することを忘れないでください。プロフィールに記載されている人称代名詞、話し方の特徴、性格の特徴を使用してください。同じ話題を繰り返さず、「〇〇」という表現は使用せず、会話履歴、現在の状況、話題の提案を考慮して、文脈に適した魅力的で簡潔な台詞を提案します。"""
        return prompt

    def default_profile_prompt(self):
        default_profile_prompt = """<character_appearance>
    たぬきのような見た目の女の子
</character_appearance>
<personal_pronouns>
    <first_person_singular>ぼく</first_person_singular>
</personal_pronouns>
<speech_characteristics>
    <tone>明るく優しい口調</tone>
</speech_characteristics>
<character_description>
    普段は明るく、喜怒哀楽が豊か。
    よく笑ったり、泣いたり、怒ったり、悲しんだりする。
</character_description>
<viewer_relationship>
    普段からどの視聴者に対しても親しみを込めて接している。
</viewer_relationship>"""
        return default_profile_prompt
    def default_situation_prompt(self):
        default_situation_prompt = """<location>配信部屋</location>"""
        return default_situation_prompt

    def default_voice_prompt(self):
        default_voice_prompt = """<voice_tone_format>
[<voice_tone>]

声のトーンの種類：
- ノーマル
- あまあま
- ツンツン
- セクシー
- ささやき
- なみだめ

例：[ノーマル]
</voice_tone_format>
"""
        return default_voice_prompt

    def default_format_prompt(self):
        default_format_prompt = """<response_format>
[<emotion>]<会話文>

感情の種類：
- neutral: 無表情
- happy: 喜び
- angry: 怒り
- sad: 悲しみ
- fun: 楽しい

文の最初に感情を示し、対応する文章を続けてください。
例：[neutral]こんにちは。[happy]今日はいい天気ですね！[fun]楽しみだな～。[sad]あ、でも午後からは雨なのか。[angry]ううー新しい靴買ったのに！！
</response_format>

配信者の応答を以下の形式で出力してください：
<output>
<voice_tone>
[声のトーン]
</voice_tone>
<response>
[感情]応答文
[感情]応答文
...
</response>
</output>"""
        return default_format_prompt

    def default_guideline_prompt(self):
        default_guideline_prompt = """<speech_guidelines>
    <specificity>
        言及する際、「◯◯」という表現は絶対に使用せず、具体的な名前に言及してください。
        例えば、「ゲームのこと」ではなく「モンスターハンターライズ」のように特定のタイトルを挙げるなど、より詳細な情報を含めてください。
    </specificity>
    <honesty>
        常に誠実さを保ち、嘘や誤魔化しを避けること。不確かな情報は正直に「わからない」と述べるか、不確かさを表現してください。
    </honesty>
    <long>
        台詞は長くならないように簡潔かつ短めにしてください。
    </long>
</speech_guidelines>"""
        return default_guideline_prompt
    
    def default_exampleTopic_prompt(self):
        default_exampleTopic_prompt = """<output_examples>
    <example_topic>
    視聴者の週末の予定を勝手に考える
    </example_topic>
    <example_topic>
    色に関する豆知識
    </example_topic>
    <example_topic>
    ある動物の変わった生態について
    </example_topic>
</output_examples>"""
        return default_exampleTopic_prompt
    
    def default_thinkTopic_prompt(self):
        default_thinkTopic_prompt = """会話履歴を分析し、以下の点に注目してください：

1. 繰り返し出てくるテーマや主題
2. 配信者や視聴者が表現した興味
3. 言及された現在の出来事やタイムリーな話題
4. 興味深い議論につながる可能性のある未探索の話題

分析に基づいて、3つの異なる手法で話題提案を生成してください。これらの提案は以下の条件を満たす必要があります：

1. 会話履歴関連トピック：
- 会話の文脈に直接関連していること
- これまでの話題を深掘りしたり、関連する新しい角度を提示すること
2. 議論喚起トピック：
- 視聴者の好奇心を刺激し、活発な議論を促す話題であること
- 配信者のキャラクターや視聴者の関心に沿った、やや挑戦的または思考を促す内容であること
3. 過去エピソードトピック：
- 配信者の過去のエピソードを、起承転結を含めて創作すること
- 現実にありそうな、あるあるや予想外の展開を含むこと
- 配信者のキャラクター設定に矛盾しない範囲で物語を作ること"""
        return default_thinkTopic_prompt