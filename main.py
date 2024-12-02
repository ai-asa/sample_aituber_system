import flet as ft
import sys
import os
import shutil
from ui.app import AIVtuberApp

def main(page: ft.Page):

    def get_documents_dir():
        # Windows のドキュメントフォルダを取得
        return os.path.join(os.environ['USERPROFILE'], 'Documents')

    def get_app_dir():
        # ドキュメントフォルダ内の 'testApp' ディレクトリを取得
        return os.path.join(get_documents_dir(), 'testApp')

    def ensure_app_dir():
        # 'testApp' ディレクトリがなければ作成
        app_dir = get_app_dir()
        if not os.path.exists(app_dir):
            os.makedirs(app_dir)
        return app_dir

    def copy_file_to_app_dir(filename):
        # アプリ内のファイルをドキュメントフォルダにコピー
        app_dir = ensure_app_dir()
        dest_path = os.path.join(app_dir, filename)

        # 既に存在する場合はコピーしない
        if not os.path.exists(dest_path):
            # アプリ内のファイルのパスを取得
            if getattr(sys, 'frozen', False):
                # パッケージ化された場合
                base_path = os.path.dirname(os.path.abspath(sys.executable))
            else:
                # スクリプト実行の場合
                base_path = os.path.dirname(os.path.abspath(__file__))

            source_path = os.path.join(base_path, filename)

            try:
                shutil.copyfile(source_path, dest_path)
                print(f"Copied {filename} to {dest_path}")
            except Exception as e:
                print(f"Error copying {filename}: {e}")
        else:
            print(f"{filename} already exists at {dest_path}, not overwriting.")

    # 初回起動時のファイルコピー
    copy_file_to_app_dir("settings.ini")
    copy_file_to_app_dir("characters.ini")
    copy_file_to_app_dir("data//ng//ng_expressions.csv")
    copy_file_to_app_dir("data//ng//ng_words.csv")
    copy_file_to_app_dir("assets")

    app = AIVtuberApp(page)

if __name__ == "__main__":
    ft.app(target=main)

