import dearpygui.dearpygui as dpg
import numpy as np
import pandas as pd
from save_dpgplot import save_item_with_ui
import tkinter as tk
from tkinter import filedialog
from theme import theme_manager
from util import *
from json_editor import JsonEditor


class PandasDataFrameViewer:
    def __init__(self, title):
        self.title = title
        self.dataframe = None  # DataFrameの初期値をNoneに設定
        self.tab_bar_id = None

    def set_df(self, dataframe, update=False):
        self.dataframe = dataframe
        if update:
            if self.dataframe is not None and not self.dataframe.empty:
                self.update(self.dataframe)
            else:
                self.show_no_data()

    def show(self):
        if not dpg.does_item_exist(self.title):
            with dpg.window(label=self.title, tag=self.title):
                self.tab_bar_id = dpg.add_tab_bar()
                if self.dataframe is not None and not self.dataframe.empty:
                    self.split_dataframe_and_create_tabs(self.dataframe)
                    self.add_statistics_tab(self.dataframe)
                else:
                    self.show_no_data()

    def split_dataframe_and_create_tabs(self, dataframe):
        columns_per_tab = 60
        total_columns = len(dataframe.columns)
        num_tabs = (total_columns - 1) // columns_per_tab + 1

        for i in range(num_tabs):
            start_col = i * columns_per_tab
            end_col = min(start_col + columns_per_tab, total_columns)
            df_subset = dataframe.iloc[:, start_col:end_col]
            tab_label = f"Columns {start_col+1}-{end_col}"
            with dpg.tab(label=tab_label, parent=self.tab_bar_id):
                self.create_table(df_subset)

    def create_table(self, dataframe):
        with dpg.table(header_row=True, borders_outerH=True, borders_innerV=True, borders_innerH=True, borders_outerV=True, row_background=True):
            for column in dataframe.columns:
                dpg.add_table_column(label=column)
            for index, row in dataframe.iterrows():
                with dpg.table_row():
                    for item in row:
                        dpg.add_text(str(item))

    def get_statistics(self, dataframe):
        stats_df = dataframe.describe().transpose()
        stats_df.insert(0, 'Column Name', stats_df.index)
        return stats_df

    def add_statistics_tab(self, dataframe):
        stats_df = self.get_statistics(dataframe)
        tab_label = "Statistics"
        with dpg.tab(label=tab_label, parent=self.tab_bar_id):
            self.create_table(stats_df)

    def show_no_data(self):
        if dpg.does_item_exist(self.tab_bar_id):
            dpg.delete_item(self.tab_bar_id, children_only=True)
        with dpg.tab(label="No Data", parent=self.tab_bar_id):
            dpg.add_text("No data available.")

    def update(self, dataframe):
        self.dataframe = dataframe
        if dpg.does_item_exist(self.tab_bar_id):
            dpg.delete_item(self.tab_bar_id, children_only=True)
        self.tab_bar_id = dpg.add_tab_bar(parent=self.title)
        if self.dataframe is not None and not self.dataframe.empty:
            self.split_dataframe_and_create_tabs(dataframe)
            self.add_statistics_tab(dataframe)
        else:
            self.show_no_data()


class DataFrameColumnInfo:
    def __init__(self, dataframe):
        self.df = dataframe
        self.column_info = self.analyze_column_info()

    def analyze_column_info(self):
        column_dict = {}
        for column in self.df.columns:
            if self.df[column].dtype == 'object':
                column_dict[column] = {
                    'type': 'str', 'unique_values': self.df[column].unique().tolist()}
            elif np.issubdtype(self.df[column].dtype, np.number):
                column_dict[column] = {'type': 'num'}
            elif self.df[column].dtype == 'bool':
                column_dict[column] = {'type': 'bool'}
            else:
                column_dict[column] = {'type': 'Other'}
        return column_dict

    def get_column_info(self):
        return self.column_info


class Plot_Manager:
    def __init__(self, window_tag: str, llm):
        self.window_tag = window_tag
        self.df = None  # データフレームを保存するための変数
        self.tag_number = 0
        self.plot_dict = None
        self.column_info = None
        self.llm = llm
        self.dfv = PandasDataFrameViewer("Data Viewer")
        self.tm = theme_manager()
        self.tm.init_white_plot()
        self.je = JsonEditor(self)

    def set_csv(self, csv_path):
        self.df = pd.read_csv(csv_path)  # CSVファイルからデータフレームを読み込む
        self.column_info = DataFrameColumnInfo(self.df)
        self.dfv.set_df(self.df)
        try:
            dpg.set_viewport_title(title=f'LLM Plot ({csv_path})')
        except SystemError:
            pass

    # ファイル選択ダイアログを表示してCSVファイルを読み込む関数
    def load_csv_file(self):
        # Tkinterのルートウィンドウを作成して即座に非表示にする
        root = tk.Tk()
        root.withdraw()

        # ファイル選択ダイアログを開く
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")])

        # ファイルが選択された場合、Pandasで読み込む
        if file_path:
            self.set_csv(file_path)
        else:
            print("File selection cancelled.")

    def set_plot_json(self, plot_dict: dict):
        self.plot_dict = plot_dict

    def clear_plot(self):
        if dpg.does_item_exist(self.window_tag):
            dpg.delete_item(self.window_tag, children_only=True)
        if self.tag_number != 0:
            for i in range(self.tag_number):
                dpg.delete_item(f"series_{i}")
                dpg.delete_item(f"theme_series_{i}")
            self.tag_number = 0

    def create_plot(self):
        plot_dict = self.plot_dict
        self.clear_plot()
        if not dpg.does_item_exist(self.window_tag):
            with dpg.window(label='Plot window', tag=self.window_tag, width=600, height=400, on_close=on_window_close):
                pass
        with dpg.menu_bar(parent=self.window_tag):
            with dpg.menu(label="ファイル"):
                dpg.add_menu_item(label="名前をつけて保存", callback=save_item_with_ui, user_data=(
                    self.window_tag, f"{self.window_tag}_plot"))

        with dpg.plot(label=plot_dict.get("title", "Plot"), width=-1, height=-1, parent=self.window_tag, anti_aliased=True, tag=f"{self.window_tag}_plot"):
            if "legend" in plot_dict:
                if plot_dict["legend"]["position"] is not None:
                    try:
                        locations = {
                            "TopLeft": dpg.mvPlot_Location_NorthWest,
                            "TopCenter": dpg.mvPlot_Location_North,
                            "TopRight": dpg.mvPlot_Location_NorthEast,
                            "BottomLeft": dpg.mvPlot_Location_SouthWest,
                            "BottomCenter": dpg.mvPlot_Location_South,
                            "BottomRight": dpg.mvPlot_Location_SouthEast,
                            "Left": dpg.mvPlot_Location_West,
                            "Center": dpg.mvPlot_Location_Center,
                            "Right": dpg.mvPlot_Location_East,
                            "top-left": dpg.mvPlot_Location_NorthWest,
                            "top-center": dpg.mvPlot_Location_North,
                            "top-right": dpg.mvPlot_Location_NorthEast,
                            "bottom-left": dpg.mvPlot_Location_SouthWest,
                            "bottom-center": dpg.mvPlot_Location_South,
                            "bottom-right": dpg.mvPlot_Location_SouthEast,
                            "left": dpg.mvPlot_Location_West,
                            "center": dpg.mvPlot_Location_Center,
                            "right": dpg.mvPlot_Location_East,
                        }
                        print(plot_dict["legend"]["position"])
                        dpg.add_plot_legend(location=locations[plot_dict["legend"]["position"]])
                    except Exception as e:
                        print_exception_info(e)

            # 列名確認
            for i in range(len(plot_dict["series"])):
                for column_label in ["xColumn", "yColumn"]:
                    column_status, correct_column_info = check_column_match(
                        self.df, plot_dict["series"][i][column_label])
                    if str(column_status) == "1":
                        plot_dict["series"][i][column_label] = correct_column_info
                    if str(column_status) == "-1":
                        print("Column error")
                        try:
                            unique_data = self.df.columns.tolist()
                            result, json_str = self.llm.similarity_string_extraction(
                                plot_dict["series"][i][column_label], unique_data)
                            plot_dict["series"][i][column_label] = result["result"]
                            print(result)
                        except Exception as e:
                            print_exception_info(e)

            x_is_time = is_time_expression(
                self.df[plot_dict["series"][0]["xColumn"]].tolist()[-1])
            y_is_time = is_time_expression(
                self.df[plot_dict["series"][0]["yColumn"]].tolist()[-1])
            xaxis_id = dpg.add_plot_axis(
                dpg.mvXAxis, label=plot_dict["xAxis"]["label"], time=x_is_time)
            yaxis_id = dpg.add_plot_axis(
                dpg.mvYAxis, label=plot_dict["yAxis"]["label"], time=y_is_time)

            try:
                bar_series_count = sum(
                    1 for item in plot_dict["series"] if item["type"] == "bar")
            except KeyError:
                bar_series_count = 0
            series_count = len(plot_dict["series"])
            
            try:
                if plot_dict.get("options", {}).get("gridLines", False):
                    self.tm.init_white_plot()
                else:
                    self.tm.init_white_plot(True)
            except Exception as e:
                print_exception_info(e)

            for series in plot_dict["series"]:
                if not "type" in series:
                    series["type"] = "line"
                # フィルタ条件がある場合はフィルタリングを適用
                if "filter" in series:
                    filters = series["filter"]
                    backup_df = self.df
                    if filters is not None:
                        filtered_df = self.df
                        for i in range(len(filters)):
                            filter_condition = filters[i]
                            splited_filter_condition = split_condition(
                                filter_condition)
                            backup_df = filtered_df
                            try:
                                filtered_df = filtered_df.query(
                                    filter_condition)
                            except:
                                filtered_df = self.df
                                print("filter error")
                            for column_label in ["xColumn", "yColumn"]:
                                if len(filtered_df[series[column_label]]) == 0:
                                    print("filter len = 0")
                                    try:
                                        unique_data = self.column_info.get_column_info()[
                                            splited_filter_condition[0]]
                                        if unique_data["type"] == "str":
                                            filtered_df = backup_df
                                            result, json_str = self.llm.similarity_string_extraction(
                                                splited_filter_condition[2], unique_data["unique_values"])
                                            series["filter"][i] = f'{splited_filter_condition[0]} {splited_filter_condition[1]} \"{result["result"]}\"'
                                            print(series["filter"][i])
                                            filtered_df = filtered_df.query(
                                                series["filter"][i])

                                    except Exception as e:
                                        print_exception_info(e)
                    else:
                        filtered_df = self.df
                else:
                    filtered_df = self.df
                x_values = filtered_df[series["xColumn"]]
                y_values = filtered_df[series["yColumn"]]

                

                # X軸が時間データの場合
                if x_is_time:
                    x_values = pd.to_datetime(x_values).apply(
                        lambda x: x.timestamp())

                # Y軸が時間データの場合
                if y_is_time:
                    y_values = pd.to_datetime(y_values).apply(
                        lambda x: x.timestamp())

                # リストに変換
                x_values = x_values.tolist()
                y_values = y_values.tolist()

                # X軸が文字列データの場合

                x_is_str = False
                buffer = self.column_info.get_column_info()
                x_values, y_values = sum_values_for_duplicate_keys(
                    x_values, y_values)
                old_x_values = x_values
                if buffer[series["xColumn"]]["type"] == "str" and not x_is_time or series["type"] == "pie":
                    processed_list = [[str(item), index + 11]
                                      for index, item in enumerate(x_values)]
                    dpg.set_axis_ticks(
                        axis=xaxis_id, label_pairs=processed_list)
                    x_values = [index + 11 for index, _ in enumerate(x_values)]
                    x_is_str = True

                # 色の指定がない場合はリストから色を割り当て
                color = series.get("color", None)

                if "label" in series:
                    label = series["label"]
                    if label is None:
                        label = f"series_{self.tag_number}"
                else:
                    label = f"series_{self.tag_number}"
                tag = f"series_{self.tag_number}"

                if series["type"] == "line":
                    dpg.add_line_series(x_values, y_values,
                                        label=label, tag=tag, parent=yaxis_id)
                elif series["type"] == "bar":
                    if x_is_str == False:
                        weight = (max(x_values) - min(x_values)) / \
                            (len(x_values) * bar_series_count * 1.2)
                        dpg.add_bar_series([x + (weight * (self.tag_number-bar_series_count/2))
                                            for x in x_values], y_values, label=label, tag=tag, parent=yaxis_id, weight=weight)
                    else:
                        weight = 0.5
                        dpg.add_bar_series(
                            x_values, y_values, label=label, tag=tag, parent=yaxis_id, weight=weight)

                elif series["type"] == "scatter":
                    dpg.add_scatter_series(
                        x_values, y_values, label=label, tag=tag, parent=yaxis_id)
                elif series["type"] == "pie":
                    dpg.set_axis_limits(dpg.last_item(), 0, 1)
                    dpg.add_pie_series(
                        0.5, 0.5, 0.5, y_values, old_x_values, label=label, tag=tag, parent=yaxis_id)

                # 他のシリーズタイプについても同様に処理を追加してください

                # テーマ
                try:
                    with dpg.theme(tag=f"theme_series_{self.tag_number}"):
                        with dpg.theme_component(0):
                            if color is not None:
                                color = to_rgb_tuple(color)
                                dpg.add_theme_color(
                                    dpg.mvPlotCol_Line, color, category=dpg.mvThemeCat_Plots)
                                dpg.add_theme_color(
                                    dpg.mvPlotCol_Fill, color, category=dpg.mvThemeCat_Plots)
                                dpg.add_theme_color(
                                    dpg.mvPlotCol_MarkerOutline, color, category=dpg.mvThemeCat_Plots)
                                dpg.add_theme_color(
                                    dpg.mvPlotCol_MarkerFill, color, category=dpg.mvThemeCat_Plots)
                    if color is not None:
                        dpg.bind_item_theme(
                            f"series_{self.tag_number}", f"theme_series_{self.tag_number}")
                except Exception as e:
                    print_exception_info(e)
                self.tag_number += 1

