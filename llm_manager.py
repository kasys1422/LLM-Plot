from llama_cpp import Llama
import json

from util import merge_dicts


def preprocess_json(json_str):
    # 最初の '{' の位置を見つけます
    start_index = json_str.find('{')
    # 最後の '}' の位置を見つけます
    end_index = json_str.rfind('}')
    # 最初の '{' より前と最後の '}' より後を削除します
    cleaned_json_str = json_str[start_index:end_index+1]
    return cleaned_json_str


class LLM_Manager:
    def __init__(self, model_path="./models/ELYZA-japanese-CodeLlama-7b-instruct-q4_K_M.gguf", n_ctx=2048, n_gpu_layers=-1):
        self.llm = Llama(model_path=model_path,
                         chat_format="llama-2", n_ctx=n_ctx, n_gpu_layers=n_gpu_layers)

    def infer(self, messages: list, system_prompt: str, temperature: float = 0.7, use_json: bool = False):
        messages = [
            {"role": "system", "content": f"{system_prompt}"}] + messages
        print(messages)
        result = self.llm.create_chat_completion(messages=messages, temperature=temperature, response_format={
                                                 "type": "json_object"} if use_json == True else None)
        result = result["choices"][0]["message"]["content"].replace(
            "\\n", "\n")
        print(result)
        return result

    def default_infer(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, use_json: bool = False):
        messages = [{"role": "system", "content": f"{system_prompt}", },
                    {"role": "user", "content": f"{user_prompt}"},]
        print(messages)
        result = self.llm.create_chat_completion(messages=messages, temperature=temperature, response_format={
                                                 "type": "json_object"} if use_json == True else None)
        result = result["choices"][0]["message"]["content"].replace(
            "\\n", "\n")
        print(result)
        return result

    def json_infer(self, user_prompt: str, system_prompt: str = "You are a convenient and friendly plotting assistant that outputs in JSON. Please reply with concise JSON in the format specified to assist in plotting.", temperature: float = 0.7):
        json_str = preprocess_json(self.default_infer(
            user_prompt=user_prompt, system_prompt=system_prompt, temperature=temperature, use_json=True))
        try:
            # 文字列を辞書に変換
            dict = json.loads(json_str)
            print("JSONとして問題ありません。辞書に格納されました。")
            print(dict)  # JSONから変換された辞書を表示
            return dict, json_str
        except ValueError as e:
            # JSON形式が無効な場合のエラー処理
            print("JSONとして無効です。エラー:", e)
            print(json_str)

    def json_infer_with_messages(self, messages: str, system_prompt: str = "You are a convenient and friendly plotting assistant that outputs in JSON. Please reply with concise JSON in the format specified to assist in plotting.", temperature: float = 0.7):
        json_str = preprocess_json(self.infer(
            messages=messages, system_prompt=system_prompt, temperature=temperature, use_json=True))
        try:
            # 文字列を辞書に変換
            dict = json.loads(json_str)
            print("JSONとして問題ありません。辞書に格納されました。")
            print(dict)  # JSONから変換された辞書を表示
            return dict, json_str
        except ValueError as e:
            # JSON形式が無効な場合のエラー処理
            print("JSONとして無効です。エラー:", e)
            print(json_str)


class LLM_Tools(LLM_Manager):
    def __init__(self, model_path="./models/ELYZA-japanese-CodeLlama-7b-instruct-q4_K_M.gguf", n_ctx=2048, n_gpu_layers=-1):
        super().__init__(model_path, n_ctx, n_gpu_layers)

    def message_classification(self, message: str):
        """
        入力されたメッセージを分類するメソッド
        """
        result, json_str = self.json_infer(
            f"「{message}」" + '''の内容はどのような質問ですか？
プロットの実行や描画、作成、プロット内容（タイトル、軸ラベル、色、凡例など）の変更を指示する内容なら"plot"、データや統計に関する質問なら"data"、その他の内容なら"chat"を必ず単一のJSON形式（{"type": "種類"}）で回答してください。''',
            "You are the assistant who will classify the questions entered. Be sure to answer in the specified JSON format.", 0.2)
        print(json_str)
        return result["type"]

    def similarity_string_extraction(self, word: str, list: list):
        """
        リストから類似文字列を抽出するメソッド
        """
        prompt = f"""「{word}」の意味は{list}のうち、どの単語に一番近いですか？回答形式は"""+"""
{"result": "単語"}
とします。
"""
        print(prompt)
        result, json_str = self.json_infer(
            prompt, "You are an assistant who briefly answers the questions asked. Please answer all questions in JSON format.", 0)
        return result
    
    def is_plot_making(self, message: str):
        """
        入力されたメッセージを分類するメソッド
        """
        result, json_str = self.json_infer(
            f'"{message}"' + '''の内容はどのような内容ですか？
            タイトル、軸ラベル、色、凡例などのプロットの追加や変更を指示する内容なら"edit"、
            プロットの作成を指示する内容なら"create"を必ず単一のJSON形式（{"type": "create / edit"}）で回答してください。''',
            "You are the assistant who will classify the questions entered. Be sure to answer in the specified JSON format.", 0)
        print(json_str)
        if result["type"] == "edit":
            return False
        else:
            return True 

    def plot(self, message: str, df_head, column_info, now_dict):
        """
        プロット形式のJSONを作成するメソッド
        """
        # 新規作成
        if self.is_plot_making(message):
            prompt = """Create or edit the JSON file according to the following orders and information.
        
"""+f"""
以下の指示をもとにDataFrame情報を使用してプロットのJSONを作成してください。内容は必ずDataFrameの要素を用いて構成してください。
# 指示
{message}
# DataFrame (Head)
{df_head}
# DataFrame imformation
{str(column_info)}"""

            system_prompt = """You are a convenient and friendly plotting assistant that outputs in JSON.
## Default JSON Plot Format
{
    "title": "プロットのタイトル",
    "xAxis": {
        "label": "X軸のラベル",
        "columns": ["列名_x_1", "列名_x_2"], // 複数のX軸データ列
    },
    "yAxis": {
        "label": "Y軸のラベル",
        "columns": ["列名_y_1", "列名_y_2"], // 複数のY軸データ列
    },
    "series": [
        {
            "label": "ラベル",
            "filter": ["Column == '列名'"などのpandasのフィルタ構文, ...] / [null],
            "type": "line/bar/pie/scatter",  
            "xColumn": "列名_x_1",
            "yColumn": "列名_y_1",
            "color": "some color(HEX)"
        },
        ...
    ],
    "legend": {
        "position": null or "top-rightのような位置指定"
    }
    "options": {
        "gridLines": bool
    }
}
"""
            result, _ = self.json_infer(prompt, system_prompt)
            try:
                result = merge_dicts(None, result)
            except:
                pass
        # 更新
        else:
            prompt = """Create or edit the JSON file according to the following orders and information. However, in the case of editing, only the difference JSON should be output.
        
"""+f"""
以下の指示に合わせてプロットのJSONの変更部分の差分を作成してください。
# 指示
{message}
# DataFrame (Head)
{df_head}
# DataFrame imformation
{str(column_info)}"""

            system_prompt = """You are a convenient and friendly plotting assistant that outputs in JSON. Please reply with concise JSON in the format specified to assist in plotting.
## Default JSON Plot Format
{
    "title": "プロットのタイトル",
    "xAxis": {
        "label": "X軸のラベル",
        "columns": ["列名_x_1", "列名_x_2"], // 複数のX軸データ列
    },
    "yAxis": {
        "label": "Y軸のラベル",
        "columns": ["列名_y_1", "列名_y_2"], // 複数のY軸データ列
    },
    "series": [
        {
            "label": "ラベル",
            "filter": ["Column == '列名'"などのpandasのフィルタ構文, ...] / [null],
            "type": "line/bar/pie/scatter",  
            "xColumn": "列名_x_1",
            "yColumn": "列名_y_1",
            "color": "some color(HEX)"
        },
        ...
    ],
    "legend": {
        "position": null or "top-rightのような位置指定"
    }
    "options": {
        "gridLines": bool
    }
}
"""
            result, _ = self.json_infer_with_messages([{"role": "user", "content": f"プロットを作成してください。", },
                                           {"role": "assistant",
                                            "content": f"{json.dumps(now_dict, ensure_ascii=False, indent=1)}"},
                                           {"role": "user", "content": f"{prompt}", }], system_prompt)
            result = merge_dicts(now_dict, result)
        return result

    def chat(self, messages):
        """
        docstring
        """
        result = self.infer(
            messages, """AssistantはCSVデータのプロットに関する優秀で親切なアシスタント「Plot AI」です。Userと会話してください。""")
        return result

    def data(self, message: str, df_head, column_info, now_dict, statistics):
        """
        docstring
        """
        result = self.infer([
            {"role": "assistant",
             "content": f"こんにちは。データに関してなにかお手伝いできますか？", },
            {"role": "user", "content": f"{message}"},],
            f"""Assistantは優秀で親切なアシスタントです。Assistantは以下のデータ(Userには見えない)を見やすく整形してUserに提供してください。
# DataFrame (Head)
{df_head}
# DataFrame Columns imformation
{str(column_info)}
# DataFrame Statistics imformation
{str(statistics)}
""" + (f"# Plot Settings\n{json.dumps(now_dict, ensure_ascii=False, indent=1)}" if now_dict is not None else "")[0])
        return result


def main():
    llm = LLM_Manager()
    result, json_str = llm.json_infer("""
reate or edit the JSON file according to the following orders and information.
# Order
凡例を右上に追加してください

# DataFrame (Head)
     Month    Product  Sales
0  2023-01  Product A    784
1  2023-01  Product B    659
2  2023-01  Product C    729

# DataFrame imformation
{'Month': {'type': 'str', 'unique_values': ['2023-01', '2023-02', '2023-03', '2023-04', '2023-05', '2023-06', '2023-07', '2023-08', '2023-09', '2023-10', '2023-11', '2023-12']}, 'Product': {'type': 'str', 'unique_values': ['Product A', 'Product B', 'Product C', 'Product D', 'Product E']}, 'Sales': {'type': 'num'}}

# Now Plot Settings JSON
{
 "title": "売上を線グラフにしました",
 "xAxis": {
  "label": "月",
  "columns": [
   "Month",
   "Month",
   "Month"
  ]
 },
 "yAxis": {
  "label": "売上高（万円）",
  "columns": [
   "Sales",
   "Sales",
   "Sales"
  ]
 },
 "series": [
  {
   "label": "Product A",
   "filter": [
    "Product == 'Product A'"
   ],
   "type": "line",
   "xColumn": "Month",
   "yColumn": "Sales",
   "color": "rgb(255, 0, 0)"
  },
  {
   "label": "Product B",
   "filter": [
    "Product == 'Product B'"
   ],
   "type": "line",
   "xColumn": "Month",
   "yColumn": "Sales",
   "color": "rgb(0, 255, 0)"
  },
  {
   "label": "Product C",
   "filter": [
    "Product == 'Product C'"
   ],
   "type": "line",
   "xColumn": "Month",
   "yColumn": "Sales",
   "color": "rgb(0, 0, 255)"
  }
 ],
 "options": {
  "gridLines": true
 },
 "legend": null
}
""", """You are a convenient and friendly plotting assistant that outputs in JSON. Please reply with concise JSON in the format specified to assist in plotting.
## default JSON style
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
""")

    print(json_str)


if __name__ == "__main__":
    main()


"""
## 入力データ(head)
      Month    Product  Sales
0   2023-01  Product A    784
1   2023-01  Product B    659
2   2023-01  Product C    729
3   2023-01  Product D    292
4   2023-01  Product E    935

# 指示
月別の商品売上データをプロットしてください
         
# 形式
{
  "title": "プロットのタイトル",
  "xAxis": {
    "label": "X軸のラベル",
    "columns": ["x1", "x2"] // 複数のX軸データ列
  },
  "yAxis": {
    "label": "Y軸のラベル",
    "columns": ["y1", "y2"] // 複数のY軸データ列
  },
  "ylabel2": "y軸のラベル(2軸目)"/null ,
  "series": [
    {
      "label": "データセットn",
      "type": "line/bar/circle/scatter",  
      "xColumn": "xn",
      "yColumn": "yn",
      "color": "some color"
    },
    ...
  ],
  "legend": {
    "position": "top-right"
  },
  "options": {
    "gridLines": true,
    "dataPoints": true
  }
}
"""
