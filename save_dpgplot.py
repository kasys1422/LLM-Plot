import numpy as np
import dearpygui.dearpygui as dpg
import tkinter as tk
from tkinter import filedialog

# グローバル変数の定義
file = ""
x_left, y_left, x_span, y_span = 0, 0, 0, 0

def _framebuffer_callback(sender, user_data):
    """フレームバッファからの画像データをクロップして保存するコールバック関数"""
    global file, x_left, y_left, x_span, y_span
    w, h = user_data.get_width(), user_data.get_height()
    image = np.frombuffer(user_data, dtype=np.float32, count=w*h*4)
    image = np.reshape(image, (h, w, 4))
    image = image[y_left:y_left + y_span, x_left:x_left + x_span, :]
    image = image.flatten()
    image[:] *= 255
    dpg.save_image(file, x_span, y_span, image)

def crop_region_and_save(filepath, window_tag, start, end):
    """指定されたウィンドウ内の領域をクロップして保存する関数"""
    global file, x_left, y_left, x_span, y_span
    file = filepath
    # ウィンドウの位置を取得してオフセットに使用
    window_pos = dpg.get_item_pos(window_tag)
    
    # 開始と終了位置にウィンドウの位置をオフセットとして加える
    start = (start[0] + window_pos[0], start[1] + window_pos[1])
    end = (end[0] + window_pos[0], end[1] + window_pos[1])

    start, end = clip_region(start, end)  # 領域のクリッピング
    x_left, y_left = start
    x_span, y_span = end[0] - start[0], end[1] - start[1]
    dpg.output_frame_buffer(callback=_framebuffer_callback)

def clip_region(start, end):
    """領域を画面サイズに合わせてクリップする関数"""
    clip_x = np.clip([round(start[0]), round(end[0])], a_min=0, a_max=dpg.get_viewport_client_width())
    clip_y = np.clip([round(start[1]), round(end[1])], a_min=0, a_max=dpg.get_viewport_client_height())
    start = (clip_x[0], clip_y[0])
    end = (clip_x[1], clip_y[1])
    return start, end

def save_item(sender, user_data, args):
    """Dear PyGuiウィジェットから画像を保存する関数"""
    window_tag, plot_tag, filepath = args[0], args[1], args[2]
    start_x, start_y = dpg.get_item_pos(plot_tag)
    end_x, end_y = dpg.get_item_rect_size(plot_tag)
    # ウィンドウのタグを使用してオフセットを加えたクロップ領域を保存
    crop_region_and_save(filepath, window_tag, (start_x, start_y), (start_x + end_x, start_y + end_y))

def save_item_with_ui(sender, user_data, args):
    """
    Tkinter UIを使用して保存先を選択し、Dear PyGuiウィジェットから画像を保存する関数。
    sender: イベントを送信した要素
    user_data: 関数に渡されるユーザーデータ
    args: (window_tag, plot_tag)のタプル。window_tagはウィンドウのタグ、plot_tagはプロットのタグ
    """
    # Tkinterのルートウィンドウを初期化（ウィンドウは表示されない）
    root = tk.Tk()
    root.withdraw()  # ダイアログのみ表示するためにルートウィンドウを隠す

    # ファイル保存ダイアログを開いてファイルパスを取得
    filepath = filedialog.asksaveasfilename(
        initialdir="/", 
        title="Save Image As",
        filetypes=(("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("BMP files", "*.bmp"), ("TGA files", "*.tga"), ("HDR files", "*.hdr"))
    )

    # ファイルパスが指定された場合にのみ保存処理を実行
    if filepath:
        # argsにfilepathを追加してsave_item関数を呼び出す
        save_item(sender, user_data, args + (filepath,))