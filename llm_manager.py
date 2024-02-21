from llama_cpp import Llama
import json

def preprocess_json(json_str):
    # 最初の '{' の位置を見つけます
    start_index = json_str.find('{')
    # 最後の '}' の位置を見つけます
    end_index = json_str.rfind('}')
    # 最初の '{' より前と最後の '}' より後を削除します
    cleaned_json_str = json_str[start_index:end_index+1]
    return cleaned_json_str

class LLM_Manager:
    def __init__(self, model_path="./models/ELYZA-japanese-CodeLlama-7b-instruct-q4_K_M.gguf", n_ctx=2048):
        self.llm = Llama(model_path=model_path,
                         chat_format="llama-2", n_ctx=n_ctx)
        
    def infer(self, messages:list, system_prompt:str, temperature:float=0.7, use_json:bool=False):
        messages = [{"role": "system", "content": f"{system_prompt}"}] + messages
        print(messages)
        result = self.llm.create_chat_completion(messages=messages, temperature=temperature, response_format={
                                                 "type": "json_object"} if use_json == True else None)
        result = result["choices"][0]["message"]["content"].replace("\\n", "\n")
        print(result)
        return result

    def default_infer(self, system_prompt:str, user_prompt:str, temperature:float=0.7, use_json:bool=False):
        messages = [{"role": "system", "content": f"{system_prompt}", },
                    {"role": "user", "content": f"{user_prompt}"},]
        print(messages)
        result = self.llm.create_chat_completion(messages=messages, temperature=temperature, response_format={
                                                 "type": "json_object"} if use_json == True else None)
        result = result["choices"][0]["message"]["content"].replace("\\n", "\n")
        print(result)
        return result
    
    def json_infer(self, user_prompt:str, system_prompt:str="You are a convenient and friendly plotting assistant that outputs in JSON. Please reply with concise JSON in the format specified to assist in plotting.", temperature:float=0.7):
        json_str = preprocess_json(self.default_infer(user_prompt=user_prompt, system_prompt=system_prompt, temperature=temperature, use_json=True))
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