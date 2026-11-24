# -*- coding: utf-8 -*-
"""
main.py - 游戏入口
====================================
启动超级马里奥冒险游戏。
初始化pygame、创建窗口、加载设置和存档、运行游戏。
"""

import pygame
import os
import sys

# 确保能导入同目录下的模块
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from constants import TITLE, DEFAULT_SETTINGS
from settings_manager import SettingsManager
from save_manager import SaveManager
from achievement_manager import AchievementManager
from game import Game


def main():
    """主函数 - 游戏入口"""
    # 初始化pygame
    pygame.init()

    # 加载设置
    settings_mgr = SettingsManager()

    # 获取屏幕尺寸
    screen_w, screen_h = settings_mgr.get_screen_size()

    # 创建窗口
    flags = pygame.SCALED | pygame.RESIZABLE
    if settings_mgr.get_fullscreen():
        flags |= pygame.FULLSCREEN
    screen = pygame.display.set_mode((screen_w, screen_h), flags)

    # 初始化混音器
    try:
        pygame.mixer.init()
    except Exception:
        print("[警告] 音频初始化失败，游戏将以静音模式运行")

    # 加载存档和成就
    save_mgr = SaveManager()
    ach_mgr = AchievementManager()

    # 创建游戏
    game = Game(screen, settings_mgr, save_mgr, ach_mgr)

    # 运行游戏
    game.run()

    # 清理退出
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
