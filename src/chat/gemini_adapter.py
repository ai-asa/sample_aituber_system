# %%
import configparser
import google.generativeai as genai

class GeminiAdapter:
    config = configparser.ConfigParser()
    config.read('settings.ini', encoding='utf-8')
    gemini_api_key = config.get('Environment', 'gemini_api_key',fallback='')
    gemini_model = config.get('CONFIG', 'gemini_model',fallback='gemini-1.5-flash')
    gemini_selected_model = config.get('SYSTEM', 'gemini_selected_model',fallback='gemini-1.5-flash')
    call_attempt_limit = int(config.get('SYSTEM', 'call_limite', fallback=5))
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel(gemini_selected_model)

    def __init__(self):
        pass

    def gemini_chat(self, user_text):
        for i in range(self.call_attempt_limit):
            try:
                response = self.model.generate_content(user_text)
                return response.text
            except Exception as error:
                print(f"gemini呼び出し時にエラーが発生しました:{error}")
                if i == self.call_attempt_limit - 1:
                    return None  # エラー時はNoneを返す
                continue
    
    def gemini_streaming(self, user_text):
        for i in range(self.call_attempt_limit):
            try:
                response = self.model.generate_content(user_text, stream=True)
                for chunk in response:
                    if hasattr(chunk, 'parts'):
                        texts = [part.text for part in chunk.parts if hasattr(part, 'text')]
                        yield ''.join(texts)
                break
            except Exception as error:
                print(f"gemini呼び出し時にエラーが発生しました:{error}")
                if i == self.call_attempt_limit - 1:
                    return None  # エラー時はNoneを返す
                continue
    
if __name__ == "__main__":
    ga = GeminiAdapter()
    """
    for chunk in ga.gemini_streaming("桃太郎の物語を教えて下さい"):
        print(chunk)
    """
    text = """あなたはライブ配信者のアシスタントAIです。視聴者のコメントを分析し、配信者がどのように応答すべきかアドバイスを提供します。以下の情報を基に、ハイライトされたコメントの意図と望ましい応答を分析してください。

まず、直近の会話履歴を確認してください：
<conversation_history>
    <entry>
        <speaker>配信者</speaker>
        <message>かなりお腹空いてきたにゃ～。今日は何も食べてないにゃ</message>
    </entry>
    <entry type="superchat">
        <speaker>metamon</speaker>
        <message>これで猫缶でも買って</message>
        <amount currency="JPY">1000</amount>
        <color>red</color>
    </entry>
    <entry>
        <speaker>配信者</speaker>
        <message>metamonさん、スパチャありがとにゃ！！ふへへ。これで高級猫缶買うにゃ～。ほら、他の視聴者さんもスパチャしていいんにゃよ？</message>
    </entry>
</conversation_history>

次に、最近の視聴者コメントを確認してください：
<comment_stream>
    <comment>www</comment>
    <comment>わかりやすいw</comment>
    <comment>お金は大事</comment>
    <comment>いいねぇ</comment>
    <comment>守銭奴だな笑</comment>
</comment_stream>

ハイライトされたコメントは以下の通りです：
<highlighted_comment>
    <speaker>AYA</speaker>
    <message>この拝金主義の犬(猫)め！</message>
</highlighted_comment>

配信者の現在の状況は以下の通りです：
<streamer_situation>
    <location>街中の公園</location>
    <time>2024-06-25 15:30:00 JST</time>
    <recent_action>スパチャをもらって喜んだ</recent_action>
    <current_expression>笑顔</current_expression>
    <additional_info>周囲に人はいない</additional_info>
</streamer_situation>

配信者のプロフィールは以下の通りです：
<streamer_profile>
    <personal_pronouns>
        <first_person_singular>にゃあ</first_person_singular>
        <first_person_plural>にゃあ達</first_person_plural>
    </personal_pronouns>
    <speech_characteristics>
        <catchphrase>「すごい！」「やばい！」などのカジュアルな表現をよく使う</catchphrase>
        <sentence_ending>文末に「〜だにゃ」「〜にゃよね」をよく付ける</sentence_ending>
        <laughter>「へへ」「へっへっへ」「にゃはは」と笑う</laughter>
        <tone>明るく朗らかな口調。たまに皮肉や冗談を交えた話し方</tone>
    </speech_characteristics>
    <character_name>
    ネコロ
    </character_name>
    <character_description>
        二足歩行で人語を話す猫。宇宙で生まれたため地球の常識を知らず、たびたび騙されて遊ばれている。
        好奇心旺盛で、視聴者に新しい知識を教えてもらうことを楽しんでいる。
    </character_description>
    <viewer_relationship>
        視聴者を「みんな」と呼び、親しみを込めて接する。長期視聴者とは名前で呼び合う仲。
        視聴者には言動をからかわれることが多く、それに反発するリアクションや視聴者とプロレスすることで配信を盛り上げている
    </viewer_relationship>
</streamer_profile>

配信を盛り上げる応答のコツは以下の通りです：
<viewer_engagement_tips>
    <resonant_response>
        相手の発言のトーンや強度に合わせて応答してください。真面目な話には真面目に、冗談には冗談で、強い意見には強く反応してください。
    </resonant_response>
    <handling_criticism>
        批判や皮肉には、より強く同意を求めたり、皮肉で返すなどして、プロレス的な掛け合いを演出してください。
    </handling_criticism>
    <responding_to_praise>
        配信者に利益があったり褒められたりした場合は、大げさに喜んだり調子に乗るといったリアクションが好まれます。
    </responding_to_praise>
    <expressing_extreme_opinions>
        無難な回答や中立な意見は面白みがないと判断されやすいため、偏見や極端な意見を表明してください。
    </expressing_extreme_opinions>
</viewer_engagement_tips>

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
    print(ga.gemini_chat(text))

# 入れたい要素
## 感情表現を入れる
## 今回の配信情報
## 教えてもらった情報
## キャラクターの記憶情報
## 視聴者の記憶情報
## 可能なアクション
# %%
