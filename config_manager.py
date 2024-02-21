import json
import os

class ConfigManager:
    # デフォルト設定をクラス変数として定義
    default_settings = {
        'plot_csv': None,
    }

    def __init__(self, config_path):
        self.__dict__['config_path'] = config_path
        self.__dict__['settings'] = self.load_config()

    def load_config(self):
        """設定ファイルを読み込む。ファイルが存在しない場合はデフォルト設定を返す。"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                # ファイルから読み込んだ設定とデフォルト設定をマージする
                file_settings = json.load(f)
                return {**self.__class__.default_settings, **file_settings}
        else:
            return self.__class__.default_settings.copy()

    def save_config(self):
        """現在の設定を設定ファイルに保存する。"""
        with open(self.config_path, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def __getattr__(self, name):
        """未定義の属性へのアクセスを設定から取得するようにする。"""
        try:
            return self.settings[name]
        except KeyError:
            raise AttributeError(f"'ConfigManager' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        """属性の設定を設定辞書に保存する。"""
        if name in self.__dict__ or name in self.__class__.__dict__:
            # 通常の属性の場合は通常通り処理
            super().__setattr__(name, value)
        else:
            # 設定項目の場合は設定辞書に保存
            self.settings[name] = value
            self.save_config()