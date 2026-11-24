# -*- coding: utf-8 -*-
"""
settings_manager.py - 设置管理
====================================
管理游戏设置：按键、音量、屏幕大小。
设置保存在 saves/settings.json 中。
"""

import json
import os
from constants import DEFAULT_SETTINGS, DEFAULT_CONTROLS, SAVE_DIR


class SettingsManager:
    """设置管理器"""

    def __init__(self):
        self.settings = dict(DEFAULT_SETTINGS)
        self.filepath = os.path.join(SAVE_DIR, "settings.json")
        self.load()

    def load(self):
        """从文件加载设置"""
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 合并默认值(防止新字段缺失)
            for key in DEFAULT_SETTINGS:
                if key in data:
                    self.settings[key] = data[key]
        except (FileNotFoundError, json.JSONDecodeError):
            self.settings = dict(DEFAULT_SETTINGS)
            self.save()

    def save(self):
        """保存设置到文件"""
        os.makedirs(SAVE_DIR, exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)

    def get_controls(self):
        """获取按键设置"""
        return self.settings.get("controls", dict(DEFAULT_CONTROLS))

    def set_control(self, action, key):
        """设置某个动作的按键"""
        if "controls" not in self.settings:
            self.settings["controls"] = dict(DEFAULT_CONTROLS)
        self.settings["controls"][action] = key
        self.save()

    def get_music_volume(self):
        """获取音乐音量(0-100)"""
        return self.settings.get("music_volume", 50)

    def set_music_volume(self, vol):
        """设置音乐音量"""
        self.settings["music_volume"] = max(0, min(100, int(vol)))
        self.save()

    def get_sfx_volume(self):
        """获取音效音量(0-100)"""
        return self.settings.get("sfx_volume", 70)

    def set_sfx_volume(self, vol):
        """设置音效音量"""
        self.settings["sfx_volume"] = max(0, min(100, int(vol)))
        self.save()

    def get_screen_size(self):
        """获取屏幕尺寸"""
        return (
            self.settings.get("screen_width", 1024),
            self.settings.get("screen_height", 576)
        )

    def set_screen_size(self, w, h):
        """设置屏幕尺寸(重启后生效)"""
        self.settings["screen_width"] = int(w)
        self.settings["screen_height"] = int(h)
        self.save()

    def get_fullscreen(self):
        """是否全屏"""
        return self.settings.get("fullscreen", False)

    def set_fullscreen(self, value):
        """设置全屏"""
        self.settings["fullscreen"] = bool(value)
        self.save()

    def reset_to_default(self):
        """恢复默认设置"""
        self.settings = dict(DEFAULT_SETTINGS)
        self.settings["controls"] = dict(DEFAULT_CONTROLS)
        self.save()
