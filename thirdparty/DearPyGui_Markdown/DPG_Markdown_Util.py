
import dearpygui.dearpygui as dpg
try:
    import DearPyGui_Markdown as dpg_markdown
except ModuleNotFoundError or ImportError:
    import os
    import sys
    # import from parent folder
    current = os.path.dirname(os.path.realpath(__file__))
    sys.path.append(os.path.dirname(current))
    import DearPyGui_Markdown as dpg_markdown


def setup_dpg_markdown(font_size=25) -> None:
    default_font_path = './thirdparty/PlemolJP/PlemolJP-Medium.ttf'
    bold_font_path = './thirdparty/PlemolJP/PlemolJP-Bold.ttf'
    italic_font_path = './thirdparty/PlemolJP/PlemolJP-Italic.ttf'
    italic_bold_font_path = './thirdparty/PlemolJP/PlemolJP-BoldItalic.ttf'

    dpg_markdown.set_font_registry(dpg.add_font_registry())

    dpg_font = dpg_markdown.set_font(
        font_size=font_size,
        default=default_font_path,
        bold=bold_font_path,
        italic=italic_font_path,
        italic_bold=italic_bold_font_path
    )

    # Apply the created DPG font
    dpg.bind_font(dpg_font)

class dpg_static_image:
    def __init__(self):
        tag_list = []
        
    def add_image(self, tag, texture_data, **kwargs):
        with dpg.texture_registry(show=True):
            dpg.add_static_texture(width=100, height=100, default_value=texture_data, tag=tag)
        dpg.add_image(tag=tag, **kwargs)

    def delete_item(self, tag, children_only=False):
        dpg.delete_item(tag, children_only)

    def delete_item_all(self, children_only=False):
        while len(self.tag_list) > 0:
            dpg.delete_item(self.tag_list[0], children_only)
            self.tag_list.pop(0)
