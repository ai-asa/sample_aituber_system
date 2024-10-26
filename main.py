import flet as ft
import os
import sys
import shutil
import multiprocessing

def get_documents_dir():
    # Windows のドキュメントフォルダを取得
    return os.path.join(os.environ['USERPROFILE'], 'Documents')

def get_base_documents_dir():
    # ドキュメント内の AIVTuberSystem フォルダを取得
    return os.path.join(get_documents_dir(), 'AIVTuberSystem')

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def copy_file_to_documents(source_relative_path, dest_relative_path):
    # source_relative_path: アプリケーションディレクトリからの相対パス
    # dest_relative_path: AIVTuberSystem ディレクトリからの相対パス

    # resource_pathを使用して、正しいパスを取得
    source_path = resource_path(source_relative_path)
    dest_path = os.path.join(get_base_documents_dir(), dest_relative_path)

    # ディレクトリが存在しない場合は作成
    dest_dir = os.path.dirname(dest_path)
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    # 既に存在する場合はコピーしない
    if not os.path.exists(dest_path):
        try:
            shutil.copyfile(source_path, dest_path)
            print(f"Copied {source_path} to {dest_path}")
        except Exception as e:
            print(f"Error copying {source_path} to {dest_path}: {e}")
    else:
        print(f"{dest_path} already exists, not overwriting.")

def main(page: ft.Page):
    from ui.app import AIVtuberApp

    # 起動時に AIVTuberSystem フォルダを作成
    base_documents_dir = get_base_documents_dir()
    if not os.path.exists(base_documents_dir):
        os.makedirs(base_documents_dir)
        print(f"Created directory: {base_documents_dir}")

    # 起動時にファイルをコピー
    copy_file_to_documents("images//default_character.png","images//default_character.png")
    copy_file_to_documents("images//史風 鈴(pose).png","images//史風 鈴(pose).png")
    copy_file_to_documents("ng//NG変換ワード.csv","ng//NG変換ワード//NG変換ワード.csv")
    copy_file_to_documents("ng//禁止ワード.csv","ng//禁止ワード//禁止ワード.csv")
    copy_file_to_documents("settings.ini","settings//settings.ini")
    copy_file_to_documents("characters.ini","characters//characters.ini")

    app = AIVtuberApp(page)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    ft.app(target=main)
