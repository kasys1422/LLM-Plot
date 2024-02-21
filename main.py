import json
import threading
import time
import dearpygui.dearpygui as dpg
from thirdparty.DearPyGui_Markdown.DPG_Markdown_Util import *
from plot_manager import Plot_Manager
from llm_manager import LLM_Manager
from config_manager import ConfigManager
from util import *

class ChatManager:
    def __init__(self):
        self.messages = []

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})
        print(self.messages)

    def delete_message(self, index=-1):
        if not self.messages:
            return  # メッセージがない場合は何もしない
        # indexが指定されないか、範囲外の場合は最新のメッセージを削除
        if index < 0 or index >= len(self.messages):

            print(self.messages.pop())
        else:
            del self.messages[index]
        print(self.messages)

    def reset_messages(self):
        self.messages.clear()

    def get_messages(self):
        return self.messages


class ChatUI:
    def __init__(self, chat_manager):
        self.chat_manager = chat_manager

    def refresh_chat(self):
        dpg.delete_item("chat_window", children_only=True)
        for msg in self.chat_manager.get_messages():
            dpg_markdown.add_text(f"**[{msg['role']}]**", parent="chat_window")
            with dpg.group(horizontal=True, parent="chat_window"):
                dpg.add_text(f"", indent=1)
                dpg_markdown.add_text(f"{msg['content']}")

    def setup_ui(self):
        with dpg.window(label="Chat UI", tag="chat_window"):
            pass
        with dpg.window(label="Controls"):
            dpg.add_input_text(label="Role", tag="role_input")
            dpg.add_input_text(label="Message", tag="message_input")
            dpg.add_button(label="Send Message", callback=self.send_message)
            dpg.add_button(label="Delete Latest Message",
                           callback=lambda: self.delete_message())
            dpg.add_input_int(label="Delete Message Index",
                              tag="delete_input", default_value=-1)
            dpg.add_button(label="Delete Message by Index", callback=lambda: self.delete_message(
                dpg.get_value("delete_input")))
            dpg.add_button(label="Reset All Messages",
                           callback=self.reset_messages)

    def send_message(self, role, message):
        self.chat_manager.add_message(role, message)
        self.refresh_chat()

    def send_message_from_ui(self):
        role = dpg.get_value("role_input")
        message = dpg.get_value("message_input")
        self.send_message(role, message)

    def delete_message(self, index=-1):
        self.chat_manager.delete_message(index)
        self.refresh_chat()

    def reset_messages(self):
        self.chat_manager.reset_messages()
        self.refresh_chat()
        self.unlock_ui()

    def lock_ui(self):
        dpg.disable_item("send_button")
        dpg.disable_item("reset_chat")

    def unlock_ui(self):
        dpg.enable_item("send_button")
        dpg.enable_item("reset_chat")


def main():
    cm = ConfigManager("./config.json")
    chat_manager = ChatManager()
    chat_ui = ChatUI(chat_manager)

    llm = LLM_Manager()
    default_window_size = [1280, 720]
    dpg.create_context()
    pm = Plot_Manager("Plot window", llm)

    setup_dpg_markdown()

    with dpg.window(tag="Main Window", label="Main Window"):
        with dpg.menu_bar():
            with dpg.menu(label="ファイル"):
                dpg.add_menu_item(label="CSVを開く", callback=pm.load_csv_file)
            with dpg.menu(label="ツール"):
                dpg.add_menu_item(label="Plot Viewer", callback=pm.create_plot)
                dpg.add_menu_item(
                    label="Plot Editor", callback=pm.je.create_ui)
                dpg.add_menu_item(label="Data Viewer", callback=pm.dfv.show)
                dpg.add_menu_item(
                    label="Style Editor", callback=lambda: dpg.show_tool(dpg.mvTool_Style))
        with dpg.group(horizontal=True):
            with dpg.child_window(width=-1, height=-1):
                with dpg.group(horizontal=True):
                    dpg.add_text("AI Chat")
                    dpg.add_button(label="Reset", tag="reset_chat",
                                   width=100, callback=chat_ui.reset_messages)
                with dpg.child_window(id="chat_window", height=int(default_window_size[1]-210), horizontal_scrollbar=True):
                    pass
                with dpg.child_window(id="bottom_buttons"):
                    with dpg.group(horizontal=True):
                        def send_message_start_thread():
                            thread = threading.Thread(
                                target=send_message, args=[], name='llm_infer', daemon=True)
                            thread.start()

                        # チャット処理関数
                        def send_message():
                            # メッセージを取得
                            message = dpg.get_value("message_input")
                            # UI処理
                            chat_ui.send_message("User", message)
                            chat_ui.lock_ui()  # UIをロック
                            # ユーザー入力を識別
                            type_from_ui = dpg.get_value("ai_type")
                            print(type_from_ui)
                            time.sleep(0.2)
                            if type_from_ui == "Auto":
                                chat_ui.send_message("Assistant", f"思考中...")
                                try:
                                    result, json_str = llm.json_infer(
                                        f"「{message}」" + '''の内容はどのような質問ですか？プロットの実行や描画、作成、プロット内容（タイトル、軸ラベル、色、凡例など）の変更を指示する内容なら"plot"、データや統計に関する質問なら"data"、その他の内容なら"chat"を必ず単一のJSON形式（{"type": "種類"}）で回答してください。''', "You are an assistant who briefly answers the questions asked. Please answer all questions in JSON format.", 0.2)
                                    print(json_str)
                                    ai_type = result["type"]
                                except Exception as e:
                                    print_exception_info(e)
                                    ai_type = "other"

                                chat_ui.delete_message()
                            else:
                                ai_type = {
                                    "Plot": "plot",
                                    "Chat": "other",
                                    "Data": "data"
                                }[type_from_ui]
                            print(ai_type)
                            # プロットの場合
                            if ai_type == "plot":
                                if pm.df is None:
                                    chat_ui.send_message(
                                        "Assistant", f"CSVを読み込んでください。")
                                    chat_ui.unlock_ui()
                                    return

                                chat_ui.send_message(
                                    "Assistant", f"プロットを作成中...")

                                prompt = f"""Create or edit the JSON file according to the following orders and information. However, in the case of editing, only the difference JSON should be output.
# Order
{message}

# DataFrame (Head)
{pm.df.head(5)}

# DataFrame imformation
{str(pm.column_info.get_column_info())}

""" + (f"# Now JSON Plot Paramater(Editable)\n{json.dumps(pm.plot_dict, ensure_ascii=False, indent=1)}\n" if pm.plot_dict is not None else "", message)[0]

                                system_prompt = """You are a convenient and friendly plotting assistant that outputs in JSON. Please reply with concise JSON in the format specified to assist in plotting.
## Default JSON Plot Format
{
"title": "プロットのタイトル",
"xAxis": {
  "label": "X軸のラベル",
  "columns": ["x1", "x2"], // 複数のX軸データ列
},
"yAxis": {
  "label": "Y軸のラベル",
  "columns": ["y1", "y2"], // 複数のY軸データ列
},
"ylabel2": "y軸のラベル(2軸目)" or null ,
"series": [
  {
    "label": "データセットn",
    "filter": ["Column == 'データセットn'"などのpandasのフィルタ構文, ...] / [null],
    "type": "line/bar/pie/scatter",  
    "xColumn": "xn",
    "yColumn": "yn",
    "color": "some color(HEX)"
  },
  ...
],
"legend": null or "top-rightのような位置指定",
"options": {
  "gridLines": bool
}
}

"""
                                print(prompt)
                                try:
                                    result, json_str = llm.json_infer(
                                        prompt, system_prompt)
                                    print(json_str)
                                    if pm.plot_dict is not None:
                                        result = merge_dicts(pm.plot_dict, result)
                                        print(f"marged dict \n{json.dumps(result, ensure_ascii=False, indent=2)}")
                                    pm.set_plot_json(result)
                                    pm.je.set_json(result)
                                    pm.create_plot()
                                    chat_ui.delete_message()
                                    chat_ui.send_message(
                                        "Assistant", f"プロットを作成しました。")
                                except Exception as e:
                                    print_exception_info(e)
                                    chat_ui.delete_message()
                                    chat_ui.send_message(
                                        "Assistant", f"プロットの作成に失敗しました。")
                                chat_ui.unlock_ui()

                            elif ai_type == "data":
                                if pm.df is None:
                                    chat_ui.send_message(
                                        "Assistant", f"CSVを読み込んでください。")
                                    chat_ui.unlock_ui()
                                    return
                                chat_ui.send_message("Assistant", f"思考中...")
                                result = llm.infer([
                                    {"role": "assistant",
                                        "content": f"こんにちは。データに関してなにかお手伝いできますか？", },
                                    {"role": "user", "content": f"{message}"},],
                                    f"""Assistantは優秀で親切なアシスタントです。Assistantは以下のデータ(Userには見えない)を見やすく整形してUserに提供してください。
# DataFrame (Head)
{pm.df.head(5)}
# DataFrame Columns imformation
{str(pm.column_info.get_column_info())}
# DataFrame Statistics imformation
{str(pm.dfv.get_statistics(pm.df))}
""" + (f"# Plot Settings\n{json.dumps(pm.plot_dict, ensure_ascii=False, indent=1)}" if pm.plot_dict is not None else "")[0])

                                chat_ui.delete_message()
                                chat_ui.send_message("Assistant", result)
                                chat_ui.unlock_ui()

                            else:
                                messages = chat_ui.chat_manager.messages.copy()
                                chat_ui.send_message("Assistant", f"思考中...")
                                result = llm.infer(
                                    messages, """AssistantはCSVデータのプロットに関する優秀で親切なアシスタント「Plot AI」です。Userと会話してください。""")

                                chat_ui.delete_message()
                                chat_ui.send_message("Assistant", result)
                                chat_ui.unlock_ui()

                        dpg.add_input_text(
                            label="", tag="message_input", multiline=False, width=int(default_window_size[1]-240), height=60, callback=send_message_start_thread, on_enter=True)
                        dpg.add_combo(items=[
                            "Auto", "Chat", "Plot", "Data"], default_value="Auto", tag=f"ai_type", width=90)
                        dpg.add_button(label="Send", tag="send_button",
                                       width=60, callback=send_message_start_thread)

    # ウインドウ更新時の処理
    def viewport_update():
        dpg.set_item_height("chat_window", dpg.get_viewport_height()-210)
        dpg.set_item_width("message_input", dpg.get_viewport_width()-240)

    pm.set_csv("./samples/monthly_sales_data.csv")

    pm.set_plot_json(json.loads("""
{
"title": "売上状況",
"xAxis": {
    "label": "月",
    "columns": ["Month"],
    "time": true
},
"yAxis": {
    "label": "売上高",
    "columns": ["Sales"],
    "time": false
},
"series": [
    {
    "label": "A",
    "filter": ["Product == 'Product A'"],
    "type": "bar",
    "xColumn": "Month",
    "yColumn": "Sales",
    "color": "blue"
    },
    {
    "label": "B",
    "filter": ["Product == 'Product B'"],
    "type": "bar",
    "xColumn": "Month",
    "yColumn": "Sales",
    "color": "green"
    },
    {
    "label": "C",
    "filter": ["Product == 'Product C'"],
    "type": "bar",
    "xColumn": "Month",
    "yColumn": "Sales",
    "color": "red"
    }
]
}
"""))
    pm.create_plot()

    dpg.set_viewport_resize_callback(viewport_update)

    # dpg.configure_app(docking=True)
    dpg.create_viewport(title='LLM Plot', width=1280, height=720)
    dpg.set_primary_window("Main Window", True)
    dpg.setup_dearpygui()
    dpg.show_viewport()

    while dpg.is_dearpygui_running():
        # insert here any code you would like to run in the render loop
        # you can manually stop by using stop_dearpygui()
        dpg.render_dearpygui_frame()

    dpg.destroy_context()
    cm.save_config()


if __name__ == "__main__":
    main()
