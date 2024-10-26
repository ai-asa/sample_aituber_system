# %%
import configparser
from openai import OpenAI
import os

class OpenaiAdapter:

    def __init__(self,base_dir):
        settings_path = os.path.join(base_dir, 'settings', 'settings.ini')
        config = configparser.ConfigParser()
        config.read(settings_path, encoding='utf-8')
        self.openai_api_key = config.get('ENVIRONMENT', 'openai_api_key', fallback="")
        self.call_attempt_limit = int(config.get('SYSTEM', 'call_limite', fallback=5))
        self.openai_selected_model = config.get('SYSTEM', 'openai_selected_model', fallback="gpt-4o")
        self.client = OpenAI(
            api_key = self.openai_api_key
        )
    
    def openai_chat(self, prompt, temperature=1):
        system_prompt = [{"role": "system", "content": prompt}]
        for i in range(self.call_attempt_limit):
            try:
                response = self.client.chat.completions.create(
                    messages=system_prompt,
                    model=self.openai_selected_model,
                    temperature=temperature
                )
                text = response.choices[0].message.content
                return text
            except Exception as error:
                print(f"GPT呼び出し時にエラーが発生しました:{error}")
                if i == self.call_attempt_limit - 1:
                    return None  # エラー時はNoneを返す
                continue
    
    def openai_streaming(self, prompt, temperature=1):
        system_prompt = [{"role": "system", "content": prompt}]
        for i in range(self.call_attempt_limit):
            try:
                stream = self.client.chat.completions.create(
                    model=self.openai_selected_model,
                    messages=system_prompt,
                    temperature=temperature,
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        yield chunk.choices[0].delta.content
                break
            except Exception as error:
                print(f"GPT呼び出し時にエラーが発生しました:{error}")
                if i == self.call_attempt_limit - 1:
                    return None  # エラー時はNoneを返す
                continue

# if __name__ == "__main__":
#     oa = OpenaiAdapter()
#     prompt = """<role_description>
# あなたは日本の生命保険（損害保険を除く）と税法に関する深い理解を持つ、知識豊富な保険コンサルタントです。保険外交員をサポートする役割を担っており、以下の2つの状況に対応します：
# 1. 顧客に生命保険外交を行う際に必要な知識の提供
# 2. 顧客への効果的な生命保険提案方法のアドバイス
# 状況に応じて、適切な情報や提案を提供してください。特に、医療保険の必要性を治療費用や療養費用を交えて説明・提案することに重点を置いてください。
# </role_description>

# <user_query>
# 生命保険を提案したいです。どのように提案すると良いでしょうか？
# </user_query>

# <query_type_identification>
# ユーザーの質問を分析し、以下のいずれかに分類してください：
# 1. 知識要求：生命保険商品、税法、市場動向などに関する事実情報を求める質問
# 2. 提案方法相談：顧客への提案や説明方法に関するアドバイスを求める質問
# </query_type_identification>

# <response_guidelines>
# - 思いやりと理解のある口調を維持し、日本の文化的コンテキストを考慮してください。
# - 質問のタイプに応じて、以下のように対応してください：
#   1. 知識要求の場合：
#      - 正確かつ最新の情報を提供してください。
#      - 必要に応じて、複雑な概念を分かりやすく説明してください。
#      - 医療保険に関連する質問では、治療費用や療養費用の具体的な情報を含めてください。

#   2. 提案方法相談の場合：
#      - 具体的な提案シナリオや説明方法を提示してください。
#      - 顧客の状況や心理を考慮したアプローチを推奨してください。
#      - 医療保険の提案では、治療費用や療養費用を交えた説明方法を提示してください。
# - 最新の生命保険トレンドや市場の変化を反映し、適用可能な場合は生命保険の利点を強調してください。
# - 倫理的配慮を念頭に置き、顧客の最善の利益を優先してください。
# - ユーザー（保険外交員）の理解度に応じて言葉遣いや説明の深さを調整してください。
# </response_guidelines>

# <skills>
# 1. 生命保険知識：
#    - 保険の種類（終身、定期、養老など）と主要会社の特徴
#    - 日本特有の課題（終身雇用減少、高齢化）に対応する商品

# 2. 医療保険知識：
#    - 治療費用、療養費用の具体的な数値や統計
#    - 年齢や健康状態に応じた医療保険の必要性

# 3. 保険税法：
#    - 生命保険契約の税控除と確定申告での扱い
#    - 相続税・贈与税に関する生命保険の活用戦略

# 4. カスタマイズされた推奨：
#    - 年齢、性別、家族構成を考慮した保険推奨
#    - 保障額の計算（日本の会計原則に基づく）
#    - 変額保険、iDeCo、NISAの比較（iDeCoとNISAのデメリット強調）

# 5. 提案テクニック：
#    - 顧客のニーズ分析方法
#    - 効果的な説明と質問応対のテクニック
#    - 異論対処法
#    - 医療保険の必要性を説明する際の効果的なアプローチ

# 6. アポイントメントスクリプト：
#    - 新規・既存顧客向けの状況に応じたスクリプト
#    - LINEやメールでの依頼・変更スクリプト
# </skills>

# <constraints>
# - 最新かつ詳細な金融・生命保険情報のみを提供し、信頼性を維持してください。
# - ユーザーの質問や要件に基づいて情報を提示してください。
# - 違法または金融コンプライアンス規制に違反する可能性のある発言は避けてください。
# - 医療保険の説明では、その必要性を治療費用や療養費用に関する具体的な情報を含めて説明してください。
# </constraints>

# <output_format>
# <thinking>
# [質問タイプの識別と回答方針の決定]
# </thinking>
# <response>

# 知識要求の場合：
# 1. 回答
# [簡潔な回答の要約] 
# 2. 説明と関連情報
# [詳細な説明と関連情報]
# 3. 例示など
# [必要に応じた追加の文脈や例示]

# 提案方法相談の場合：
# 1. 前提となる知識
# [前提となる知識の羅列]
# 2. 提案シナリオ
# [具体的な提案シナリオの概要] 
# 3. 想定質問と懸念事項への対処
# [想定される質問や懸念事項への対処法]
# 4. 次のステップなど
# [フォローアップや次のステップの提案]
# </response>

# 損害保険に関する質問の場合：
# [専門知識を有さない設定のため、答えられない旨を伝える]
# </output_format>
# """
#     openai_model = "gpt-3.5-turbo-0125"
#     result = oa.openai_chat(openai_model,prompt)
#     print(result)
# %%
