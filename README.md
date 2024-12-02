# AI VTuber System

AITuberのキャラクター編集、作成、配信システムを統合したシステム及びFletを使用したUIアプリケーション。VTubeStudioと連携してLive2Dアバターのアニメーションを制御します。

## 主な機能

- AIによる会話生成（OpenAI GPT / Google Gemini対応）
- VTubeStudioとの連携によるキャラクターアニメーション
- VOICEVOXを使用した音声合成
- OBS Studioとの連携による字幕表示
- わんコメとの連携によるコメント取得
- 複数キャラクターの管理
- NGワード・禁止ワードの管理

## 必要要件

- Python 3.8以上
- VTubeStudio
- VOICEVOX
- OBS Studio
- わんコメ
- VB-Audio Virtual Cable

## インストール

1. リポジトリをクローン:

    git clone [repository-url]
    cd ai-vtuber-system

2. 必要なパッケージをインストール:

    pip install -r requirements.txt

## 設定

1. 各種APIキーの設定:
- OpenAI APIキー
- Google Gemini APIキー

2. 外部ソフトウェアの設定:
- OBS Studio WebSocket
- わんコメ WebSocket
- VTubeStudio WebSocket

3. キャラクター設定:
- キャラクター情報
- プロンプト設定
- ボイス設定
- ホットキー設定

## 使用方法

1. アプリケーションを起動:

    python main.py

2. キャラクターの作成・編集:
- キャラクタータブでキャラクターを作成
- プロフィール、プロンプト、ボイス等を設定

3. 配信の開始:
- 配信タブで使用するキャラクターを選択
- 「配信開始」ボタンをクリック

## ファイル構成

- `main.py`: アプリケーションのエントリーポイント
- `ai_vtuber_system.py`: AIVTuberシステムのコア機能
- `settings.ini`: システム設定ファイル
- `characters.ini`: キャラクター設定ファイル
- `src/`: ソースコードディレクトリ
  - `chat/`: AI会話機能
  - `obs/`: OBS Studio連携
  - `onecomme/`: わんコメ連携
  - `prompt/`: プロンプト管理
  - `voice/`: 音声合成
  - `vtubestudio/`: VTubeStudio連携
- `ui/`: ユーザーインターフェース

## ライセンス

本プロジェクトは通常非公開です。リポジトリのコピー・公開は禁止します。

## 注意事項

- 各種APIキーは適切に管理してください
- 外部サービスの利用規約を遵守してください
- キャラクター設定時は著作権に注意してください