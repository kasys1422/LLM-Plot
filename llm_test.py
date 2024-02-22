from llama_cpp import Llama
from llm_manager import LLM_Tools
llm = LLM_Tools()
# result = llm.create_chat_completion(
#     messages=[
#         {
#             "role": "system",
#             "content": "You are a helpful plotting assistant that outputs in JSON. プロットを補助するために指定された形式のJSONを返してください。",
#         },
#         {"role": "user", "content": """
# ## 入力データ(head)
#       Month    Product  Sales
# 0   2023-01  Product A    784
# 1   2023-01  Product B    659
# 2   2023-01  Product C    729
# 3   2023-01  Product D    292
# 4   2023-01  Product E    935

# # 指示
# 月別の商品売上データをプロットしてください
         
# # 形式
# {
#   "title": "プロットのタイトル",
#   "xAxis": {
#     "label": "X軸のラベル",
#     "columns": ["x1", "x2"] // 複数のX軸データ列
#   },
#   "yAxis": {
#     "label": "Y軸のラベル",
#     "columns": ["y1", "y2"] // 複数のY軸データ列
#   },
#   "series": [
#     {
#       "label": "データセットn",
#       "type": "line/bar/circle/scatter",
#       "xColumn": "xn",
#       "yColumn": "yn",
#       "color": "some color"
#     },
#     ...
#   ],
#   "legend": {
#     "position": "top-right"
#   },
#   "options": {
#     "gridLines": true,
#     "dataPoints": true
#   }
# }
# """},
#     ],
#     response_format={
#         "type": "json_object",
#     },
#     temperature=0.7,
#     max_tokens=1024
# )

result = llm.is_plot_making("タイトルをテストに変更してください")
print(result)
