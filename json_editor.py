
import dearpygui.dearpygui as dpg
from util import *


class JsonEditor:
    def __init__(self, pm):
        self.window_id = None
        self.json_data = None
        self.pm = pm

    def set_json(self, json_data):
        self.json_data = json_data
        if dpg.does_item_exist(self.window_id):
            self.create_ui()

    def create_ui(self):
        if self.json_data is None:
            self.json_data = {
                "title": "Plot Title",
                "xAxis": {"label": "X Axis Label", "columns": [list(self.pm.df.columns)[0]]},
                "yAxis": {"label": "Y Axis Label", "columns": [list(self.pm.df.columns)[1]]},
                "series": [
                    {
                        "label": "Dataset 1",
                        "type": "line",
                        "xColumn": list(self.pm.df.columns)[0],
                        "yColumn": list(self.pm.df.columns)[1],
                        "color": "#FF0000",
                        "filter": [None]
                    }
                ],
                "Legend": {"position": None},
                "options": {"gridLines": True}
            }
        if dpg.does_item_exist(self.window_id):
            dpg.focus_item(self.window_id)
            print("does_item_exist")
            dpg.delete_item(self.window_id, children_only=True)

        else:
            self.window_id = dpg.add_window(
                label="Plot Editor", tag="JsonEditorWindow", on_close=on_window_close)

        # Title
        try:
            json_title = self.json_data["title"]
        except:
            json_title = ""
        dpg.add_input_text(
            label="Title", default_value=json_title, parent=self.window_id, tag="json_title")

        # X Axis
        with dpg.group(label="X Axis", parent=self.window_id):
            try:
                xAxis_label = self.json_data["xAxis"]["label"]
            except:
                xAxis_label = "X"
            dpg.add_input_text(
                label="X Label", default_value=xAxis_label, tag="xAxis_label")

        # Y Axis
        with dpg.group(label="Y Axis", parent=self.window_id):
            try:
                yAxis_label = self.json_data["yAxis"]["label"]
            except:
                yAxis_label = "Y"
            dpg.add_input_text(
                label="Y Label", default_value=yAxis_label, tag="yAxis_label")

        # Options
        with dpg.group(label="Options", parent=self.window_id):
            try:
                gridLines = self.json_data["options"]["gridLines"]
            except:
                gridLines = True
            dpg.add_checkbox(
                label="Grid Lines", default_value=gridLines, tag="options_gridLines")
            try:
                legend = {
                    "TopLeft":      "TopLeft",
                    "TopCenter":    "TopCenter",
                    "TopRight":     "TopRight",
                    "BottomLeft":   "BottomLeft",
                    "BottomCenter": "BottomCenter",
                    "BottomRight":  "BottomRight",
                    "Left":         "Left",
                    "Center":       "Center",
                    "Right":        "Right",
                    "top-left":     "TopLeft",
                    "top-center":   "TopCenter",
                    "top-right":    "TopRight",
                    "bottom-left":  "BottomLeft",
                    "bottom-center": "BottomCenter",
                    "bottom-right": "BottomRight",
                    "left":         "Left",
                    "center":       "Center",
                    "right":        "Right",
                }[str(self.json_data["legend"]["position"])]
            except:
                legend = "None"
            dpg.add_combo(label="legend", items=["None",
                                                 "TopLeft",
                                                 "TopCenter",
                                                 "TopRight",
                                                 "BottomLeft",
                                                 "BottomCenter",
                                                 "BottomRight",
                                                 "Left",
                                                 "Center",
                                                 "Right"
                                                 ], default_value=legend, tag="options_legend")

        # Series
        dpg.add_child_window(
            parent=self.window_id, tag="series_group")
        self.refresh_series_ui()
        dpg.add_button(label="+ Add Series",
                       parent=self.window_id, callback=self.add_series)
        dpg.add_button(label="- Remove Last Series",
                       parent=self.window_id, callback=self.remove_last_series)

        # Save and Cancel Buttons
        with dpg.group(parent=self.window_id):
            dpg.add_button(label="Save", callback=self.save_data)

    def refresh_series_ui(self):

        dpg.delete_item('series_group', children_only=True)

        if not "series" in self.json_data:
            self.json_data["series"] = []
        for i, series in enumerate(self.json_data["series"]):
            with dpg.child_window(parent='series_group', height=225):
                print(i)
                dpg.add_input_text(
                    label=f"Series Label {i}", default_value=series["label"], tag=f"series_label_{i}")
                dpg.add_combo(label=f"Type {i}", items=[
                              "line", "bar", "pie", "scatter"], default_value=series["type"], tag=f"series_type_{i}")
                dpg.add_combo(
                    label=f"X Column {i}", items=list(self.pm.df.columns), default_value=series["xColumn"], tag=f"series_xColumn_{i}")
                dpg.add_combo(
                    label=f"Y Column {i}", items=list(self.pm.df.columns), default_value=series["yColumn"], tag=f"series_yColumn_{i}")
                try:
                    dpg.add_color_edit(label=f"Color {i}", default_value=to_rgb_tuple(
                        series["color"]), tag=f"series_color_{i}")
                except:
                    dpg.add_color_edit(
                        label=f"Color {i}", tag=f"series_color_{i}")
                try:
                    filters = ",".join(
                        series["filter"]) if series["filter"][0] is not None else ""
                except:
                    filters = ""
                dpg.add_input_text(
                    label=f"Filter {i}", default_value=filters, tag=f"series_filter_{i}")

    def add_series(self, sender, app_data, user_data):
        self.json_data["series"].append({
            "label": "New Series",
            "type": "line",
            "xColumn": list(self.pm.df.columns)[0],
            "yColumn": list(self.pm.df.columns)[1],
            "color": "#FFFFFF",
            "filter": [None]
        })
        self.refresh_series_ui()

    def remove_last_series(self, sender, app_data, user_data):
        if self.json_data["series"]:
            self.json_data["series"].pop()
            self.refresh_series_ui()

    def save_data(self, sender, app_data, user_data):
        self.serialize_ui_to_dict()
        print("Data saved:", self.json_data)
        self.pm.set_plot_json(self.json_data)
        self.pm.create_plot()

    def serialize_ui_to_dict(self):
        self.json_data["title"] = dpg.get_value("json_title")
        self.json_data.setdefault('xAxis', {})[
            "label"] = dpg.get_value("xAxis_label")
        self.json_data["xAxis"]["columns"] = []
        self.json_data.setdefault('yAxis', {})[
            "label"] = dpg.get_value("yAxis_label")
        self.json_data["yAxis"]["columns"] = []
        self.json_data.setdefault('options', {})["gridLines"] = dpg.get_value(
            "options_gridLines")
        legend = dpg.get_value("options_legend")
        if legend == "None":
            legend = None
        self.json_data.setdefault('legend', {})["position"] = legend
        for i, series in enumerate(self.json_data["series"]):
            series["label"] = dpg.get_value(f"series_label_{i}")
            series["type"] = dpg.get_value(f"series_type_{i}")
            series["xColumn"] = dpg.get_value(f"series_xColumn_{i}")
            self.json_data["xAxis"]["columns"].append(
                dpg.get_value(f"series_xColumn_{i}"))
            series["yColumn"] = dpg.get_value(f"series_yColumn_{i}")
            self.json_data["yAxis"]["columns"].append(
                dpg.get_value(f"series_yColumn_{i}"))
            color = dpg.get_value(f"series_color_{i}")
            print(color)
            series["color"] = f"rgb({int(color[0])}, {int(color[1])}, {int(color[2])})"
            filter_text = dpg.get_value(f"series_filter_{i}")
            series["filter"] = filter_text.split(
                ",") if filter_text else [None]
