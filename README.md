# AI Vtuber システム

## イントロダクション
本システムは、生成AIを用いたAI-Vtuberの統合配信システムです。以下の機能を自動で実行するようサポートしています：

- わんコメによる各種配信サイト（YouTube, Twitch, ニコニコ等）の視聴者コメント取得
- Gemini APIまたはOpenAI APIを利用した応答コメント生成
- VoiceVoxによる音声合成と再生
- VTube Studioによるアバターのリップシンク、ホットキーの実行
- OBSの字幕更新
- NGワード機能によるコンテンツフィルタリング

## システム要件

- オペレーティングシステム: Windows 10以上
- プログラミング言語: Python 3.9または3.10を推奨
- RAM: 最低16GB、推奨32GB
- CPU: 第七世代以降のプロセッサを推奨
- ストレージ: 1GB以上の空き容量
- GPU: VRAM 4GB以上を推奨(VOICEVOX GPU版を使用時)

## インストール & セットアップ

### APIキーの取得

[Gemini](https://ai.google.dev/)または[OpenAI](https://openai.com/blog/openai-api)のAPIキーを取得してください。本システムは両方のAPIをサポートしています。

### 必要なアプリケーションのインストール

以下のアプリケーションをダウンロードし、公式サイトに従ってインストールしてください：

- [わんコメ](https://onecomme.com/)
- [OBS](https://obsproject.com/ja/download)
- [VTube Studio](https://store.steampowered.com/app/1325860/VTube_Studio/?l=japanese)
- [VoiceVox](https://voicevox.hiroshiba.jp/)
- [VB-CABLE](https://vb-audio.com/Cable/)

### 仮想環境の構築

1. 本リポジトリをクローンまたはダウンロードします。
2. `Setup.bat`ファイルを実行してください。自動で必要なPythonモジュールがインストールされ、仮想環境が構築されます。

### 設定値リストの取得

1. VoiceVoxのサーバーを起動します。
2. VTube Studioを起動し、使用するモデルに切り替えます。
3. VTube Studioの設定画面を開き、`APIの起動(プラグインを許可)`をONに設定します。
4. `Get_list.bat`ファイルを実行します（VTube Studioの画面に表示されるプラグインを許可してください）。
5. ルートディレクトリに2つのテキストファイル（`sound_device_list.txt`, `hotkey_list.txt`）が生成されたことを確認します。これらの設定値リストは後で使用します。

### VTube Studioの設定

+ **リップシンク設定**

	- VB-CABLEの確認  

		本システムでは、再生される音声を仮想オーディオケーブル(VB-CABLE)を通してVTube Studioに渡すことでリップシンクを行います。前項で取得した「sound_device_list.txt」を開き、「CABLE Output (VB-Audio Virtual Cable)」の記載があることを確認してください  

		(例)sound_device_list.txtの様式  
	  ```
	  45 マイク (HD Pro Webcam C920), Windows WASAPI (2 in, 0 out)
		46 ライン (AVerMedia Live Gamer HD 2), Windows WASAPI (2 in, 0 out)
		47 CABLE Output (VB-Audio Virtual Cable), Windows WASAPI (2 in, 0 out)
		48 ヘッドセット マイク (Wireless Controller), Windows WASAPI (1 in, 0 out)
	  ```

  		※「CABLE Output (VB-Audio Virtual Cable)」が無い場合  
  		- [VB-CABLE](https://vb-audio.com/Cable/)  がインストールされているかを確認し、必要に応じて再インストールしてください  
  		- PCを再起動してください  


	- マイク入力の設定  
	VTube Studioの設定を開き、「リップシンク設定（マイク）」の`マイクを使う`をONにし、`マイク`を「CABLE Output(VB-Adio Virtual Cable)」に設定してください

	- 口の動作設定
	VTube Studioのモデルモーション設定を開き、以下の画像のように「VoiceVolume」から「ParamMouthOpen」を操作するように設定してください(キャラクターモデルによってパラメータ名は異なりますが、入力音声の音量によって口の開閉を操作するような設定を作成すればOKです。また、IN/OUTの値は必要に応じて調整してください)

		![image](https://github.com/ai-asa/aituber-system-for-sivaxo/assets/135745608/5070cd7e-4a05-4464-8d9b-0de395432b23)


+ **Hotkey設定**

	応答セリフとともにVTube Studio上で実行されるホットキーを設定します。本システムでは、Gemini APIもしくはOpenAI APIからの応答が以下の形式で返され、textの音声読み上げと同時にExpressionsに対応するホットキーを実行します。これにより、発話内容にあった表情(アクション)をリアルタイムで実行します。
	```
 	# 様式
	[Expressions]text
	
	# 例
	[neutral]こんにちは。[happy]今日はいい天気だね！
	```
	デフォルトで{pose|happy|sad|surprise|angry|blue|neutral}の7つの表情(アクション)に対応しています。必要に応じて`./src/vtubestudio/hotkeys.py`と`./src/prompt/get_gemini_prompt.py`を書き換えることで変更・削除・追加が可能ですが、出力安定のために最大数の推奨は5~7つです。

	- HotkeyIdの確認  
		前項で取得した、「hotkey_list.txt」を確認し、以下の例のような形式のHotkeyが設定されていることを確認します
		```
      {
            "Hotkey_name": "Smile",
            "type": "ToggleExpression",
            "description": "Toggles an expression",
            "file": "Smile.exp3.json",
            "keyCombination": [],
            "onScreenButtonID": 1,
            "hotkeyID": "2e42a281cc3441e79d0f063dc3fc245d"
        }
	  ```
  		このような記載がない場合、使用するモデルにホットキーが設定されていないため、VTube Studio上でホットキーを作成してください。また、デフォルトの7つの表情(アクション)に対応したホットキーが存在しない場合、同様に作成・変更を行い、再度「hotkey_list.txt」を取得してください

	- hotkeys.pyの書き換え  
		`./src/vtubestudio/hotkeys.py`には、以下のようにデフォルトの7つの表情(アクション)に対応するHotkeyIdが記載されています。「hotkey_list.txt」を参照し、それぞれのExpressionに対応するHotkeyIdに書き換えてください
		```
      pose = "ここを書き換える"(デフォルトは、猫の手.exp3.json)
		happy = "ここを書き換える"(デフォルトは、smile.exp3.json)
		sad = "ここを書き換える"(デフォルトは、涙目.exp3.json)
		surprise = "ここを書き換える"(デフォルトは、驚き.exp3.json)
		angry = "ここを書き換える"(デフォルトは、怒り.exp3.json)
      blue = "ここを書き換える"(デフォルトは、青ざめ1.exp3.json)
		neutral = "ここを書き換える"(デフォルトは、表情を消す)
		```

### OBSの設定  
**字幕設定**  
本システムでは、OBSに以下の名前で設定されたソースを操作します  
以下の名前で`テキスト(GDI+)`ソースを追加してください  
+ Listener
  AIが応答するコメントの発言者名(リスナー名)を表示します  
  コメントが選択された際に、自動でテキスト内容が書き換わります
+ Question
  AIが応答するコメントを表示します  
  コメントが選択された際に、自動でテキスト内容が書き換わります
+ Answer
  AIの応答内容を表示します  
  AIの応答が音声再生される際に自動でテキスト内容が書き換わります

**音声入力設定**  
VOICEVOXで生成された音声を仮想音声ケーブルを通してOBSに渡し、配信上で聞こえるようにします。  
任意の名前の`音声入力キャプチャ`を追加し、デバイスに`CABLE Output (VB-Audio Virtual Cable)`を設定してください

**WebSocketサーバー設定**
WebSocketとは、サーバーとブラウザで双方向通信を低コストで行うための仕組みです。ここでは、本システムからのテキスト等の送信をOBSが受け入れるための設定だと考えてください。

1. OBS画面上部の「ツール」を選択
2. 「WebSocket サーバー設定」を選択
3. 以下の画像のように設定してください。「サーバーポート」、「サーバーパスワード」は任意の値を設定し、環境変数ファイルの設定時に使用するため控えておいてください。(サーバーポートは任意の値を設定できますが、デフォルトの4455のままでも大丈夫です)

### 環境変数ファイルの設定

`.env`ファイルを開き、以下の情報を編集します：

```
OPENAI_API_KEY = your_openai_api_key
GEMINI_API_KEY = your_gemini_api_key
OBS_WS_HOST = 127.0.0.1
OBS_WS_PORT = 4455
OBS_WS_PASSWORD = your_obs_websocket_password
onecomme_WS_URL = ws://127.0.0.1:11180
```

### configファイルの設定

`config.txt`ファイルを開き、必要に応じて以下の設定を変更します：

```
[CONFIG]
aituber_name = AI Vtuberの名前
select_ai_model = 0 または 1 (0: OpenAI, 1: Gemini)
openai_model = gpt-4o-mini
gemini_model = gemini-1.5-flash
voicevox_model_id = 0
call_attempt_limit = 5

[ONECOMME]
comment_id = わんコメの枠ID
get_comment_timeout = 20

[NG]
ng_word_path = ./data/ng/ng_words.csv
conversion_table_path = ./data/ng/conversion_table.csv

[INDEX]
history_limit = 3
```
+ aituber_name  
  AI Vtuberの名前を設定します  
+ select_ai_model  
  使用する生成AIモデルをOpenAI、Geminiから選択します  
+ openai_model  
  OpenAI APIで使用する[AIモデル名](https://platform.openai.com/docs/models)を設定します  
  （Gemini APIを使用する場合は設定の必要はありません）  
+ gemini_model  
  Gemini APIで使用する[AIモデル名](https://ai.google.dev/models)を設定します  
  （OpenAI APIを使用する場合は設定の必要はありません） 
+ voicevox_model_id
  VOICEVOXの使用したいキャラクター音声のIDを指定します。公式のID一覧が無いためリンクを控えますが、「VOICEVOX speaker id」で検索すると出てきます。
+ call_attempt_limit
  生成AIモデル呼び出しエラー発生時、再呼び出しの試行限度回数を設定します
+ comment_id  
  任意の設定です。わんコメ上でAIの応答コメントを取得したい場合は設定してください。わんコメ上で任意の名前の枠を作成し、その枠上で右クリック→「IDをコピー」して取得したIDを記載してください
  
  ![image](https://github.com/ai-asa/aituber-system-for-sivaxo/assets/135745608/617370c8-d80e-458c-aea3-86ea95a2e61f)

+ get_comment_timeout
  新規視聴者コメントの待ち受け時間を指定します。AI Vtuberが自分から話し始めるまでの猶予時間です
+ ng_word_path 
  NGワードを設定するcsvファイルパスを設定します
+ ng_word_path 
  NG語彙とその変換テーブルを設定するcsvファイルパスを設定します
+ history_limit 
  AI Vtuberの発言が何件前までの会話を考慮するかを設定します。多すぎると応答の精度が低下します

### NGワードの設定

1. `./data/ng/ng_words.csv`を開き、フィルタリングしたいNGワードを追加します。
2. `./data/ng/conversion_table.csv`を開き、必要に応じて変換テーブルを設定します。

## システムの起動方法

+ 各ソフトウェアを起動します
  - VTube Studio
  - OBS
  - わんコメ
  - VOICEVOX
+ 配信サイトで配信を開始します
  - わんコメで配信URLに接続します
+ 「Run.bat」を実行
	- Vtube Studio上でプラグインを承認します

起動後は自動で配信コメントを取得し、応答を行います  
停止する際は、コマンドプロンプトのウィンドウを選択した状態で「Ctrl + C」を入力し、動作が停止したのを確認してウィンドウを閉じてください。

## 応用事項