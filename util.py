import re
import webcolors
from dateutil.parser import parse
import dearpygui.dearpygui as dpg
import traceback


def split_condition(condition):
    if condition is None:
        return []
    # 比較演算子にマッチする正規表現パターン
    pattern = r'(<=|>=|!=|==|>|<)'
    # 条件式を比較演算子で分割
    parts = re.split(pattern, condition)
    # 分割された各部分をトリム（前後の空白を削除）して返す
    return [part.strip() for part in parts]


def merge_dicts(base, update):
    """
    2つの辞書をマージする関数。リスト内の辞書も特定のキーに基づいてマージします。
    """
    if base is None:
        print("base is None")
        base = {
            "title": "Plot Title",
            "xAxis": {"label": "X軸", "columns": []},
            "yAxis": {"label": "Y軸", "columns": []},
            "series": [],
            "legend": {"position": None},
            "options": {"gridLines": True}
        }

    merged = base.copy()  # ベースの辞書をコピー
    print(update)
    for key, value in update.items():
        # ベースとアップデートの両方でキーが存在する場合
        if key in merged:
            if isinstance(merged[key], dict) and isinstance(value, dict):
                # 両方の値が辞書の場合、再帰的にマージ
                merged[key] = merge_dicts(merged[key], value)
            elif isinstance(merged[key], list) and isinstance(value, list):
                # 両方の値がリストの場合、特別なマージ処理を行う
                merged[key] = merge_lists(merged[key], value)
            else:
                # それ以外の場合、アップデートの値で上書き
                merged[key] = value
        else:
            # キーがベースに存在しない場合、アップデートの値を追加
            merged[key] = value

    return merged


def merge_lists(base_list, update_list):
    """
    2つのリストをマージする関数。辞書が含まれる場合、特定のキーに基づいてマージを試みる。
    """
    # マージされたリストを作成
    merged_list = base_list.copy()  # ベースのリストをコピー

    # ラベルに基づいて更新または追加
    for update_item in update_list:
        if isinstance(update_item, dict):
            # 更新項目が辞書の場合、一致するラベルを持つ既存の辞書を探す
            label = update_item.get('label')
            existing_item = next((item for item in merged_list if isinstance(
                item, dict) and item.get('label') == label), None)
            if existing_item:
                # 一致するラベルが見つかった場合、辞書をマージ
                merged_list[merged_list.index(existing_item)] = merge_dicts(
                    existing_item, update_item)
            else:
                # 一致するラベルがない場合、辞書を追加
                merged_list.append(update_item)
        else:
            # 更新項目が辞書でない場合、単純に追加
            if update_item not in merged_list:
                merged_list.append(update_item)

    return merged_list


def print_exception_info(e):
    # エラーの型とメッセージを表示
    print(f"Error type: {type(e).__name__}, Message: {str(e)}")

    # スタックトレースを表示
    print("\nStack Trace:")
    traceback.print_tb(e.__traceback__)

    # 例外オブジェクトのすべての属性を表示
    print("\nException attributes:")
    for attr in dir(e):
        # 特定の属性を表示
        print(f"{attr}: {getattr(e, attr, 'Not Available')}")


def check_column_exists(df, column_name):
    """
    指定したデータフレームに指定した名前の列が存在するか確認する。

    Parameters:
    - df: pd.DataFrame
        操作対象のデータフレーム
    - column_name: str
        確認したい列名

    Returns:
    - 存在する場合は True、存在しない場合はFalse
    """
    if column_name in df.columns:
        return True  # 列が存在する
    else:
        return False


def check_column_match(df, column_name):
    """
    指定したデータフレームにおいて、指定した名前の列がデータフレーム内に完全一致、
    大文字小文字が異なる形で一致、または全く一致しないかを確認し、その結果に応じて
    異なる値を返す。

    Parameters:
    - df: pd.DataFrame
        操作対象のデータフレーム。
    - column_name: str
        確認したい列名。

    Returns:
    - tuple: (状態コード, 正しい列名またはNone)
        状態コードは以下のとおり:
        0: 指定された列名がデータフレームに完全一致する場合。
        1: 指定された列名が大文字小文字の違いを除いてデータフレームに一致する場合。この場合、
           データフレームの正しい列名が返される。
        -1: 指定された列名がデータフレームに一致しない場合。
    """
    # 列名を小文字に統一したリストを作成し、その元の列名も保持する
    lower_case_columns = {col.lower(): col for col in df.columns}
    # 指定された列名も小文字に変換
    lower_case_column_name = column_name.lower()

    if column_name in df.columns:
        return 0, column_name  # 列が完全に一致する
    elif lower_case_column_name in lower_case_columns:
        # 大文字小文字が異なるが一致する場合、正しい列名を返す
        return 1, lower_case_columns[lower_case_column_name]
    else:
        return -1, None  # 列が一致しない


def on_window_close(sender, app_data, user_data):
    # workaround
    children_dict = dpg.get_item_children(sender)
    for key in children_dict.keys():
        for child in children_dict[key]:
            dpg.delete_item(child)

    dpg.delete_item(sender)
    print("window was deleted")


def sum_values_for_duplicate_keys(x, y):
    # 空の辞書を初期化
    result_dict = {}

    # xとyの要素をループで回す
    for key, value in zip(x, y):
        # キーが既に辞書に存在する場合は、値を合計する
        if key in result_dict:
            result_dict[key] += value
        else:
            # そうでなければ、新しいキーと値のペアを辞書に追加
            result_dict[key] = value

    # 辞書からx_listとy_listを作成
    x_list = list(result_dict.keys())
    y_list = list(result_dict.values())

    return x_list, y_list


def to_rgb_tuple(input_color):
    # RGBやRGBAの形式を直接解析
    rgb_match = re.match(r'RGB\((\d+),\s*(\d+),\s*(\d+)\)',
                         input_color, re.IGNORECASE)
    rgba_match = re.match(
        r'RGBA\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)', input_color, re.IGNORECASE)

    if rgb_match:
        return tuple(map(int, rgb_match.groups()))
    elif rgba_match:
        return tuple(map(int, rgba_match.groups()[:3]))
    else:
        # Hexコードまたはカラー名をRGBに変換
        if input_color.startswith('#'):
            hex_code = input_color.lstrip('#')
            if len(hex_code) == 3:
                hex_code = ''.join([c*2 for c in hex_code])
            return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
        else:
            try:
                hex_code = webcolors.name_to_hex(input_color).lstrip('#')
                return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
            except ValueError:
                return "Invalid input color format."


def is_time_expression(input_str):
    # 入力が数値 (intまたはfloat) の場合はFalseを返す
    if isinstance(input_str, (int, float)):
        return False

    try:
        # 入力文字列を解析してdatetimeオブジェクトを得る
        parse(input_str, fuzzy=False)
        return True
    except ValueError:
        # 解析できなかった場合はFalseを返す
        return False
