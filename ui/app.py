import os
import csv
import uuid
import time
import configparser
import flet as ft
import logging
import sounddevice as sd
import multiprocessing

class AIVtuberApp:

    def __init__(self, page: ft.Page):
        from ui.utils.character_manager import CharacterManager
        from src.prompt.get_prompt import GetPrompt
        self.base_dir = self.get_base_documents_dir()
        # log_path = os.path.join(self.base_dir, 'app.log')
        self.config = configparser.ConfigParser()
        self.cm = CharacterManager(self.base_dir)
        self.gp = GetPrompt(self.base_dir)
        self.page = page
        self.page.title = "AI VTuber System"
        self.page.window_width = 1000
        self.page.window_height = 700
        self.page.window_min_width = 800
        self.page.window_min_height = 500
        self.page.window_resizable = True
        self.start_stream_button = None
        self.stop_stream_button = None
        self.selected_index = -1
        self.characters = []
        self.character_containers = []
        self.openai_models = []
        self.gemini_models = []

        self.create_ref()
        self.ng_words_changed = False
        self.prohibited_words_changed = False  # 禁止語彙変更フラグを追加
        self.gen_ai_service_flag = 0
        self.gen_ai_model_changed = False  # 生成AIモデル変更フラグを追加
        self.bottom_sheet = self.create_bottom_sheet()
        self.page.overlay.append(self.bottom_sheet)
        self.page.on_route_change = self.route_change
        self.page.on_view_pop = self.view_pop
        self.load_settings()
        self.load_characters()
        self.create_main_view()

        # プロンプトのインポート
        self.default_profile_prompt = self.gp.default_profile_prompt()
        self.default_situation_prompt = self.gp.default_situation_prompt()
        self.default_format_prompt = self.gp.default_format_prompt()
        self.default_guideline_prompt = self.gp.default_guideline_prompt()
        self.default_voice_prompt = self.gp.default_voice_prompt()
        self.default_exampleTopic_prompt = self.gp.default_exampleTopic_prompt()
        self.default_thinkTopic_prompt = self.gp.default_thinkTopic_prompt()

        # NGワードCSVファイルの自動読み込み
        ini_prohibited_path = os.path.join(self.base_dir, 'ng', '禁止ワード', '禁止ワード.csv')
        ini_ng_path = os.path.join(self.base_dir, 'ng', 'NG変換ワード', 'NG変換ワード.csv')

        ngword_file_path = self.config.get('NGWORD', 'NGWORD_FILE_PATH', fallback=ini_ng_path)
        if not ngword_file_path:
            ngword_file_path = ini_ng_path
        if os.path.exists(ngword_file_path):
            self.ng_words_file_path.value = f"使用するCSVファイル: {ngword_file_path}"
            self.load_ng_words_from_csv(ngword_file_path)
        else:
            # ファイルが存在しない場合のメッセージ表示
            self.ng_words_file_path.value = "ファイルが移動されたか削除されました。"
            self.ng_words_file_path.update()
            # テーブルをクリアし、空の行を追加
            self.ng_words_table.rows.clear()
            self.add_ng_word_row()

        # 禁止語彙CSVファイルの自動読み込み
        prohibited_file_path = self.config.get('NGWORD', 'PROHIBITED_FILE_PATH', fallback=ini_prohibited_path)
        if not prohibited_file_path:
            prohibited_file_path = ini_prohibited_path
        if os.path.exists(prohibited_file_path):
            self.prohibited_words_file_path.value = f"使用するCSVファイル: {prohibited_file_path}"
            self.load_prohibited_words_from_csv(prohibited_file_path)
        else:
            # ファイルが存在しない場合のメッセージ表示
            self.prohibited_words_file_path.value = "ファイルが移動されたか削除されました。"
            self.prohibited_words_file_path.update()
            # テーブルをクリアし、空の行を追加
            self.prohibited_words_table.rows.clear()
            self.add_prohibited_word_row()

        # Update view
        self.update_view()
        self.page.go(self.page.route)

    def create_ref(self):
        self.OPENAI_API_KEY = ft.Ref[ft.TextField]()
        self.GEMINI_API_KEY = ft.Ref[ft.TextField]()
        self.OBS_WS_HOST = ft.Ref[ft.TextField]()
        self.OBS_WS_PORT = ft.Ref[ft.TextField]()
        self.OBS_WS_PASSWORD = ft.Ref[ft.TextField]()
        self.OBS_SUBTITLE_AI = ft.Ref[ft.TextField]()
        self.OBS_SUBTITLE_COMMENT = ft.Ref[ft.TextField]()
        self.OBS_SUBTITLE_NAME = ft.Ref[ft.TextField]()
        self.OBS_SUBTITLE_LIMITE = ft.Ref[ft.TextField]()
        self.ONECOMME_WS_HOST = ft.Ref[ft.TextField]()
        self.ONECOMME_WS_PORT = ft.Ref[ft.TextField]()
        self.ONECOMME_ID = ft.Ref[ft.TextField]()
        self.VTS_WS_HOST = ft.Ref[ft.TextField]()
        self.VTS_WS_PORT = ft.Ref[ft.TextField]()
        self.VIRTUAL_AUDIO_CABLE = ft.Ref[ft.Dropdown]()
        self.HISTORY_LIMITE = ft.Ref[ft.TextField]()
        self.CALL_LIMITE = ft.Ref[ft.TextField]()
        self.GEN_AI_SERVICE = ft.Ref[ft.Dropdown]()
        self.GEN_AI_MODEL = ft.Ref[ft.Dropdown]()
        self.character_row = ft.Ref[ft.Row]()
        self.stream_character_dropdown = ft.Ref[ft.Dropdown]()
        self.selected_character_image = ft.Ref[ft.Image]()
        self.selected_character_name = ft.Ref[ft.Text]()
        self.gen_ai_service = ["OpenAI API", "Gemini API"]
        self.openai_default_models = ["gpt-4o", "gpt-4o-mini"]
        self.gemini_default_models = ["gemini-1.5-flash", "gemini-1.5-pro"]
        self.ng_words_file_path = ft.Text()
        self.prohibited_words_file_path = ft.Text()

    def get_documents_dir(self):
        # Windows のドキュメントフォルダを取得
        return os.path.join(os.environ['USERPROFILE'], 'Documents')
    
    def get_base_documents_dir(self):
        # ドキュメント内の AIVTuberSystem フォルダを取得
        return os.path.join(self.get_documents_dir(), 'AIVTuberSystem')

    def create_bottom_sheet(self):
        return ft.BottomSheet(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Character Details", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                    ft.Image(width=100, height=100, fit=ft.ImageFit.CONTAIN),
                    ft.ElevatedButton("編集", on_click=self.edit_character),
                    ft.ElevatedButton("複製", on_click=self.duplicate_character),
                    ft.ElevatedButton("削除", on_click=self.delete_character, color=ft.colors.RED),
                    ft.ElevatedButton("閉じる", on_click=self.close_bottom_sheet)
                ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20,
                width=400,
            ),
            open=False,
            enable_drag=False,
            on_dismiss=self.on_bottom_sheet_dismiss
        )

    def create_main_view(self):
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="キャラクター",
                    icon=ft.icons.PERSON,
                    content=self.create_character_tab(),
                ),
                ft.Tab(
                    text="設定",
                    icon=ft.icons.SETTINGS,
                    content=self.create_settings_tab(),
                ),
                ft.Tab(
                    text="配信",  # 新しいタブの追加
                    icon=ft.icons.LIVE_TV,  # 適切なアイコンを選択
                    content=self.create_stream_tab(),  # 新しいタブのコンテンツメソッド
                ),
            ],
            expand=1
        )

        self.main_view = ft.View(
            "/",
            [
                self.tabs
            ],
            padding=0,
            bgcolor=ft.colors.BACKGROUND
        )
        self.page.views.append(self.main_view)
        self.page.update()

    def create_settings_tab(self):
        save_button = ft.ElevatedButton("保存", on_click=self.save_all_settings)
        reset_button = ft.ElevatedButton("変更を元に戻す", on_click=self.reset_all_settings)

        settings_tabs = ft.Tabs(
            animation_duration=300,
            tabs=[
                ft.Tab(text="APIキー", icon=ft.icons.KEY, content=self.create_apiKey_settings_tab()),
                ft.Tab(text="外部ソフト", icon=ft.icons.APPS, content=self.create_soft_settings_tab()),
                ft.Tab(text="システム", icon=ft.icons.COMPUTER, content=self.create_system_settings_tab()),
                ft.Tab(text="NGワード", icon=ft.icons.BLOCK, content=self.create_ngword_settings_tab()),
            ],
            expand=1
        )

        return ft.Column(
            [
                settings_tabs,
                ft.Divider(thickness=0.5),
                ft.Container(
                    content=ft.Row(
                        [
                            save_button,
                            reset_button,
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                    padding=ft.padding.symmetric(vertical=10, horizontal=20),
                )
            ],
            expand=True,
            spacing=0,
        )

    def create_character_tab(self):
        character_row = ft.Row(
            ref=self.character_row,
            controls=self.character_containers,
            wrap=True,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=0,
        )

        header_row = ft.Row(
            [
                ft.Text("キャラクター作成", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                ft.ElevatedButton("配信までの流れを確認する", on_click=self.onboarding_flow),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        scrollable_content = ft.Column(
            controls=[character_row],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

        content_column = ft.Column(
            [
                header_row,
                ft.Divider(thickness=1),
                scrollable_content,
            ],
            spacing=10,
            expand=True,
        )

        return ft.Container(
            content=content_column,
            padding=20,
        )

    def onboarding_flow(self, e):
        # オンボーディング処理のプレースホルダー
        pass

    def create_apiKey_settings_tab(self):
        explanation_text = ft.Text(
            "使用する生成AIサービスのAPIキーを入力してください",
            size=16,
            weight=ft.FontWeight.BOLD,
        )

        # テキストフィールドを作成
        self.OPENAI_API_KEY.current = ft.TextField(
            label="OpenAI API キー",
            hint_text="OpenAI APIキーを入力してください",
            value=self.config.get('ENVIRONMENT', 'OPENAI_API_KEY', fallback=''),
            password=True,
            can_reveal_password=True,
            bgcolor=ft.colors.WHITE
        )
        self.GEMINI_API_KEY.current = ft.TextField(
            label="GeminiAPI キー",
            hint_text="Gemini APIキーを入力してください",
            value=self.config.get('ENVIRONMENT', 'GEMINI_API_KEY', fallback=''),
            password=True,
            can_reveal_password=True,
            bgcolor=ft.colors.WHITE
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("APIキー設定", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                    explanation_text,
                    self.OPENAI_API_KEY.current,
                    self.GEMINI_API_KEY.current,
                ],
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=ft.padding.only(left=20, right=20, top=20, bottom=0),
        )

    def create_soft_settings_tab(self):
        # テキストフィールドを作成
        self.OBS_WS_HOST.current = ft.TextField(
            label="サーバーホストURL",
            hint_text="サーバーホストURLを入力(既定:127.0.0.1)",
            value=self.config.get('OBS', 'OBS_WS_HOST', fallback='127.0.0.1'),
            bgcolor=ft.colors.WHITE
        )
        self.OBS_WS_PORT.current = ft.TextField(
            label="サーバーポート",
            hint_text="サーバーポート番号を入力(既定:4455)",
            value=self.config.get('OBS', 'OBS_WS_PORT', fallback='4455'),
            bgcolor=ft.colors.WHITE
        )
        self.OBS_WS_PASSWORD.current = ft.TextField(
            label="サーバーパスワード",
            hint_text="サーバーパスワードを入力",
            value=self.config.get('OBS', 'OBS_WS_PASSWORD', fallback='password'),
            password=True,
            can_reveal_password=True,
            bgcolor=ft.colors.WHITE
        )
        self.OBS_SUBTITLE_AI.current = ft.TextField(
            label="AIアンサー字幕",
            hint_text="AIアンサーを反映するOBSソース名を入力",
            value=self.config.get('OBS', 'OBS_SUBTITLE_AI', fallback='AI'),
            bgcolor=ft.colors.WHITE
        )
        self.OBS_SUBTITLE_COMMENT.current = ft.TextField(
            label="コメント字幕",
            hint_text="視聴者コメントを反映するOBSソース名を入力",
            value=self.config.get('OBS', 'OBS_SUBTITLE_COMMENT', fallback='COMMENT'),
            bgcolor=ft.colors.WHITE
        )
        self.OBS_SUBTITLE_NAME.current = ft.TextField(
            label="コメント主字幕",
            hint_text="視聴者名を反映するOBSソース名を入力",
            value=self.config.get('OBS', 'OBS_SUBTITLE_NAME', fallback='NAME'),
            bgcolor=ft.colors.WHITE
        )
        self.OBS_SUBTITLE_LIMITE.current = ft.TextField(
            label="AIアンサー字幕表示文字数上限",
            hint_text="AIアンサー字幕の表示文字数上限を入力(半角数字)",
            value=self.config.get('OBS', 'OBS_SUBTITLE_LIMITE', fallback='50'),
            bgcolor=ft.colors.WHITE
        )
        self.ONECOMME_WS_HOST.current = ft.TextField(
            label="サーバーホストURL",
            hint_text="サーバーホストURLを入力(既定:127.0.0.1)",
            value=self.config.get('ONECOMME', 'ONECOMME_WS_URL', fallback='127.0.0.1'),
            bgcolor=ft.colors.WHITE
        )
        self.ONECOMME_WS_PORT.current = ft.TextField(
            label="サーバーポート番号",
            hint_text="サーバーポスト番号を入力(既定:11180)",
            value=self.config.get('ONECOMME', 'ONECOMME_WS_PORT', fallback='11180'),
            bgcolor=ft.colors.WHITE
        )
        self.ONECOMME_ID.current = ft.TextField(
            label="チャンネルID",
            hint_text="【任意】チャンネルIDを入力",
            value=self.config.get('ONECOMME', 'ONECOMME_ID', fallback='channel ID'),
            bgcolor=ft.colors.WHITE
        )
        self.VTS_WS_HOST.current = ft.TextField(
            label="サーバーホストURL",
            hint_text="サーバーホストURLを入力(既定:127.0.0.1)",
            value=self.config.get('VTS', 'VTS_WS_HOST', fallback='127.0.0.1'),
            bgcolor=ft.colors.WHITE
        )
        self.VTS_WS_PORT.current = ft.TextField(
            label="サーバーポートURL",
            hint_text="サーバーポートURLを入力(既定:8001)",
            value=self.config.get('VTS', 'VTS_WS_PORT', fallback='8001'),
            bgcolor=ft.colors.WHITE
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("OBSの設定", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                    self.OBS_WS_HOST.current,
                    self.OBS_WS_PORT.current,
                    self.OBS_WS_PASSWORD.current,
                    self.OBS_SUBTITLE_COMMENT.current,
                    self.OBS_SUBTITLE_NAME.current,
                    self.OBS_SUBTITLE_AI.current,
                    self.OBS_SUBTITLE_LIMITE.current,
                    ft.Divider(thickness=1),
                    ft.Text("わんコメの設定", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                    self.ONECOMME_WS_HOST.current,
                    self.ONECOMME_WS_PORT.current,
                    self.ONECOMME_ID.current,
                    ft.Divider(thickness=1),
                    ft.Text("VTSの設定", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                    self.VTS_WS_HOST.current,
                    self.VTS_WS_PORT.current
                ],
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=ft.padding.only(left=20, right=20, top=20, bottom=0),
        )

    def create_system_settings_tab(self):
        sound_settings_text = ft.Text(
            "AIVtuberの音声出力先となる仮想オーディオケーブルを設定してください",
            size=16,
            weight=ft.FontWeight.BOLD,
        )

        refresh_button = ft.ElevatedButton("デバイスを再取得", on_click=self.refresh_devices)

        device_options = self.get_device_options()
        self.VIRTUAL_AUDIO_CABLE.current = ft.Dropdown(
            label="仮想オーディオケーブル",
            options=[ft.dropdown.Option(device_name) for device_name in device_options],
            value=self.config.get('SYSTEM', 'VIRTUAL_AUDIO_CABLE', fallback=device_options[0] if device_options else None),
            bgcolor=ft.colors.WHITE
        )

        memory_settings_text = ft.Text(
            "AI Vtuberの発言が何件前までの会話を考慮するかを設定してください。多すぎると応答の精度が低下します",
            size=16,
            weight=ft.FontWeight.BOLD,
        )

        self.HISTORY_LIMITE.current = ft.TextField(
            label="AIが考慮する会話履歴件数",
            hint_text="半角数字を入力してください(デフォルト値: 3)",
            value=self.config.get('SYSTEM', 'HISTORY_LIMITE', fallback='3'),
            bgcolor=ft.colors.WHITE
        )

        AIcall_settings_text = ft.Text(
            "AI応答エラー時のリトライ上限回数を設定してください",
            size=16,
            weight=ft.FontWeight.BOLD,
        )

        self.CALL_LIMITE.current = ft.TextField(
            label="AI呼出試行回数上限",
            hint_text="半角数字を入力してください(デフォルト値: 5)",
            value=self.config.get('SYSTEM', 'CALL_LIMITE', fallback='5'),
            bgcolor=ft.colors.WHITE
        )

        genAIservice_settings_text = ft.Text(
            "ご利用する生成AIサービスを選択してください(対応するAPIキーの設定が必要です)",
            size=16,
            weight=ft.FontWeight.BOLD,
        )

        genAI_settings_text = ft.Text(
            "ご利用するAIモデル名を選択してください(追加する場合は正確なAIモデル名を入力してください)",
            size=16,
            weight=ft.FontWeight.BOLD,
        )

        self.GEN_AI_SERVICE.current = ft.Dropdown(
            label="使用する生成AIサービス",
            options=[ft.dropdown.Option(service) for service in self.gen_ai_service],
            value=self.config.get('SYSTEM', 'GEN_AI_SERVICE', fallback='OpenAI API'),
            on_change=self.on_gen_ai_service_changed,
            width=300,
            bgcolor=ft.colors.WHITE
        )

        # 初期選択されたサービスに基づいてモデルを設定
        selected_service = self.GEN_AI_SERVICE.current.value
        if selected_service == 'OpenAI API':
            models = self.openai_models
            default_model = self.config.get('SYSTEM', 'OPENAI_SELECTED_MODEL', fallback=models[0] if models else None)
        else:
            models = self.gemini_models
            default_model = self.config.get('SYSTEM', 'GEMINI_SELECTED_MODEL', fallback=models[0] if models else None)

        # 編集可能なドロップダウンメニューを追加
        self.GEN_AI_MODEL.current = ft.Dropdown(
            label="使用するAIモデル名",
            options=[ft.dropdown.Option(model) for model in models],
            value=default_model,
            on_change=self.on_gen_ai_model_changed,
            width=300,
            bgcolor=ft.colors.WHITE
        )

        self.new_gen_ai_option = ft.TextField(hint_text="新しいモデルを追加", width=300, bgcolor=ft.colors.WHITE)
        add_button = ft.ElevatedButton("追加", on_click=self.add_gen_ai_option)
        delete_button = ft.ElevatedButton("削除", on_click=self.delete_gen_ai_option)

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("サウンド設定", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                    sound_settings_text,
                    self.VIRTUAL_AUDIO_CABLE.current,
                    refresh_button,
                    ft.Divider(thickness=1),
                    ft.Text("会話履歴設定", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                    memory_settings_text,
                    self.HISTORY_LIMITE.current,
                    ft.Divider(thickness=1),
                    ft.Text("生成AI設定", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                    AIcall_settings_text,
                    self.CALL_LIMITE.current,
                    genAIservice_settings_text,
                    self.GEN_AI_SERVICE.current,
                    genAI_settings_text,
                    self.GEN_AI_MODEL.current,
                    ft.Row([self.new_gen_ai_option, add_button, delete_button]),
                ],
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=ft.padding.only(left=20, right=20, top=20, bottom=0),
        )

    def on_gen_ai_service_changed(self, e):
        selected_service = self.GEN_AI_SERVICE.current.value
        if selected_service == 'OpenAI API':
            self.gen_ai_service_flag = 0
            models = self.openai_models
        else:
            self.gen_ai_service_flag = 1
            models = self.gemini_models

        # GEN_AI_MODELの選択肢を更新
        self.GEN_AI_MODEL.current.options = [ft.dropdown.Option(model) for model in models]
        # 選択値をリセット
        self.GEN_AI_MODEL.current.value = models[0] if models else None
        self.GEN_AI_MODEL.current.update()

    def on_gen_ai_model_changed(self, e):
        self.gen_ai_model_changed = True

    def add_gen_ai_option(self, e):
        new_model = self.new_gen_ai_option.value.strip()
        if new_model:
            selected_service = self.GEN_AI_SERVICE.current.value
            if selected_service == 'OpenAI API':
                if new_model not in self.openai_models:
                    self.openai_models.append(new_model)
                    self.GEN_AI_MODEL.current.options.append(ft.dropdown.Option(new_model))
            else:
                if new_model not in self.gemini_models:
                    self.gemini_models.append(new_model)
                    self.GEN_AI_MODEL.current.options.append(ft.dropdown.Option(new_model))
            self.new_gen_ai_option.value = ""
            self.update_gen_ai_model_list()
            self.gen_ai_model_changed = True

    def delete_gen_ai_option(self, e):
        selected_option = self.GEN_AI_MODEL.current.value
        selected_service = self.GEN_AI_SERVICE.current.value
        if selected_service == 'OpenAI API':
            default_models = self.openai_default_models
            models = self.openai_models
        else:
            default_models = self.gemini_default_models
            models = self.gemini_models

        if selected_option and selected_option not in default_models:
            if selected_option in models:
                models.remove(selected_option)
                # Dropdownのオプションを再生成
                self.GEN_AI_MODEL.current.options = [ft.dropdown.Option(model) for model in models]
                # 新しい選択値を設定
                self.GEN_AI_MODEL.current.value = models[0] if models else None
                self.update_gen_ai_model_list()
                self.gen_ai_model_changed = True

    def update_gen_ai_model_list(self):
        self.GEN_AI_MODEL.current.update()
        self.new_gen_ai_option.update()

    def create_ngword_settings_tab(self):
        explanation_text = ft.Text(
            "NGワードの変換設定を行います。不適切な文字列を変換するために使用します。",
            size=16,
            weight=ft.FontWeight.BOLD,
        )

        select_ngword_file_button = ft.ElevatedButton("使用するCSVファイルを選択", on_click=self.select_ng_words_file)

        self.ng_words_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("NGワード")),
                ft.DataColumn(ft.Text("変換ワード")),
                ft.DataColumn(ft.Text("選択")),
            ],
            rows=[],
        )

        # 新規CSV保存ボタン
        save_as_new_ngword_csv_button = ft.ElevatedButton(
            "新規CSVとして保存",
            icon=ft.icons.SAVE,
            on_click=self.open_save_csv_dialog
        )

        # 選択行を削除ボタンを追加
        delete_selected_ngword_button = ft.ElevatedButton(
            "選択行を削除",
            icon=ft.icons.DELETE,
            on_click=self.delete_selected_ng_words
        )

        # DataTableを固定高さのContainerにラップしてスクロールを有効にする
        ng_words_table_container = ft.Container(
            height=200,  # 必要に応じて高さを調整
            border=ft.border.all(1, ft.colors.GREY),
            border_radius=ft.border_radius.all(5),
            padding=10,
            bgcolor=ft.colors.WHITE,
            content=ft.Column(
                controls=[self.ng_words_table],
                scroll=ft.ScrollMode.AUTO,
            )
        )

        # --- 禁止語彙設定セクションの追加 ---

        prohibited_explanation_text = ft.Text(
            "禁止ワードの設定を行います。禁止ワードを含むコメントは無視し、AIの発言にも含めないようにします。",
            size=16,
            weight=ft.FontWeight.BOLD,
        )

        select_prohibited_file_button = ft.ElevatedButton("使用するCSVファイルを選択", on_click=self.select_prohibited_words_file)

        self.prohibited_words_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("禁止ワード")),
                ft.DataColumn(ft.Text("選択")),
            ],
            rows=[],
        )

        # 新規CSV保存ボタン
        save_as_new_prohibited_csv_button = ft.ElevatedButton(
            "新規CSVとして保存",
            icon=ft.icons.SAVE,
            on_click=self.open_save_prohibited_csv_dialog
        )

        # 選択行を削除ボタンを追加
        delete_selected_prohibited_button = ft.ElevatedButton(
            "選択行を削除",
            icon=ft.icons.DELETE,
            on_click=self.delete_selected_prohibited_words
        )

        # DataTableを固定高さのContainerにラップしてスクロールを有効にする
        prohibited_words_table_container = ft.Container(
            height=200,  # 必要に応じて高さを調整
            border=ft.border.all(1, ft.colors.GREY),
            border_radius=ft.border_radius.all(5),
            padding=10,
            bgcolor=ft.colors.WHITE,
            content=ft.Column(
                controls=[self.prohibited_words_table],
                scroll=ft.ScrollMode.AUTO,
            )
        )

        return ft.Container(
            content=ft.ListView(
                controls=[
                    # --- NGワード設定セクション ---
                    ft.Text("NGワード変換設定", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                    explanation_text,
                    self.ng_words_file_path,
                    select_ngword_file_button,
                    ng_words_table_container,
                    ft.Row(
                        [
                            save_as_new_ngword_csv_button,
                            delete_selected_ngword_button,
                        ],
                        alignment=ft.MainAxisAlignment.END,
                        spacing=10,
                    ),
                    ft.Divider(thickness=1),
                    # --- 禁止語彙設定セクション ---
                    ft.Text("禁止ワード設定", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                    prohibited_explanation_text,
                    self.prohibited_words_file_path,
                    select_prohibited_file_button,
                    prohibited_words_table_container,
                    ft.Row(
                        [
                            save_as_new_prohibited_csv_button,
                            delete_selected_prohibited_button,
                        ],
                        alignment=ft.MainAxisAlignment.END,
                        spacing=10,
                    ),
                ],
                spacing=10,
                expand=True,
            ),
            padding=ft.padding.only(left=20, right=20, top=20, bottom=0),
        )
    
    def create_stream_tab(self):
        # 配信するキャラクターのプルダウン
        self.stream_character_dropdown.current = ft.Dropdown(
            label="配信するキャラクター",
            options=[ft.dropdown.Option(char["name"]) for char in self.characters],
            value=self.characters[0]["name"] if self.characters else None,
            on_change=self.on_stream_character_selected,
            width=400,
            bgcolor=ft.colors.WHITE
        )

        # 選択されたキャラクターの画像と名前を表示
        self.selected_character_image.current = ft.Image(
            width=350,
            height=350,
            fit=ft.ImageFit.CONTAIN,
            src=self.characters[0]["image"] if self.characters else ""
        )
        self.selected_character_name.current = ft.Text(
            self.characters[0]["name"] if self.characters else "",
            size=24,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER
        )

        # 配信開始ボタン
        self.start_stream_button = ft.ElevatedButton(
            text="配信開始",
            icon=ft.icons.PLAY_ARROW,
            on_click=self.start_stream,
            disabled=False
        )

        # 配信停止ボタン
        self.stop_stream_button = ft.ElevatedButton(
            text="配信停止",
            icon=ft.icons.STOP,
            on_click=self.stop_stream,
            disabled=True
        )

        # 配信ステータス表示
        self.stream_status = ft.Text("設定を完了し配信を開始してください。", color=ft.colors.BLACK)

        # 配信ボタンを並べるRow
        stream_buttons_row = ft.Row(
            [
                self.start_stream_button,
                self.stop_stream_button,
            ],
            spacing=10
        )

        # 画面左側を並べるColumn
        left_column = ft.Column(
            [
                self.stream_character_dropdown.current,
                stream_buttons_row,
                self.stream_status,
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.START,
        )

        # キャラクター選択と表示を並べるRow
        character_selection_row = ft.Row(
            [
                ft.Container(
                    content=ft.Column([
                        self.selected_character_image.current,
                        self.selected_character_name.current
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=20
        )

        # 左側とキャラクター画像を並べるRow
        main_content = ft.Row(
            [
                left_column,
                character_selection_row,
            ],
            spacing=150
        )

        # 配信タブのコンテンツを構築
        stream_content = ft.Column(
            [
                ft.Text("配信設定", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                main_content
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.START,
        )

        return ft.Container(
            content=stream_content,
            padding=20,
        )

    def on_stream_character_selected(self, e):
        selected_name = self.stream_character_dropdown.current.value
        selected_character = next((char for char in self.characters if char["name"] == selected_name), None)
        if selected_character:
            self.selected_character_image.current.src = selected_character["image"]
            self.selected_character_name.current.value = selected_character["name"]
        else:
            self.selected_character_image.current.src = ""
            self.selected_character_name.current.value = ""
        self.selected_character_image.current.update()
        self.selected_character_name.current.update()

    def start_stream(self, e=None):
        from sub.subprocess_main_loop import subprocess_main_loop
        from sub.subprocess_playsound import subprocess_playsound
        from sub.subprocess_streaming import subprocess_streaming
        from sub.subprocess_subtitle_emotion import subprocess_subtitle_emotion
        from sub.subprocess_onecomme import subprocess_onecomme
        self.start_stream_button.disabled = True
        self.stop_stream_button.disabled = False
        self.page.update()
        selected_name = self.stream_character_dropdown.current.value
        if not selected_name:
            self.show_error_message("配信するキャラクターを選択してください。")
            return

        # 配信プロセスの定義
        self.queue_onecomme = multiprocessing.Queue()
        self.queue_streaming = multiprocessing.Queue()
        self.queue_playsound = multiprocessing.Queue()
        self.queue_subtitle_emotion = multiprocessing.Queue()
        self.queue_flag = multiprocessing.Queue()
        self.vts_allow_flag = multiprocessing.Queue()
        self.exit_event = multiprocessing.Event()
        base_dir = self.get_base_documents_dir()
        self.p_1 = multiprocessing.Process(target=subprocess_onecomme,args=(base_dir,self.queue_onecomme,))
        self.p_2 = multiprocessing.Process(target=subprocess_streaming,args=(base_dir,self.queue_streaming,self.queue_playsound,self.exit_event,selected_name))
        self.p_3 = multiprocessing.Process(target=subprocess_playsound,args=(self.queue_playsound,self.queue_subtitle_emotion,self.queue_flag,self.exit_event))
        self.p_4 = multiprocessing.Process(target=subprocess_subtitle_emotion,args=(base_dir,self.queue_subtitle_emotion,self.vts_allow_flag,self.exit_event,selected_name))
        self.p_5 = multiprocessing.Process(target=subprocess_main_loop,args=(base_dir,self.queue_flag,self.queue_onecomme,self.queue_streaming,self.exit_event,selected_name,self.GEN_AI_SERVICE.current.value,self.GEN_AI_MODEL.current.value))
        # 配信開始ロジック
        self.p_1.start()
        self.p_2.start()
        self.p_3.start()
        self.p_4.start()
        self.p_5.start()
        self.stream_status.value = f'配信を開始します。VTSにて"AIVsystem_Plugin"を許可してください。'
        self.stream_status.color = ft.colors.RED
        self.stream_status.update()
        allow_flag = self.vts_allow_flag.get()
        if allow_flag == 1:
            self.stream_status.value = "VTSプラグインが拒否されました。配信を停止しています。"
            self.stream_status.color = ft.colors.RED
            self.stream_status.update()
            self.exit_event.set()
            time.sleep(5)
            self.p_1.terminate()
            self.p_2.terminate()
            self.p_3.terminate()
            self.p_4.terminate()
            self.p_5.terminate()
            self.stream_status.value = "配信を開始してください。"
            self.stream_status.color = ft.colors.BLACK
            self.stream_status.update()
            self.start_stream_button.disabled = False
            self.stop_stream_button.disabled = True
            self.show_error_message("配信が中止されました。")
        else:
            self.stream_status.value = f"配信中: {selected_name}"
            self.stream_status.color = ft.colors.GREEN
            self.stream_status.update()
            self.show_success_message(f"配信を開始しました。キャラクター: {selected_name}")

    def stop_stream(self, e=None):
        self.start_stream_button.disabled = False
        self.stop_stream_button.disabled = True
        self.page.update()
        # 配信停止のロジックをここに実装
        self.p_1.terminate()
        self.exit_event.set()
        self.stream_status.value = "配信を停止しています。"
        self.stream_status.color = ft.colors.RED
        self.stream_status.update()
        time.sleep(5)
        self.p_2.terminate()
        self.p_3.terminate()
        self.p_4.terminate()
        self.p_5.terminate()
        self.stream_status.value = "配信を開始してください。"
        self.stream_status.color = ft.colors.BLACK
        self.stream_status.update()
        self.show_success_message("配信を停止しました。")

    def select_ng_words_file(self, e):
        def file_picker_result(e: ft.FilePickerResultEvent):
            if e.files:
                file_path = e.files[0].path
                self.ng_words_file_path.value = f"使用するCSVファイル: {file_path}"
                self.ng_words_file_path.update()
                self.load_ng_words_from_csv(file_path)
                self.ng_words_changed = True

        file_picker = ft.FilePicker(on_result=file_picker_result)
        self.page.overlay.append(file_picker)
        self.page.update()
        file_picker.pick_files(
            allowed_extensions=["csv"],
            allow_multiple=False,
        )

    def open_save_csv_dialog(self, e):
        # ファイルパス入力用のRefを作成
        self.save_csv_textfield_ref = ft.Ref[ft.TextField]()

        # カスタムダイアログを作成してファイルパスを入力してもらう
        self.save_csv_dialog = ft.AlertDialog(
            title=ft.Text("新規CSVとして保存"),
            content=ft.Column([
                ft.Text("保存先のファイルパスを入力してください（例: C:/Users/Username/Documents/new_ng_words.csv）"),
                ft.TextField(
                    ref=self.save_csv_textfield_ref,
                    hint_text="ファイルパスを入力",
                    autofocus=True,
                    expand=True
                ),
            ]),
            actions=[
                ft.TextButton("保存", on_click=self.save_as_new_csv_callback_dialog),
                ft.TextButton("キャンセル", on_click=lambda _: self.close_save_csv_dialog())
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = self.save_csv_dialog
        self.save_csv_dialog.open = True
        self.page.update()

    def close_save_csv_dialog(self):
        self.save_csv_dialog.open = False
        self.page.update()

    def save_as_new_csv_callback_dialog(self, e):
        # Refを使用してTextFieldにアクセス
        text_field = self.save_csv_textfield_ref.current
        if isinstance(text_field, ft.TextField):
            file_path = text_field.value.strip()
        else:
            self.show_error_message("ファイルパスの取得に失敗しました。")
            return

        if not file_path.endswith(".csv"):
            self.show_error_message("ファイル名は .csv で終わる必要があります。")
            return

        # ファイルパスのエスケープシーケンスを避けるためにスラッシュを使用
        file_path = file_path.replace("\\", "/")

        try:
            with open(file_path, "w", encoding="utf-8", newline="") as csvfile:
                writer = csv.writer(csvfile)
                for row in self.ng_words_table.rows:
                    # NGワードの取得
                    ng_word_container = row.cells[0].content
                    if isinstance(ng_word_container, ft.Container) and isinstance(ng_word_container.content, ft.TextField):
                        ng_word = ng_word_container.content.value.strip()
                    else:
                        ng_word = ""

                    # 変換後の値の取得
                    replacement_container = row.cells[1].content
                    if isinstance(replacement_container, ft.Container) and isinstance(replacement_container.content, ft.TextField):
                        replacement = replacement_container.content.value.strip()
                    else:
                        replacement = ""

                    # NGワードと変換後の値が両方とも存在する場合にのみ書き込む
                    if ng_word and replacement:
                        writer.writerow([ng_word, replacement])
            self.show_success_message(f"NGワードを新しいCSVファイルとして保存しました: {file_path}")
            self.close_save_csv_dialog()
        except Exception as ex:
            self.show_error_message(f"ファイルの保存中にエラーが発生しました: {str(ex)}")

    def load_ng_words_from_csv(self, file_path):
        if not os.path.exists(file_path):
            self.show_error_message("ファイルが移動されたか削除されました。")
            self.ng_words_file_path.value = "ファイルが移動されたか削除されました。"
            self.ng_words_file_path.update()
            self.ng_words_table.rows.clear()
            self.add_ng_word_row()
            self.ng_words_table.update()
            return

        self.ng_words_table.rows.clear()
        try:
            with open(file_path, "r", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader, None)  # ヘッダー行をスキップ
                for row_data in reader:
                    if len(row_data) >= 2:
                        self.add_ng_word_row(row_data[0], row_data[1])
        except Exception as e:
            self.show_error_message(f"ファイルの読み込み中にエラーが発生しました: {str(e)}")

        self.add_ng_word_row()
        self.ng_words_table.update()

    def delete_selected_ng_words(self, e):
        rows_to_remove = []
        for row in self.ng_words_table.rows:
            cell_content = row.cells[2].content
            if isinstance(cell_content, ft.Container):
                checkbox = cell_content.content
                if isinstance(checkbox, ft.Checkbox) and checkbox.value:
                    rows_to_remove.append(row)

        if not rows_to_remove:
            self.show_error_message("削除する行が選択されていません。")
            return

        for row in rows_to_remove:
            self.ng_words_table.rows.remove(row)

        self.ng_words_changed = True
        self.show_success_message(f"{len(rows_to_remove)} 行を削除しました。")
        self.ng_words_table.update()

    def add_ng_word_row(self, ng_word="", replacement=""):
        # Checkboxの参照を作成
        checkbox_ref = ft.Ref[ft.Checkbox]()

        def on_change(e):
            self.ng_words_changed = True
            # チェック: もしこの行が最後の行で、両方のフィールドが入力されていたら新しい行を追加
            if row == self.ng_words_table.rows[-1]:
                ng_val = ng_word_input.content.value.strip()
                rep_val = replacement_input.content.value.strip()
                if ng_val and rep_val:
                    self.add_ng_word_row()
                    self.ng_words_table.update()
            # Checkboxの表示状態を更新
            if ng_word_input.content.value.strip() or replacement_input.content.value.strip():
                if checkbox_ref.current:
                    checkbox_ref.current.visible = True
                    checkbox_ref.current.update()
            else:
                if checkbox_ref.current:
                    checkbox_ref.current.visible = False
                    checkbox_ref.current.update()

        # NGワード入力フィールドをContainerでラップし、上下にパディングを追加
        ng_word_input = ft.Container(
            content=ft.TextField(
                value=ng_word,
                on_change=on_change,
                autofocus=False,
                border=ft.InputBorder.UNDERLINE,  # 枠線を変更（必要に応じて）
                bgcolor=ft.colors.WHITE,          # 背景色を設定
                content_padding=ft.padding.only(left=10, right=10),  # 左右のパディングを設定
            ),
            padding=ft.padding.symmetric(vertical=5),  # 上下に5pxのパディングを追加
            width=300  # Containerに幅を設定
        )

        # 変換後入力フィールドも同様にContainerでラップ
        replacement_input = ft.Container(
            content=ft.TextField(
                value=replacement,
                on_change=on_change,
                autofocus=False,
                border=ft.InputBorder.UNDERLINE,  # 枠線を変更（必要に応じて）
                bgcolor=ft.colors.WHITE,          # 背景色を設定
                content_padding=ft.padding.only(left=10, right=10),  # 左右のパディングを設定
            ),
            padding=ft.padding.symmetric(vertical=5),  # 上下に5pxのパディングを追加
            width=300  # Containerに幅を設定
        )

        # Checkboxを作成し、初期表示状態を設定
        checkbox = ft.Checkbox(
            value=False,
            visible=bool(ng_word.strip() or replacement.strip()),
            on_change=lambda e: setattr(self, 'ng_words_changed', True)
        )
        checkbox_ref.current = checkbox

        # CheckboxをContainerでラップし、中央揃えを設定
        checkbox_container = ft.Container(
            content=checkbox,
            alignment=ft.alignment.center
        )

        # 新しい行を作成し、テーブルに追加
        row = ft.DataRow(
            cells=[
                ft.DataCell(ng_word_input),
                ft.DataCell(replacement_input),
                ft.DataCell(checkbox_container),
            ]
        )
        self.ng_words_table.rows.append(row)

    def save_ng_words_to_csv(self, file_path):
        try:
            with open(file_path, "w", encoding="utf-8", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["NGワード", "変換ワード"])  # ヘッダー行を追加

                for row in self.ng_words_table.rows:
                    # NGワードの取得
                    ng_word_container = row.cells[0].content
                    if isinstance(ng_word_container, ft.Container) and isinstance(ng_word_container.content, ft.TextField):
                        ng_word = ng_word_container.content.value.strip()
                    else:
                        ng_word = ""

                    # 変換後の値の取得
                    replacement_container = row.cells[1].content
                    if isinstance(replacement_container, ft.Container) and isinstance(replacement_container.content, ft.TextField):
                        replacement = replacement_container.content.value.strip()
                    else:
                        replacement = ""

                    # NGワードと変換後の値が両方とも存在する場合にのみ書き込む
                    if ng_word and replacement:
                        writer.writerow([ng_word, replacement])
        except Exception as e:
            self.show_error_message(f"NGワードの保存中にエラーが発生しました: {str(e)}")

    def select_prohibited_words_file(self, e):
        def file_picker_result(e: ft.FilePickerResultEvent):
            if e.files:
                file_path = e.files[0].path
                self.prohibited_words_file_path.value = f"使用するCSVファイル: {file_path}"
                self.prohibited_words_file_path.update()
                self.load_prohibited_words_from_csv(file_path)
                self.prohibited_words_changed = True

        file_picker = ft.FilePicker(on_result=file_picker_result)
        self.page.overlay.append(file_picker)
        self.page.update()
        file_picker.pick_files(
            allowed_extensions=["csv"],
            allow_multiple=False,
        )

    def open_save_prohibited_csv_dialog(self, e):
        # ファイルパス入力用のRefを作成
        self.save_prohibited_csv_textfield_ref = ft.Ref[ft.TextField]()

        # カスタムダイアログを作成してファイルパスを入力してもらう
        self.save_prohibited_csv_dialog = ft.AlertDialog(
            title=ft.Text("新規CSVとして保存"),
            content=ft.Column([
                ft.Text("保存先のファイルパスを入力してください（例: C:/Users/Username/Documents/new_prohibited_words.csv）"),
                ft.TextField(
                    ref=self.save_prohibited_csv_textfield_ref,
                    hint_text="ファイルパスを入力",
                    autofocus=True,
                    expand=True
                ),
            ]),
            actions=[
                ft.TextButton("保存", on_click=self.save_as_new_prohibited_csv_callback_dialog),
                ft.TextButton("キャンセル", on_click=lambda _: self.close_save_prohibited_csv_dialog())
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = self.save_prohibited_csv_dialog
        self.save_prohibited_csv_dialog.open = True
        self.page.update()

    def close_save_prohibited_csv_dialog(self):
        self.save_prohibited_csv_dialog.open = False
        self.page.update()

    def save_as_new_prohibited_csv_callback_dialog(self, e):
        # Refを使用してTextFieldにアクセス
        text_field = self.save_prohibited_csv_textfield_ref.current
        if isinstance(text_field, ft.TextField):
            file_path = text_field.value.strip()
        else:
            self.show_error_message("ファイルパスの取得に失敗しました。")
            return

        if not file_path.endswith(".csv"):
            self.show_error_message("ファイル名は .csv で終わる必要があります。")
            return

        # ファイルパスのエスケープシーケンスを避けるためにスラッシュを使用
        file_path = file_path.replace("\\", "/")

        try:
            with open(file_path, "w", encoding="utf-8", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["禁止ワード"])  # ヘッダー行を追加
                for row in self.prohibited_words_table.rows:
                    # 禁止語彙の取得
                    prohibited_word_container = row.cells[0].content
                    if isinstance(prohibited_word_container, ft.Container) and isinstance(prohibited_word_container.content, ft.TextField):
                        prohibited_word = prohibited_word_container.content.value.strip()
                    else:
                        prohibited_word = ""

                    # 禁止語彙が存在する場合にのみ書き込む
                    if prohibited_word:
                        writer.writerow([prohibited_word])
            self.show_success_message(f"禁止ワードを新しいCSVファイルとして保存しました: {file_path}")
            self.close_save_prohibited_csv_dialog()
        except Exception as ex:
            self.show_error_message(f"ファイルの保存中にエラーが発生しました: {str(ex)}")

    def load_prohibited_words_from_csv(self, file_path):
        if not os.path.exists(file_path):
            self.show_error_message("ファイルが移動されたか削除されました。")
            self.prohibited_words_file_path.value = "ファイルが移動されたか削除されました。"
            self.prohibited_words_file_path.update()
            self.prohibited_words_table.rows.clear()
            self.add_prohibited_word_row()
            self.prohibited_words_table.update()
            return

        self.prohibited_words_table.rows.clear()
        try:
            with open(file_path, "r", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader, None)  # ヘッダー行をスキップ
                for row_data in reader:
                    if len(row_data) >= 1:
                        self.add_prohibited_word_row(row_data[0])
        except Exception as e:
            self.show_error_message(f"ファイルの読み込み中にエラーが発生しました: {str(e)}")

        self.add_prohibited_word_row()
        self.prohibited_words_table.update()

    def delete_selected_prohibited_words(self, e):
        rows_to_remove = []
        for row in self.prohibited_words_table.rows:
            cell_content = row.cells[1].content
            if isinstance(cell_content, ft.Container):
                checkbox = cell_content.content
                if isinstance(checkbox, ft.Checkbox) and checkbox.value:
                    rows_to_remove.append(row)

        if not rows_to_remove:
            self.show_error_message("削除する行が選択されていません。")
            return

        for row in rows_to_remove:
            self.prohibited_words_table.rows.remove(row)

        self.prohibited_words_changed = True
        self.show_success_message(f"{len(rows_to_remove)} 行を削除しました。")
        self.prohibited_words_table.update()

    def add_prohibited_word_row(self, prohibited_word=""):
        # Checkboxの参照を作成
        checkbox_ref = ft.Ref[ft.Checkbox]()

        def on_change(e):
            self.prohibited_words_changed = True
            # チェック: もしこの行が最後の行で、フィールドが入力されていたら新しい行を追加
            if row == self.prohibited_words_table.rows[-1]:
                prohibited_val = prohibited_word_input.content.value.strip()
                if prohibited_val:
                    self.add_prohibited_word_row()
                    self.prohibited_words_table.update()
            # Checkboxの表示状態を更新
            if prohibited_word_input.content.value.strip():
                if checkbox_ref.current:
                    checkbox_ref.current.visible = True
                    checkbox_ref.current.update()
            else:
                if checkbox_ref.current:
                    checkbox_ref.current.visible = False
                    checkbox_ref.current.update()

        # 禁止語彙入力フィールドをContainerでラップし、上下にパディングを追加
        prohibited_word_input = ft.Container(
            content=ft.TextField(
                value=prohibited_word,
                on_change=on_change,
                autofocus=False,
                border=ft.InputBorder.UNDERLINE,
                bgcolor=ft.colors.WHITE,
                content_padding=ft.padding.only(left=10, right=10),
            ),
            padding=ft.padding.symmetric(vertical=5),
            width=300
        )

        # Checkboxを作成し、初期表示状態を設定
        checkbox = ft.Checkbox(
            value=False,
            visible=bool(prohibited_word.strip()),
            on_change=lambda e: setattr(self, 'prohibited_words_changed', True)
        )
        checkbox_ref.current = checkbox

        # CheckboxをContainerでラップし、中央揃えを設定
        checkbox_container = ft.Container(
            content=checkbox,
            alignment=ft.alignment.center
        )

        # 新しい行を作成し、テーブルに追加
        row = ft.DataRow(
            cells=[
                ft.DataCell(prohibited_word_input),
                ft.DataCell(checkbox_container),
            ]
        )
        self.prohibited_words_table.rows.append(row)

    def save_prohibited_words_to_csv(self, file_path):
        try:
            with open(file_path, "w", encoding="utf-8", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["禁止ワード"])  # ヘッダー行を追加

                for row in self.prohibited_words_table.rows:
                    # 禁止ワードの取得
                    prohibited_words_container = row.cells[0].content
                    if isinstance(prohibited_words_container, ft.Container) and isinstance(prohibited_words_container.content, ft.TextField):
                        prohibited_words = prohibited_words_container.content.value.strip()
                    else:
                        prohibited_words = ""

                    # NGワードと変換後の値が両方とも存在する場合にのみ書き込む
                    if prohibited_words:
                        writer.writerow([prohibited_words])
        except Exception as e:
            self.show_error_message(f"禁止ワードの保存中にエラーが発生しました: {str(e)}")

    def show_error_message(self, message):
        self.page.snack_bar = ft.SnackBar(content=ft.Text(message), bgcolor=ft.colors.ERROR)
        self.page.snack_bar.open = True
        self.page.update()

    def show_success_message(self, message):
        self.page.snack_bar = ft.SnackBar(content=ft.Text(message), bgcolor=ft.colors.GREEN)
        self.page.snack_bar.open = True
        self.page.update()

    def get_device_options(self):
        try:
            devices = sd.query_devices()
            device_options = [device['name'] for device in devices if device['max_output_channels'] > 0]
            return device_options
        except Exception as e:
            print(f"Error querying devices: {e}")
            return []

    def refresh_devices(self, e=None):
        device_options = self.get_device_options()
        self.VIRTUAL_AUDIO_CABLE.current.options = [ft.dropdown.Option(device_name) for device_name in device_options]
        if device_options:
            self.VIRTUAL_AUDIO_CABLE.current.value = device_options[0]
        else:
            self.VIRTUAL_AUDIO_CABLE.current.value = None
        self.VIRTUAL_AUDIO_CABLE.current.update()

    def load_settings(self):
        settings_path = os.path.join(self.base_dir, 'settings', 'settings.ini')
        if os.path.exists(settings_path):
            self.config.read(settings_path, encoding='utf-8')

        # Ensure all necessary sections exist
        for section in ['ENVIRONMENT', 'OBS', 'ONECOMME', 'VTS', 'SYSTEM', 'NGWORD']:
            if not self.config.has_section(section):
                self.config.add_section(section)

        # OpenAIモデルリストの読み込み
        openai_models = self.config.get('SYSTEM', 'OPENAI_MODELS', fallback=None)
        if openai_models:
            self.openai_models = openai_models.split(',')
        else:
            self.openai_models = self.openai_default_models.copy()

        # Geminiモデルリストの読み込み
        gemini_models = self.config.get('SYSTEM', 'GEMINI_MODELS', fallback=None)
        if gemini_models:
            self.gemini_models = gemini_models.split(',')
        else:
            self.gemini_models = self.gemini_default_models.copy()

    def save_all_settings(self, e=None):
        # Save API keys
        self.config.set('ENVIRONMENT', 'OPENAI_API_KEY', self.OPENAI_API_KEY.current.value)
        self.config.set('ENVIRONMENT', 'GEMINI_API_KEY', self.GEMINI_API_KEY.current.value)
        # Save OBS settings
        self.config.set('OBS', 'OBS_WS_HOST', self.OBS_WS_HOST.current.value)
        self.config.set('OBS', 'OBS_WS_PORT', self.OBS_WS_PORT.current.value)
        self.config.set('OBS', 'OBS_WS_PASSWORD', self.OBS_WS_PASSWORD.current.value)
        self.config.set('OBS', 'OBS_SUBTITLE_AI', self.OBS_SUBTITLE_AI.current.value)
        self.config.set('OBS', 'OBS_SUBTITLE_COMMENT', self.OBS_SUBTITLE_COMMENT.current.value)
        self.config.set('OBS', 'OBS_SUBTITLE_NAME', self.OBS_SUBTITLE_NAME.current.value)
        self.config.set('OBS', 'OBS_SUBTITLE_LIMITE', self.OBS_SUBTITLE_LIMITE.current.value)
        # Save ONECOMME settings
        self.config.set('ONECOMME', 'ONECOMME_WS_HOST', self.ONECOMME_WS_HOST.current.value)
        self.config.set('ONECOMME', 'ONECOMME_WS_PORT', self.ONECOMME_WS_PORT.current.value)
        self.config.set('ONECOMME', 'ONECOMME_ID', self.ONECOMME_ID.current.value)
        # Save VTS settings
        self.config.set('VTS', 'VTS_WS_HOST', self.VTS_WS_HOST.current.value)
        self.config.set('VTS', 'VTS_WS_PORT', self.VTS_WS_PORT.current.value)
        # Save SYSTEM settings
        self.config.set('SYSTEM', 'VIRTUAL_AUDIO_CABLE', self.VIRTUAL_AUDIO_CABLE.current.value)
        self.config.set('SYSTEM', 'HISTORY_LIMITE', self.HISTORY_LIMITE.current.value)
        self.config.set('SYSTEM', 'CALL_LIMITE', self.CALL_LIMITE.current.value)
        self.config.set('SYSTEM', 'GEN_AI_MODEL', self.GEN_AI_MODEL.current.value)
        # Save AI settings
        self.config.set('SYSTEM', 'GEN_AI_SERVICE', self.GEN_AI_SERVICE.current.value)
        if self.gen_ai_model_changed:
            self.config.set('SYSTEM', 'OPENAI_MODELS', ','.join(self.openai_models))
            self.config.set('SYSTEM', 'GEMINI_MODELS', ','.join(self.gemini_models))
        selected_service = self.GEN_AI_SERVICE.current.value
        if selected_service == 'OpenAI API':
            self.config.set('SYSTEM', 'OPENAI_SELECTED_MODEL', self.GEN_AI_MODEL.current.value)
        else:
            self.config.set('SYSTEM', 'GEMINI_SELECTED_MODEL', self.GEN_AI_MODEL.current.value)

        # Save NGWORD settings
        if self.ng_words_changed:
            if not self.config.has_section('NGWORD'):
                self.config.add_section('NGWORD')
            # ファイルパスの取得
            file_path_text = self.ng_words_file_path.value
            if file_path_text.startswith("使用するCSVファイル: "):
                file_path = file_path_text.replace("使用するCSVファイル: ", "").strip()
                if os.path.exists(file_path):
                    self.config.set('NGWORD', 'NGWORD_FILE_PATH', file_path)
                    self.save_ng_words_to_csv(file_path)
                else:
                    self.config.set('NGWORD', 'NGWORD_FILE_PATH', '')
            elif file_path_text == "ファイルが移動されたか削除されました。":
                self.config.set('NGWORD', 'NGWORD_FILE_PATH', '')
            else:
                self.config.set('NGWORD', 'NGWORD_FILE_PATH', '')
                self.ng_words_table.rows.clear()
                self.add_ng_word_row()

        # Save PROHIBITED settings
        if self.prohibited_words_changed:
            if not self.config.has_section('NGWORD'):
                self.config.add_section('NGWORD')
            # ファイルパスの取得
            prohibited_file_path_text = self.prohibited_words_file_path.value
            if prohibited_file_path_text.startswith("使用するCSVファイル: "):
                file_path = prohibited_file_path_text.replace("使用するCSVファイル: ", "").strip()
                if os.path.exists(file_path):
                    self.config.set('NGWORD', 'PROHIBITED_FILE_PATH', file_path)
                    self.save_prohibited_words_to_csv(file_path)
                else:
                    self.config.set('NGWORD', 'PROHIBITED_FILE_PATH', '')
            elif prohibited_file_path_text == "ファイルが移動されたか削除されました。":
                self.config.set('NGWORD', 'PROHIBITED_FILE_PATH', '')
            else:
                self.config.set('NGWORD', 'PROHIBITED_FILE_PATH', '')
                self.prohibited_words_table.rows.clear()
                self.add_prohibited_word_row()

        # Save settings to file
        self.save_settings()
        self.show_success_message("設定変更を保存しました。")
        self.ng_words_changed = False
        self.prohibited_words_changed = False
        self.gen_ai_model_changed = False

    def reset_all_settings(self, e=None):
        # Reset API keys
        self.OPENAI_API_KEY.current.value = self.config.get('ENVIRONMENT', 'OPENAI_API_KEY', fallback='')
        self.GEMINI_API_KEY.current.value = self.config.get('ENVIRONMENT', 'GEMINI_API_KEY', fallback='')
        self.OPENAI_API_KEY.current.update()
        self.GEMINI_API_KEY.current.update()
        # Reset OBS settings
        self.OBS_WS_HOST.current.value = self.config.get('OBS', 'OBS_WS_HOST', fallback='127.0.0.1')
        self.OBS_WS_PORT.current.value = self.config.get('OBS', 'OBS_WS_PORT', fallback='4455')
        self.OBS_WS_PASSWORD.current.value = self.config.get('OBS', 'OBS_WS_PASSWORD', fallback='password')
        self.OBS_SUBTITLE_AI.current.value = self.config.get('OBS', 'OBS_SUBTITLE_AI', fallback='AI')
        self.OBS_SUBTITLE_COMMENT.current.value = self.config.get('OBS', 'OBS_SUBTITLE_COMMENT', fallback='COMMENT')
        self.OBS_SUBTITLE_NAME.current.value = self.config.get('OBS', 'OBS_SUBTITLE_NAME', fallback='NAME')
        self.OBS_SUBTITLE_LIMITE.current.value = self.config.get('OBS', 'OBS_SUBTITLE_LIMITE', fallback='50')
        self.OBS_WS_HOST.current.update()
        self.OBS_WS_PORT.current.update()
        self.OBS_WS_PASSWORD.current.update()
        self.OBS_SUBTITLE_AI.current.update()
        self.OBS_SUBTITLE_COMMENT.current.update()
        self.OBS_SUBTITLE_NAME.current.update()
        self.OBS_SUBTITLE_LIMITE.current.update()
        # Reset ONECOMME settings
        self.ONECOMME_WS_HOST.current.value = self.config.get('ONECOMME', 'ONECOMME_WS_HOST', fallback='127.0.0.1')
        self.ONECOMME_WS_PORT.current.value = self.config.get('ONECOMME', 'ONECOMME_WS_PORT', fallback='11180')
        self.ONECOMME_ID.current.value = self.config.get('ONECOMME', 'ONECOMME_ID', fallback='channel ID')
        self.ONECOMME_WS_HOST.current.update()
        self.ONECOMME_WS_PORT.current.update()
        self.ONECOMME_ID.current.update()
        # Reset SYSTEM settings
        self.VTS_WS_HOST.current.value = self.config.get('VTS', 'VTS_WS_HOST', fallback='127.0.0.1')
        self.VTS_WS_PORT.current.value = self.config.get('VTS', 'VTS_WS_PORT', fallback='8001')
        self.VTS_WS_HOST.current.update()
        self.VTS_WS_PORT.current.update()
        # Reset SYSTEM settings
        self.refresh_devices()
        self.VIRTUAL_AUDIO_CABLE.current.value = self.config.get('SYSTEM', 'VIRTUAL_AUDIO_CABLE', fallback="CABLE Input (VB-Audio Virtual Cable)")
        self.HISTORY_LIMITE.current.value = self.config.get('SYSTEM', 'HISTORY_LIMITE', fallback='3')
        self.CALL_LIMITE.current.value = self.config.get('SYSTEM', 'CALL_LIMITE', fallback='5')
        self.VIRTUAL_AUDIO_CABLE.current.update()
        self.HISTORY_LIMITE.current.update()
        self.CALL_LIMITE.current.update()
        self.GEN_AI_MODEL.current.update()
        # Reset AI settings
        self.GEN_AI_SERVICE.current.value = self.config.get('SYSTEM', 'GEN_AI_SERVICE', fallback='OpenAI API')
        self.GEN_AI_SERVICE.current.update()
        # モデルリストの読み込み
        openai_models = self.config.get('SYSTEM', 'OPENAI_MODELS', fallback=None)
        if openai_models:
            self.openai_models = openai_models.split(',')
        else:
            self.openai_models = self.openai_default_models.copy()

        gemini_models = self.config.get('SYSTEM', 'GEMINI_MODELS', fallback=None)
        if gemini_models:
            self.gemini_models = gemini_models.split(',')
        else:
            self.gemini_models = self.gemini_default_models.copy()

        # 選択されたモデルの設定
        selected_service = self.GEN_AI_SERVICE.current.value
        if selected_service == 'OpenAI API':
            models = self.openai_models
            selected_model = self.config.get('SYSTEM', 'OPENAI_SELECTED_MODEL', fallback=models[0] if models else None)
        else:
            models = self.gemini_models
            selected_model = self.config.get('SYSTEM', 'GEMINI_SELECTED_MODEL', fallback=models[0] if models else None)

        self.GEN_AI_MODEL.current.options = [ft.dropdown.Option(model) for model in models]
        self.GEN_AI_MODEL.current.value = selected_model
        self.GEN_AI_MODEL.current.update()

        # Reset NGWORD settings
        ngword_file_path = self.config.get('NGWORD', 'NGWORD_FILE_PATH', fallback='')
        if ngword_file_path:
            if os.path.exists(ngword_file_path):
                self.ng_words_file_path.value = f"使用するCSVファイル: {ngword_file_path}"
                self.load_ng_words_from_csv(ngword_file_path)
            else:
                # ファイルが存在しない場合のメッセージ表示
                self.ng_words_file_path.value = "ファイルが移動されたか削除されました。"
                self.ng_words_file_path.update()
                # テーブルをクリアし、空の行を追加
                self.ng_words_table.rows.clear()
                self.add_ng_word_row()
        else:
            self.ng_words_table.rows.clear()
            self.add_ng_word_row()
            self.ng_words_table.update()

        # Reset PROHIBITED settings
        prohibited_file_path = self.config.get('NGWORD', 'PROHIBITED_FILE_PATH', fallback='')
        if prohibited_file_path:
            if os.path.exists(prohibited_file_path):
                self.prohibited_words_file_path.value = f"使用するCSVファイル: {prohibited_file_path}"
                self.load_prohibited_words_from_csv(prohibited_file_path)
            else:
                # ファイルが存在しない場合のメッセージ表示
                self.prohibited_words_file_path.value = "ファイルが移動されたか削除されました。"
                self.prohibited_words_file_path.update()
                # テーブルをクリアし、空の行を追加
                self.prohibited_words_table.rows.clear()
                self.add_prohibited_word_row()
        else:
            self.prohibited_words_table.rows.clear()
            self.add_prohibited_word_row()
            self.prohibited_words_table.update()

        # Update page
        self.page.update()

    def save_settings(self):
        settings_path = os.path.join(self.base_dir, 'settings', 'settings.ini')
        with open(settings_path, "w", encoding='utf-8') as f:
            self.config.write(f)

    def load_characters(self):
        """
        CharacterManagerクラスのself.charactersを取得してAITuberAppのself.charactersを更新
        update_character_containersを実行
            →self.charactersのコンテナを一体ずつ作成
             character_tabをアップデート
        """
        print("Loading characters")
        self.characters = self.cm.characters
        print(f"Loaded {len(self.characters)} characters")
        self.update_character_containers()

        # 更新後に配信タブのプルダウンも更新
        if hasattr(self, 'stream_character_dropdown') and self.stream_character_dropdown.current:
            self.stream_character_dropdown.current.options = [ft.dropdown.Option(char["name"]) for char in self.characters]
            if self.characters:
                self.stream_character_dropdown.current.value = self.characters[0]["name"]
                # 更新されたキャラクターの画像と名前を設定
                self.selected_character_image.current.src = self.characters[0]["image"]
                self.selected_character_name.current.value = self.characters[0]["name"]
            else:
                self.stream_character_dropdown.current.value = None
                self.selected_character_image.current.src = ""
                self.selected_character_name.current.value = ""
            self.stream_character_dropdown.current.update()
            self.selected_character_image.current.update()
            self.selected_character_name.current.update()

    def update_character_containers(self):
        logging.debug("Updating character containers")
        self.character_containers = [self.create_character_container(char, i) for i, char in enumerate(self.characters)]
        self.character_containers.append(self.create_add_character_container())

        if self.page.route == "/" and self.character_row.current:
            self.character_row.current.controls = self.character_containers
            self.character_row.current.update()

    def create_add_character_container(self):
        container = ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.ADD, size=80, color=ft.colors.GREY_400),
                ft.Text("新規作成", size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=220,
            height=260,
            padding=0,
            on_click=lambda _: self.page.go("/add_character"),
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
        )

        def on_hover(e):
            if e.data == "true":
                container.bgcolor = ft.colors.BLUE_GREY_100
            else:
                container.bgcolor = None
            container.update()

        container.on_hover = on_hover

        return container

    def create_character_container(self, char, index):
        container = ft.Container(
            content=ft.Column([
                ft.Image(src=char["image"], width=200, height=200, fit=ft.ImageFit.CONTAIN),
                ft.Text(char["name"], size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=220,
            height=260,
            padding=0,
            on_click=lambda _: self.toggle_character_selection(index),
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
        )

        def on_hover(e):
            if e.data == "true":
                container.bgcolor = ft.colors.BLUE_GREY_100
            else:
                container.bgcolor = None
            container.update()

        container.on_hover = on_hover

        return container

    def toggle_character_selection(self, index):
        logging.debug(f"Toggling character selection. Index: {index}, Current selected: {self.selected_index}")
        if index < 0 or index >= len(self.characters):
            logging.debug(f"Invalid index: {index}. Ignoring selection.")
            return

        if self.selected_index == index:
            self.selected_index = -1
            self.close_bottom_sheet()
        else:
            self.selected_index = index
            self.open_bottom_sheet(index)
        self.update_character_containers()
        self.page.update()

    def open_bottom_sheet(self, index):
        if index < 0 or index >= len(self.characters):
            print(f"Invalid index: {index}. Cannot open bottom sheet.")
            return

        character = self.characters[index]
        sheet_content = self.bottom_sheet.content.content
        # 更新: キャラクター名を表示
        if isinstance(sheet_content.controls[0], ft.Text):
            sheet_content.controls[0].value = f"キャラクター: {character['name']}"
        # 更新: 画像ソースを設定
        if isinstance(sheet_content.controls[1], ft.Image):
            sheet_content.controls[1].src = character['image']
        self.bottom_sheet.open = True
        self.bottom_sheet.update()

    def close_bottom_sheet(self, _=None):
        self.bottom_sheet.open = False
        self.bottom_sheet.update()

    def on_bottom_sheet_dismiss(self, e):
        logging.debug("BottomSheet dismissed")
        self.selected_index = -1
        if self.page.route == "/":
            self.update_character_containers()
            self.page.update()

    def edit_character(self, e):
        logging.debug(f"Edit character clicked. Selected index: {self.selected_index}")
        if self.selected_index != -1:
            self.page.go(f"/character_detail/{self.selected_index}")

    def duplicate_character(self, e):
        if self.selected_index != -1:
            original_character = self.characters[self.selected_index]
            new_character = original_character.copy()
            new_character["name"] = f"{original_character['name']} (Copy)"
            # 画像ファイルをコピー
            original_image_path = original_character['image']
            if original_image_path != self.cm.DEFAULT_IMAGE:
                # 新しいユニークなファイル名を生成
                ext = os.path.splitext(original_image_path)[1]
                new_image_filename = f"{uuid.uuid4()}{ext}"
                # 画像ファイルをコピー
                new_image_path = self.cm.copy_image(original_image_path, new_image_filename)
                # 新しいキャラクターのデータに画像パスを更新
                new_character['image'] = new_image_path
            else:
                # デフォルトの画像の場合はそのまま使用
                new_character['image'] = self.cm.DEFAULT_IMAGE
            # 新しいフィールドもコピー
            new_character["pose"] = original_character.get("pose", "")
            new_character["happy"] = original_character.get("happy", "")
            new_character["sad"] = original_character.get("sad", "")
            new_character["surprise"] = original_character.get("surprise", "")
            new_character["angry"] = original_character.get("angry", "")
            new_character["blue"] = original_character.get("blue", "")
            new_character["neutral"] = original_character.get("neutral", "")
            self.cm.add_character(new_character)
            self.load_characters()
            self.update_character_containers()
            self.close_bottom_sheet()
            self.page.update()
            self.show_success_message(f"キャラクター '{original_character['name']}' を複製しました。")

    def delete_character(self, e):
        print(f"Delete button clicked. Selected index: {self.selected_index}")
        if self.selected_index != -1:
            index_to_delete = self.selected_index
            character_name = self.characters[self.selected_index]['name']

            def confirm_delete(e):
                print(f"Confirming deletion of character at index {index_to_delete}")
                self.cm.delete_character(index_to_delete)
                print("Character deleted, updating UI")
                self.load_characters()
                # 現在のルートがメインページかどうかを確認
                if self.page.route == "/":
                    self.update_character_containers()
                self.close_bottom_sheet()
                dialog.open = False
                self.selected_index = -1
                self.page.update()
                print("UI updated after deletion")

                self.show_success_message(f"キャラクター '{character_name}' を削除しました。")

            def cancel_delete(e):
                print("Deletion cancelled")
                dialog.open = False
                self.page.update()

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("※警告"),
                content=ft.Text("キャラクターを削除してもよろしいですか？"),
                actions=[
                    ft.TextButton("はい", on_click=confirm_delete),
                    ft.TextButton("いいえ", on_click=cancel_delete),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

    def route_change(self, route):
        logging.debug(f"Route changed to: {route.route}")
        self.update_view()

    def update_view(self):
        """
        ルートが変更された際に実行され、現在のビューを変更し、更新する
        ・ルートがメインビューの場合、load_charactersが実行され、メインビューを表示する
        ・ルートがキャラクター編集画面の場合、そのindexの編集画面を表示する
        ・ルートがキャラクター追加画面の場合、その画面を表示する
        """
        self.page.views.clear()
        if self.page.route == "/":
            self.page.views.append(self.main_view)
            self.page.update()
            self.load_characters()
        elif self.page.route.startswith("/character_detail/"):
            index = int(self.page.route.split("/")[-1])
            self.page.views.append(self.create_character_page(is_new=False, index=index))
        elif self.page.route == "/add_character":
            self.page.views.append(self.create_character_page(is_new=True))
        self.page.update()

    def navigate(self, route):
        self.page.route = route
        self.update_view()
        self.page.update()

    def view_pop(self, view):
        self.page.views.pop()
        top_view = self.page.views[-1]
        self.page.go(top_view.route)

    def show_success_message(self, message):
        self.page.snack_bar = ft.SnackBar(content=ft.Text(message), bgcolor=ft.colors.GREEN)
        self.page.snack_bar.open = True
        self.page.update()

    def create_character_page(self, is_new=False, index=0):
        image_ref = ft.Ref[ft.Image]()
        name_input = ft.Ref[ft.TextField]()
        family_name_input = ft.Ref[ft.TextField]()
        last_name_input = ft.Ref[ft.TextField]()
        family_name_kana_input = ft.Ref[ft.TextField]()
        last_name_kana_input = ft.Ref[ft.TextField]()
        profile_prompt_input = ft.Ref[ft.TextField]()
        situation_prompt_input = ft.Ref[ft.TextField]()
        guideline_prompt_input = ft.Ref[ft.TextField]()
        voice_prompt_input = ft.Ref[ft.TextField]()
        format_prompt_input = ft.Ref[ft.TextField]()
        exampleTopic_prompt_input = ft.Ref[ft.TextField]()
        thinkTopic_prompt_input = ft.Ref[ft.TextField]()
        voice_service_dropdown = ft.Ref[ft.Dropdown]()
        voice_dropdown = ft.Ref[ft.Dropdown]()
        change_tone_checkbox = ft.Ref[ft.Checkbox]()
        wait_time = ft.Ref[ft.TextField]()
        happy_input = ft.Ref[ft.TextField]()
        sad_input = ft.Ref[ft.TextField]()
        fun_input = ft.Ref[ft.TextField]()
        angry_input = ft.Ref[ft.TextField]()
        neutral_input = ft.Ref[ft.TextField]()
        hotkeys_table_container = ft.Column()
        vv_status = ft.Ref[ft.Text]()
        vts_status = ft.Ref[ft.Text]()
        file_picker = ft.FilePicker(on_result=lambda e: self.update_image(e, image_ref))
        self.page.overlay.append(file_picker)

        def get_voicevoxIds(e):
            from src.voice.voicevox_adapter import VoicevoxAdapter
            try:
                va = VoicevoxAdapter()
                voice_list, _ = va.fetch_voice_id()
                dropdown_options = [ft.dropdown.Option(voice_name) for voice_name in voice_list]
                voice_dropdown.current.options = dropdown_options

                # 保存されたボイスキャラクターがあれば選択状態にする
                saved_voice = voice_dropdown.current.value
                if saved_voice in voice_list:
                    voice_dropdown.current.value = saved_voice
                else:
                    voice_dropdown.current.value = voice_list[0] if voice_list else None

                voice_dropdown.current.update()
            except Exception as ex:
                # エラー処理
                vv_status.current.value = f"エラーが発生しました: {str(ex)}"
                vv_status.current.color = ft.colors.RED
                vv_status.current.update()

        def get_hotkeyIds(e):
            from src.vtubestudio.vtubestudio_adapter import VtubeStudioAdapter
            try:
                vts_status.current.value = "ホットキーIDを取得します。VTSにて'AIVsystem_Plugin'を許可してください。"
                vts_status.current.color = ft.colors.RED
                vts_status.current.update()
                vts_allow_flag = multiprocessing.Queue()
                vs = VtubeStudioAdapter(self.base_dir,vts_allow_flag)
                allow_flag = vts_allow_flag.get()
                if allow_flag == 1:
                    vts_status.current.value = "VTSプラグインが拒否されました。"
                    vts_status.current.color = ft.colors.RED
                    vts_status.current.update()
                    pass
                else:
                    hotkey_datas = vs.get_hotkey_list()
                    current_model_name = hotkey_datas["current_model_name"]
                    hotkey_dict_list = hotkey_datas["hotkeys_list"]

                    # コンテナをクリア
                    hotkeys_table_container.controls.clear()

                    # モデル名を追加
                    hotkeys_table_container.controls.append(
                        ft.Text(f"現在のモデル名: {current_model_name}", weight=ft.FontWeight.BOLD)
                    )

                    # テーブルのデータ行を作成
                    data_rows = []
                    for hotkey in hotkey_dict_list:
                        hotkey_id = hotkey.get('hotkeyID', '')
                        hotkey_name = hotkey.get('hotkey_name', '')
                        row = ft.DataRow(cells=[
                            ft.DataCell(ft.Text(hotkey_name)),
                            ft.DataCell(ft.Text(hotkey.get('file', ''))),
                            ft.DataCell(ft.Row([
                                ft.Text(hotkey_id),
                                ft.IconButton(
                                    icon=ft.icons.COPY,
                                    tooltip="ホットキーIDをコピー",
                                    on_click=lambda e, hotkey_name=hotkey_name, hotkey_id=hotkey_id: copy_to_clipboard(e, hotkey_id, hotkey_name)
                                )
                            ], alignment=ft.MainAxisAlignment.START))
                        ])
                        data_rows.append(row)

                    # DataTableを作成
                    hotkeys_table = ft.DataTable(
                        columns=[
                            ft.DataColumn(ft.Text('ホットキー名')),
                            ft.DataColumn(ft.Text('ファイル')),
                            ft.DataColumn(ft.Text('ホットキーID')),
                        ],
                        rows=data_rows
                    )

                    hotkeys_table_container.controls.append(hotkeys_table)

                    # コンテナを更新
                    hotkeys_table_container.update()
                    vts_status.current.value = "ホットキーIDを取得しました。"
                    vts_status.current.color = ft.colors.BLACK
                    vts_status.current.update()
            except Exception as ex:
                # エラー処理
                hotkeys_table_container.controls.clear()
                hotkeys_table_container.controls.append(
                    ft.Text(f"エラーが発生しました: {str(ex)}", color=ft.colors.RED)
                )
                hotkeys_table_container.update()

        def copy_to_clipboard(e, hotkey_id, hotkey_name):
            self.page.set_clipboard(hotkey_id)
            self.show_success_message(f"'{hotkey_name}'のホットキーIDをクリップボードにコピーしました。")

        def save_and_return(is_new, index):
            if not name_input.current.value:
                name = self.cm.DEFAULT_NAME
            else:
                name = name_input.current.value
            family_name = family_name_input.current.value
            last_name = last_name_input.current.value
            family_name_kana = family_name_kana_input.current.value
            last_name_kana = last_name_kana_input.current.value
            profile_prompt = profile_prompt_input.current.value
            situation_prompt = situation_prompt_input.current.value
            guideline_prompt = guideline_prompt_input.current.value
            voice_prompt = voice_prompt_input.current.value
            format_prompt = format_prompt_input.current.value
            exampleTopic_prompt = exampleTopic_prompt_input.current.value
            thinkTopic_prompt = thinkTopic_prompt_input.current.value
            voice_service = voice_service_dropdown.current.value
            voice = voice_dropdown.current.value
            change_tone = change_tone_checkbox.current.value
            wait = wait_time.current.value
            happy = happy_input.current.value.strip()
            sad = sad_input.current.value.strip()
            fun = fun_input.current.value.strip()
            angry = angry_input.current.value.strip()
            neutral = neutral_input.current.value.strip()

            # 他のキャラクターの表示名とかぶらないかチェック
            existing_names = [char["name"] for char in self.characters]
            if not is_new:
                # 編集の場合は自分自身の名前を除外
                existing_names.remove(self.characters[index]["name"])
            existing_names_lower = [n.lower() for n in existing_names]
            if name.lower() in existing_names_lower:
                self.show_error_message("エラー: その表示名は既に使用されています。")
                return

            character_data = {
                "name": name,
                "family_name": family_name,
                "last_name": last_name, 
                "family_name_kana": family_name_kana,
                "last_name_kana": last_name_kana,
                "image": image_ref.current.src,
                "profile_prompt": profile_prompt,
                "situation_prompt": situation_prompt,
                "guideline_prompt": guideline_prompt,
                "voice_prompt" : voice_prompt,
                "format_prompt" : format_prompt,
                "exampleTopic_prompt" : exampleTopic_prompt,
                "thinkTopic_prompt" : thinkTopic_prompt,
                "voice_service": voice_service,
                "voice": voice,
                "change_tone": change_tone,
                "wait": wait,
                "happy": happy,
                "sad": sad,
                "fun": fun,
                "angry": angry,
                "neutral": neutral,
            }
            if is_new:
                self.cm.add_character(character_data)
            else:
                self.cm.update_character(index, character_data)

            message = f"キャラクター '{name}' {'を作成' if is_new else 'の更新を保存'}しました。"
            self.navigate("/")
            self.show_success_message(message)

        character = self.cm.get_character(index) if not is_new else None

        # 左側のカラム（固定）
        left_column = ft.Column([
            ft.Image(ref=image_ref, src=character["image"] if character else self.cm.DEFAULT_IMAGE, width=300, height=300, fit=ft.ImageFit.CONTAIN),
            ft.ElevatedButton("画像を選択", on_click=lambda _: file_picker.pick_files(allow_multiple=False)),
            ft.Row([
                ft.ElevatedButton("保存", on_click=lambda _: save_and_return(is_new, index)),
                ft.ElevatedButton("キャンセル", on_click=lambda _: self.navigate("/"))
            ], spacing=10)
        ], alignment=ft.MainAxisAlignment.START, spacing=10)

        character_name_text = ft.Text(
            "キャラクター名を入力するフィールドです。(姓、名の片方のみの入力も可能です。)",
            size=16,
            weight=ft.FontWeight.BOLD,
        )
        profile_prompt_text = ft.Text(
            "キャラクタープロフィールを設定するフィールドです。",
            size=16,
            weight=ft.FontWeight.BOLD,
        )
        situation_prompt_text = ft.Text(
            "キャラクターの状況を設定するフィールドです。",
            size=16,
            weight=ft.FontWeight.BOLD,
        )
        guideline_prompt_text = ft.Text(
            "キャラクターのコメントへの応答のガイドラインを設定するフィールドです。",
            size=16,
            weight=ft.FontWeight.BOLD,
        )
        voice_prompt_text = ft.Text(
            "キャラクターの発言時の声のトーンの選択肢、指定形式を設定するフィールドです。",
            size=16,
            weight=ft.FontWeight.BOLD,
        )
        format_prompt_text = ft.Text(
            "キャラクターのコメントへの応答形式の制約を設定するフィールドです。",
            size=16,
            weight=ft.FontWeight.BOLD,
        )
        exampleTopic_prompt_text = ft.Text(
            "キャラクターが自発的に話す際に参考にする話題の例を設定するフィールドです。\n(確実にその話題を話すわけではありません。)",
            size=16,
            weight=ft.FontWeight.BOLD,
        )
        thinkTopic_prompt_text = ft.Text(
            "キャラクターが自発的に話す際の話題選びの考え方を設定するフィールドです。",
            size=16,
            weight=ft.FontWeight.BOLD,
        )
        hotkey_explain_text = ft.Text(
            "ホットキーを指定し、キャラクターの発話中のアクションを設定します。以下のボタンを使用する場合は事前にVTSの設定・ホットキーの作成を完了し、VTSを起動してください。",
            size=16,
            weight=ft.FontWeight.BOLD,
        )

        # 右側のカラム（スクロール可能）- 見出しを追加
        right_column = ft.ListView([
            ft.Text("キャラクター設定", style=ft.TextThemeStyle.HEADLINE_SMALL, weight=ft.FontWeight.BOLD),
            character_name_text,
            ft.TextField(ref=name_input, label="表示名", value=character.get("name", self.cm.DEFAULT_NAME) if character else self.cm.DEFAULT_NAME, expand=1, bgcolor=ft.colors.WHITE,),
            ft.Row([
                ft.TextField(ref=family_name_input, label="姓", value=character.get("family_name", self.cm.DEFAULT_FAMILY_NAME) if character else self.cm.DEFAULT_FAMILY_NAME, expand=1, bgcolor=ft.colors.WHITE,),
                ft.TextField(ref=last_name_input, label="名", value=character.get("last_name", self.cm.DEFAULT_LAST_NAME) if character else self.cm.DEFAULT_LAST_NAME, expand=1, bgcolor=ft.colors.WHITE),
            ]),
            ft.Row([
                ft.TextField(ref=family_name_kana_input, label="せい（かな）", value=character.get("family_name_kana", self.cm.DEFAULT_FAMILY_KANA_NAME) if character else self.cm.DEFAULT_FAMILY_KANA_NAME, expand=1, bgcolor=ft.colors.WHITE),
                ft.TextField(ref=last_name_kana_input, label="めい（かな）", value=character.get("last_name_kana", self.cm.DEFAULT_LAST_KANA_NAME) if character else self.cm.DEFAULT_LAST_KANA_NAME, expand=1, bgcolor=ft.colors.WHITE),
            ]),
            ft.Divider(thickness=1),
            ft.Text("ボイス設定", style=ft.TextThemeStyle.HEADLINE_SMALL, weight=ft.FontWeight.BOLD),
            ft.Dropdown(
                ref=voice_service_dropdown,
                label="合成音声サービス",
                options=[
                    ft.dropdown.Option("VOICEVOX"),
                ],
                value=character.get("voice_service", "VOICEVOX") if character else "VOICEVOX",
                bgcolor=ft.colors.WHITE
            ),
            ft.Dropdown(
                ref=voice_dropdown,
                label="ボイスキャラクター",
                bgcolor=ft.colors.WHITE,
                value=character.get("voice", "ずんだもん(ノーマル)") if character else "ずんだもん(ノーマル)",
            ),
            ft.ElevatedButton("ボイスキャラクターを取得", on_click=get_voicevoxIds),
            ft.Text(
                ref=vv_status,
                value="利用可能なボイスキャラクターを取得します。\n「外部ソフト」設定を完了し、VOICEVOXを起動した状態でボタンを押下してください。",
                color=ft.colors.BLACK
            ),
            ft.Row(
                [
                    ft.Checkbox(
                        ref=change_tone_checkbox,
                        label="発言内容に合わせて声のトーンを変える",
                        value=character.get("change_tone", False) if character else False,
                    )
                ],
            ),
            ft.Text(
                ref=vv_status,
                value="以下のキャラクターを選択した場合のみ可能です。\n・四国めたん(ノーマル)\n・ずんだもん(ノーマル)\n・玄野武宏(ノーマル)\n・白上虎太郎(ふつう)\n・青山龍星(ノーマル)\n・九州そら(ノーマル)\n・もち子さん(ノーマル)\n・WhiteCUL(ノーマル)\n※本機能を使用する場合は、使用ボイスに合わせてプロンプト設定の声のトーンの種類を変更してください。",
                color=ft.colors.BLACK
            ),
            ft.Divider(thickness=1),
            ft.Text("自動発話設定", style=ft.TextThemeStyle.HEADLINE_SMALL, weight=ft.FontWeight.BOLD),
            ft.TextField(ref=wait_time, label="自動発話までのコメント待機時間(秒:半角数字で入力)", value=character["wait"] if character else "", bgcolor=ft.colors.WHITE),
            ft.Divider(thickness=1),
            ft.Text("ホットキー設定(VTS)", style=ft.TextThemeStyle.HEADLINE_SMALL, weight=ft.FontWeight.BOLD),
            hotkey_explain_text,
            ft.ElevatedButton("ホットキーを取得", on_click=get_hotkeyIds),
            ft.Text(
                ref=vts_status,
                value="VTSに表示中のモデルのホットキーIDを取得します。ボタン押下後、'AIVsystem_Plugin'を許可してください。",
                color=ft.colors.BLACK
            ),
            hotkeys_table_container,
            ft.TextField(ref=happy_input, label="Happy ホットキーID", value=character.get("happy", "") if character else "", bgcolor=ft.colors.WHITE),
            ft.TextField(ref=sad_input, label="Sad ホットキーID", value=character.get("sad", "") if character else "", bgcolor=ft.colors.WHITE),
            ft.TextField(ref=fun_input, label="Fun ホットキーID", value=character.get("fun", "") if character else "", bgcolor=ft.colors.WHITE),
            ft.TextField(ref=angry_input, label="Angry ホットキーID", value=character.get("angry", "") if character else "", bgcolor=ft.colors.WHITE),
            ft.TextField(ref=neutral_input, label="Neutral ホットキーID", value=character.get("neutral", "") if character else "", bgcolor=ft.colors.WHITE),
            ft.Divider(thickness=1),
            ft.Text("プロンプト設定", style=ft.TextThemeStyle.HEADLINE_SMALL, weight=ft.FontWeight.BOLD),
            profile_prompt_text,
            ft.TextField(ref=profile_prompt_input, label="キャラクターのプロフィールを入力してください", value=character.get("profile_prompt", self.default_profile_prompt) if character else self.default_profile_prompt, multiline=True, min_lines=3, max_lines=5, bgcolor=ft.colors.WHITE),
            situation_prompt_text,
            ft.TextField(ref=situation_prompt_input, label="キャラクターの配信シチュエーションを入力してください", value=character.get("situation_prompt", self.default_situation_prompt) if character else self.default_situation_prompt, multiline=True, min_lines=3, max_lines=5, bgcolor=ft.colors.WHITE),
            guideline_prompt_text,
            ft.TextField(ref=guideline_prompt_input, label="キャラクターの応答のガイドラインを入力してください", value=character.get("guideline_prompt", self.default_guideline_prompt) if character else self.default_guideline_prompt, multiline=True, min_lines=3, max_lines=5, bgcolor=ft.colors.WHITE),
            voice_prompt_text,
            ft.TextField(ref=voice_prompt_input, label="声のトーンの指定形式を入力してください", value=character.get("voice_prompt", self.default_voice_prompt) if character else self.default_voice_prompt, multiline=True, min_lines=3, max_lines=5, bgcolor=ft.colors.WHITE),
            format_prompt_text,
            ft.TextField(ref=format_prompt_input, label="キャラクターの応答形式の制約を入力してください", value=character.get("format_prompt", self.default_format_prompt) if character else self.default_format_prompt, multiline=True, min_lines=3, max_lines=5, bgcolor=ft.colors.WHITE),
            exampleTopic_prompt_text,
            ft.TextField(ref=exampleTopic_prompt_input, label="自動発話時の話題の例を入力してください", value=character.get("exampleTopic_prompt", self.default_exampleTopic_prompt) if character else self.default_exampleTopic_prompt, multiline=True, min_lines=3, max_lines=5, bgcolor=ft.colors.WHITE),
            thinkTopic_prompt_text,
            ft.TextField(ref=thinkTopic_prompt_input, label="自動発話時の話題の生成方法を入力してください", value=character.get("thinkTopic_prompt", self.default_thinkTopic_prompt) if character else self.default_thinkTopic_prompt, multiline=True, min_lines=3, max_lines=5, bgcolor=ft.colors.WHITE),
        ], expand=True, spacing=10, padding=20)

        return ft.View(
            "/add_character" if is_new else f"/character_detail/{index}",
            [
                ft.AppBar(title=ft.Text("新規キャラクター追加" if is_new else "キャラクター編集"), bgcolor=ft.colors.SURFACE_VARIANT),
                ft.Row([
                    left_column,
                    ft.VerticalDivider(width=1),
                    right_column
                ], expand=True)
            ]
        )

    def update_image(self, e, image_ref):
        if e.files:
            upload_file = e.files[0]
            # ファイルの拡張子を取得
            ext = os.path.splitext(upload_file.name)[1]
            # ユニークなファイル名を生成
            new_file_name = f"{uuid.uuid4()}{ext}"
            # 画像をコピー
            new_file_path = self.cm.copy_image(upload_file.path, new_file_name)
            image_ref.current.src = new_file_path
            image_ref.current.update()
            self.page.update()

