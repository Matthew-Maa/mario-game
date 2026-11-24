# -*- coding: utf-8 -*-
"""
asset_generator.py - 游戏资产生成器
====================================
使用pygame绘图和numpy音频合成，自动生成所有游戏所需的:
- 精灵图(玩家、敌人、道具、地图块)
- 背景图(各关主题)
- 音效(跳跃、攻击、受伤、拾取等)
- 背景音乐(各关主题旋律)

运行此脚本即可在assets/目录下生成全部资源。
"""

import os
import sys
import math
import struct
import wave
import random

# 确保使用项目目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
ASSET_DIR = os.path.join(BASE_DIR, "assets")
IMAGE_DIR = os.path.join(ASSET_DIR, "images")
SOUND_DIR = os.path.join(ASSET_DIR, "sounds")
MUSIC_DIR = os.path.join(ASSET_DIR, "music")

# 颜色常量(从constants导入或在此定义)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SCREEN_W = 1024
SCREEN_H = 576

# 创建目录
for d in [IMAGE_DIR, SOUND_DIR, MUSIC_DIR]:
    os.makedirs(d, exist_ok=True)

# ==================== 尝试导入pygame ====================
try:
    import pygame
    pygame.init()
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False
    print("[警告] 未安装pygame，跳过图片资源生成")

# ==================== 尝试导入numpy ====================
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("[警告] 未安装numpy，跳过音频资源生成")


# ====================================================================
#  图片资源生成
# ====================================================================

def create_surface(w, h, color=None, alpha=255):
    """创建一个透明Surface"""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    if color:
        surf.fill((*color, alpha))
    return surf


def draw_player():
    """绘制马里奥精灵(站立、行走2帧、跳跃、攻击)"""
    # 站立帧
    frames = {}
    size = (32, 44)
    for state in ["idle", "walk1", "walk2", "jump", "attack"]:
        surf = create_surface(*size)
        cx, cy = size[0] // 2, size[1]
        # 帽子(红色)
        pygame.draw.rect(surf, (220, 30, 30), (cx - 12, 2, 24, 8), border_radius=3)
        pygame.draw.rect(surf, (220, 30, 30), (cx - 14, 6, 28, 4), border_radius=2)
        # 脸(肤色)
        pygame.draw.rect(surf, (255, 200, 150), (cx - 10, 10, 20, 10), border_radius=3)
        # 眼睛
        pygame.draw.rect(surf, (0, 0, 0), (cx + 2, 13, 3, 4))
        # 胡子
        pygame.draw.rect(surf, (100, 50, 20), (cx - 8, 17, 16, 3))
        # 衣服(蓝色背带)
        pygame.draw.rect(surf, (50, 100, 220), (cx - 12, 20, 24, 16), border_radius=3)
        # 红色上衣
        pygame.draw.rect(surf, (220, 30, 30), (cx - 12, 20, 24, 4))
        # 背带
        pygame.draw.rect(surf, (50, 100, 220), (cx - 8, 20, 4, 16))
        pygame.draw.rect(surf, (50, 100, 220), (cx + 4, 20, 4, 16))

        if state == "jump":
            # 跳跃姿势：手臂上举
            pygame.draw.rect(surf, (255, 200, 150), (cx - 16, 22, 4, 8))
            pygame.draw.rect(surf, (255, 200, 150), (cx + 12, 22, 4, 8))
            # 腿弯曲
            pygame.draw.rect(surf, (100, 50, 20), (cx - 10, 36, 8, 8))
            pygame.draw.rect(surf, (100, 50, 20), (cx + 2, 36, 8, 8))
        elif state == "walk1":
            pygame.draw.rect(surf, (100, 50, 20), (cx - 10, 36, 8, 8))
            pygame.draw.rect(surf, (100, 50, 20), (cx + 4, 34, 8, 10))
        elif state == "walk2":
            pygame.draw.rect(surf, (100, 50, 20), (cx - 12, 34, 8, 10))
            pygame.draw.rect(surf, (100, 50, 20), (cx + 2, 36, 8, 8))
        elif state == "attack":
            # 攻击姿势：手臂前伸
            pygame.draw.rect(surf, (255, 200, 150), (cx + 10, 24, 12, 5))
            pygame.draw.rect(surf, (100, 50, 20), (cx - 10, 36, 8, 8))
            pygame.draw.rect(surf, (100, 50, 20), (cx + 2, 36, 8, 8))
        else:  # idle
            pygame.draw.rect(surf, (100, 50, 20), (cx - 10, 36, 8, 8))
            pygame.draw.rect(surf, (100, 50, 20), (cx + 2, 36, 8, 8))
        # 鞋子
        pygame.draw.rect(surf, (40, 40, 40), (cx - 12, 42, 10, 2))
        pygame.draw.rect(surf, (40, 40, 40), (cx + 2, 42, 10, 2))
        frames[state] = surf
    return frames


def draw_enemy(name, color, size):
    """根据敌人类型绘制精灵"""
    w, h = size
    surf = create_surface(w, h)

    if "goomba" in name:
        # 栗子仔：圆头，两只脚
        pygame.draw.ellipse(surf, color, (2, 4, w - 4, h - 16))
        pygame.draw.ellipse(surf, (darker(color)), (2, 4, w - 4, h - 16), 2)
        # 眼睛
        pygame.draw.ellipse(surf, WHITE, (8, 12, 6, 8))
        pygame.draw.ellipse(surf, WHITE, (w - 14, 12, 6, 8))
        pygame.draw.ellipse(surf, BLACK, (10, 14, 3, 4))
        pygame.draw.ellipse(surf, BLACK, (w - 12, 14, 3, 4))
        # 脚
        pygame.draw.ellipse(surf, (60, 40, 20), (2, h - 12, 12, 10))
        pygame.draw.ellipse(surf, (60, 40, 20), (w - 14, h - 12, 12, 10))
    elif "koopa" in name or "buzzy" in name or "hammer" in name or "fire_bro" in name or "magikoopa" in name:
        # 乌龟类：壳+头+脚
        # 头
        pygame.draw.ellipse(surf, lighter(color), (w // 2 - 6, 2, 12, 12))
        # 壳
        pygame.draw.ellipse(surf, color, (2, 12, w - 4, h - 20))
        pygame.draw.ellipse(surf, darker(color), (2, 12, w - 4, h - 20), 2)
        # 壳纹路
        pygame.draw.line(surf, darker(color), (4, h // 2), (w - 4, h // 2), 1)
        # 眼睛
        pygame.draw.ellipse(surf, WHITE, (w // 2 - 3, 6, 4, 4))
        pygame.draw.ellipse(surf, BLACK, (w // 2 - 2, 7, 2, 2))
        # 脚
        pygame.draw.ellipse(surf, lighter(color), (4, h - 10, 8, 8))
        pygame.draw.ellipse(surf, lighter(color), (w - 12, h - 10, 8, 8))
    elif "spiny" in name:
        # 刺球：圆形带刺
        cx, cy = w // 2, h // 2
        pygame.draw.circle(surf, color, (cx, cy), min(w, h) // 2 - 4)
        # 刺
        for ang in range(0, 360, 45):
            rad = math.radians(ang)
            x1 = cx + int(math.cos(rad) * (min(w, h) // 2 - 6))
            y1 = cy + int(math.sin(rad) * (min(w, h) // 2 - 6))
            x2 = cx + int(math.cos(rad) * (min(w, h) // 2 + 2))
            y2 = cy + int(math.sin(rad) * (min(w, h) // 2 + 2))
            pygame.draw.line(surf, darker(color), (x1, y1), (x2, y2), 2)
        pygame.draw.ellipse(surf, WHITE, (cx - 6, cy - 4, 5, 6))
        pygame.draw.ellipse(surf, BLACK, (cx - 5, cy - 3, 3, 3))
    elif "boo" in name or "ghost" in name:
        # 幽灵：半透明，底部波浪
        surf.fill((0, 0, 0, 0))
        for i in range(h - 8):
            alpha = 220
            pygame.draw.line(surf, (*color, alpha), (0, i), (w, i))
        # 底部波浪
        for i in range(0, w, 8):
            pygame.draw.ellipse(surf, (*color, 220), (i, h - 10, 8, 10))
        # 眼睛
        pygame.draw.ellipse(surf, BLACK, (w // 2 - 8, 8, 6, 8))
        pygame.draw.ellipse(surf, BLACK, (w // 2 + 2, 8, 6, 8))
        # 嘴
        pygame.draw.ellipse(surf, (0, 0, 0), (w // 2 - 4, 20, 8, 6))
    elif "dry_bones" in name:
        # 枯骨：白色骨架
        pygame.draw.ellipse(surf, color, (4, 2, w - 8, 14))  # 头
        pygame.draw.rect(surf, color, (w // 2 - 2, 14, 4, 12))  # 脊柱
        # 肋骨
        for i in range(3):
            pygame.draw.line(surf, color, (w // 2 - 8, 16 + i * 4), (w // 2 + 8, 16 + i * 4), 2)
        # 腿
        pygame.draw.rect(surf, color, (w // 2 - 6, 26, 4, 14))
        pygame.draw.rect(surf, color, (w // 2 + 2, 26, 4, 14))
        # 眼洞
        pygame.draw.ellipse(surf, BLACK, (w // 2 - 5, 6, 4, 4))
        pygame.draw.ellipse(surf, BLACK, (w // 2 + 1, 6, 4, 4))
    elif "bullet" in name:
        # 子弹：黑色椭圆+火焰尾
        pygame.draw.ellipse(surf, color, (2, 4, w - 4, h - 8))
        pygame.draw.ellipse(surf, (80, 80, 80), (2, 4, w - 4, h - 8), 2)
        # 眼睛
        pygame.draw.ellipse(surf, WHITE, (6, 10, 5, 5))
        pygame.draw.ellipse(surf, BLACK, (7, 11, 3, 3))
        # 火焰尾
        pygame.draw.polygon(surf, (255, 100, 0), [(w - 2, 6), (w + 8, h // 2), (w - 2, h - 6)])
    elif "lakitu" in name:
        # 云龟：云+龟壳
        # 云
        pygame.draw.ellipse(surf, (200, 200, 255), (0, 0, w, 16))
        # 龟
        pygame.draw.ellipse(surf, color, (4, 10, w - 8, h - 14))
        pygame.draw.ellipse(surf, darker(color), (4, 10, w - 8, h - 14), 2)
        # 眼镜
        pygame.draw.circle(surf, (255, 255, 0), (w // 2 - 4, 16), 5, 1)
        pygame.draw.circle(surf, (255, 255, 0), (w // 2 + 4, 16), 5, 1)
    elif "thwomp" in name:
        # 巨石怪：大方块+愤怒表情
        pygame.draw.rect(surf, color, (2, 2, w - 4, h - 4), border_radius=4)
        pygame.draw.rect(surf, darker(color), (2, 2, w - 4, h - 4), 3, border_radius=4)
        # 眉毛
        pygame.draw.line(surf, (255, 0, 0), (10, 16), (20, 20), 3)
        pygame.draw.line(surf, (255, 0, 0), (w - 20, 20), (w - 10, 16), 3)
        # 眼睛
        pygame.draw.ellipse(surf, (255, 0, 0), (12, 22, 8, 8))
        pygame.draw.ellipse(surf, (255, 0, 0), (w - 20, 22, 8, 8))
        # 嘴
        pygame.draw.rect(surf, (0, 0, 0), (w // 2 - 8, 38, 16, 6))
    elif "fire_piranha" in name:
        # 火焰花：管子+花头
        pygame.draw.rect(surf, (80, 180, 80), (w // 2 - 6, 16, 12, h - 16))  # 茎
        pygame.draw.ellipse(surf, color, (2, 0, w - 4, 20))  # 花头
        pygame.draw.ellipse(surf, (255, 255, 255), (6, 4, 6, 6))  # 牙齿
        pygame.draw.ellipse(surf, (255, 255, 255), (w - 12, 4, 6, 6))
        pygame.draw.ellipse(surf, BLACK, (8, 6, 3, 3))
        pygame.draw.ellipse(surf, BLACK, (w - 10, 6, 3, 3))
    elif "bowser" in name or name == "bowser":
        # Bowser大boss
        # 身体(绿色)
        pygame.draw.ellipse(surf, color, (4, 20, w - 8, h - 24))
        # 头
        pygame.draw.ellipse(surf, lighter(color), (w // 2 - 16, 2, 32, 24))
        # 角
        pygame.draw.polygon(surf, (220, 220, 220), [(w // 2 - 14, 2), (w // 2 - 18, -4), (w // 2 - 10, 0)])
        pygame.draw.polygon(surf, (220, 220, 220), [(w // 2 + 14, 2), (w // 2 + 18, -4), (w // 2 + 10, 0)])
        # 眼睛(红色)
        pygame.draw.ellipse(surf, (255, 50, 50), (w // 2 - 10, 10, 8, 6))
        pygame.draw.ellipse(surf, (255, 50, 50), (w // 2 + 2, 10, 8, 6))
        # 嘴+牙
        pygame.draw.rect(surf, (40, 20, 20), (w // 2 - 14, 22, 28, 8))
        pygame.draw.rect(surf, WHITE, (w // 2 - 12, 22, 4, 6))
        pygame.draw.rect(surf, WHITE, (w // 2 - 4, 22, 4, 6))
        pygame.draw.rect(surf, WHITE, (w // 2 + 4, 22, 4, 6))
        pygame.draw.rect(surf, WHITE, (w // 2 + 8, 22, 4, 6))
        # 壳(带刺)
        pygame.draw.ellipse(surf, darker(color), (8, 30, w - 16, h - 34), 3)
    else:
        # 默认：简单方块
        pygame.draw.rect(surf, color, (2, 2, w - 4, h - 4))
        pygame.draw.rect(surf, WHITE, (2, 2, w - 4, h - 4), 2)
        pygame.draw.ellipse(surf, WHITE, (6, 6, 6, 6))
        pygame.draw.ellipse(surf, BLACK, (8, 8, 3, 3))
        pygame.draw.ellipse(surf, WHITE, (w - 12, 6, 6, 6))
        pygame.draw.ellipse(surf, BLACK, (w - 10, 8, 3, 3))

    return surf


def darker(color, factor=0.6):
    """使颜色变暗"""
    return tuple(max(0, int(c * factor)) for c in color[:3])


def lighter(color, factor=1.3):
    """使颜色变亮"""
    return tuple(min(255, int(c * factor)) for c in color[:3])


def draw_projectile(proj_type="fireball"):
    """绘制投射物"""
    if proj_type == "fireball":
        surf = create_surface(16, 16)
        pygame.draw.circle(surf, (255, 100, 0), (8, 8), 7)
        pygame.draw.circle(surf, (255, 200, 0), (8, 8), 4)
        pygame.draw.circle(surf, (255, 255, 200), (8, 8), 2)
    elif proj_type == "hammer":
        surf = create_surface(20, 20)
        pygame.draw.rect(surf, (120, 80, 40), (4, 4, 12, 12))
        pygame.draw.rect(surf, (80, 50, 20), (2, 8, 16, 4))
    elif proj_type == "magic":
        surf = create_surface(20, 20)
        pygame.draw.circle(surf, (180, 0, 200), (10, 10), 8)
        pygame.draw.circle(surf, (255, 100, 255), (10, 10), 5)
        pygame.draw.circle(surf, (255, 200, 255), (10, 10), 2)
    else:
        surf = create_surface(12, 12)
        pygame.draw.circle(surf, (200, 200, 200), (6, 6), 5)
    return surf


def draw_tile(name, size=32):
    """绘制地图块"""
    surf = create_surface(size, size)
    if name == "ground":
        pygame.draw.rect(surf, (120, 80, 40), (0, 0, size, size))
        pygame.draw.rect(surf, (90, 60, 30), (0, 0, size, 4))
        pygame.draw.rect(surf, (100, 70, 35), (0, size - 4, size, 4))
        # 草地顶部
        pygame.draw.rect(surf, (80, 160, 60), (0, 0, size, 6))
    elif name == "brick":
        pygame.draw.rect(surf, (180, 100, 50), (0, 0, size, size))
        pygame.draw.rect(surf, (120, 70, 30), (0, 0, size, 2))
        pygame.draw.line(surf, (120, 70, 30), (0, size // 2), (size, size // 2), 1)
        pygame.draw.line(surf, (120, 70, 30), (size // 2, 0), (size // 2, size // 2), 1)
        pygame.draw.line(surf, (120, 70, 30), (size // 4, size // 2), (size // 4, size), 1)
        pygame.draw.line(surf, (120, 70, 30), (size * 3 // 4, size // 2), (size * 3 // 4, size), 1)
    elif name == "pipe":
        pygame.draw.rect(surf, (50, 180, 50), (0, 0, size, size))
        pygame.draw.rect(surf, (30, 120, 30), (0, 0, size, 4))
        pygame.draw.rect(surf, (70, 200, 70), (4, 4, 6, size - 4))
    elif name == "platform":
        pygame.draw.rect(surf, (200, 150, 100), (0, 0, size, size))
        pygame.draw.rect(surf, (160, 110, 70), (0, 0, size, 3))
    elif name == "save_point":
        # 存档点：旗杆+旗帜
        pygame.draw.rect(surf, (180, 180, 180), (size // 2 - 2, 0, 4, size))
        pygame.draw.polygon(surf, (255, 200, 50), [(size // 2 + 2, 2), (size - 2, 8), (size // 2 + 2, 14)])
    elif name == "end_gate":
        # 终点门
        pygame.draw.rect(surf, (100, 60, 30), (2, 0, size - 4, size))
        pygame.draw.rect(surf, (200, 200, 50), (6, 6, size - 12, 6))
    else:
        surf.fill((255, 0, 255))
    return surf


def draw_background(theme, w=1024, h=576):
    """绘制背景"""
    surf = create_surface(w, h)
    if theme == "grassland":
        surf.fill((135, 206, 235))
        # 云
        for i in range(5):
            cx = (i * 250 + 100) % w
            cy = 60 + (i % 3) * 40
            for j in range(3):
                pygame.draw.ellipse(surf, (255, 255, 255), (cx + j * 20, cy, 30, 25))
        # 远山
        pygame.draw.polygon(surf, (100, 150, 100), [(0, h), (200, h - 150), (400, h)])
        pygame.draw.polygon(surf, (80, 130, 80), [(300, h), (500, h - 200), (700, h)])
    elif theme == "underground":
        surf.fill((30, 30, 50))
        # 钟乳石
        for i in range(8):
            x = i * 130 + 50
            pygame.draw.polygon(surf, (60, 60, 80), [(x, 0), (x + 20, 40), (x + 40, 0)])
    elif theme == "ghost":
        surf.fill((40, 40, 60))
        # 月亮
        pygame.draw.circle(surf, (200, 200, 150), (w - 150, 80), 40)
        # 飘动的幽灵轮廓
        for i in range(6):
            cx = (i * 200 + 50) % w
            pygame.draw.ellipse(surf, (60, 60, 80), (cx, 100 + (i % 2) * 50, 40, 30))
    elif theme == "lava":
        surf.fill((60, 20, 10))
        # 火焰
        for i in range(8):
            x = i * 140 + 30
            pygame.draw.polygon(surf, (255, 100, 0), [(x, h), (x + 10, h - 60), (x + 20, h)])
            pygame.draw.polygon(surf, (255, 200, 0), [(x + 5, h), (x + 10, h - 40), (x + 15, h)])
    elif theme == "castle":
        surf.fill((30, 20, 20))
        # 城堡轮廓
        for i in range(4):
            x = i * 280 + 100
            pygame.draw.rect(surf, (60, 40, 40), (x, h - 200, 80, 200))
            pygame.draw.polygon(surf, (60, 40, 40), [(x, h - 200), (x + 40, h - 240), (x + 80, h - 200)])
    return surf


def draw_item(name, size=24):
    """绘制道具/增益图标"""
    surf = create_surface(size, size)
    if "heart" in name or "hp" in name:
        pygame.draw.ellipse(surf, (220, 50, 50), (4, 4, 8, 8))
        pygame.draw.ellipse(surf, (220, 50, 50), (size - 12, 4, 8, 8))
        pygame.draw.polygon(surf, (220, 50, 50), [(4, 10), (size - 4, 10), (size // 2, size - 4)])
    elif "sword" in name or "atk" in name:
        pygame.draw.polygon(surf, (200, 200, 220), [(size // 2, 2), (size // 2 - 4, size - 6), (size // 2 + 4, size - 6)])
        pygame.draw.rect(surf, (120, 80, 40), (size // 2 - 4, size - 6, 8, 4))
    elif "star" in name or "ult" in name:
        points = []
        cx, cy = size // 2, size // 2
        for i in range(10):
            ang = math.radians(i * 36 - 90)
            r = size // 2 - 2 if i % 2 == 0 else size // 4
            points.append((cx + int(math.cos(ang) * r), cy + int(math.sin(ang) * r)))
        pygame.draw.polygon(surf, (255, 200, 0), points)
    elif "boot" in name or "cd" in name:
        pygame.draw.rect(surf, (100, 50, 200), (4, 4, size - 12, size - 8))
        pygame.draw.rect(surf, (80, 30, 160), (size - 8, size - 8, 8, 4))
    elif "lightning" in name or "charge" in name:
        pygame.draw.polygon(surf, (255, 220, 0), [(size // 2, 2), (size // 2 - 6, size // 2), (size // 2, size // 2), (size // 2 - 3, size - 2), (size // 2 + 6, size // 2 - 2), (size // 2, size // 2 - 2)])
    elif "arrow" in name or "range" in name:
        pygame.draw.line(surf, (100, 200, 100), (4, size // 2), (size - 4, size // 2), 3)
        pygame.draw.polygon(surf, (100, 200, 100), [(size - 8, size // 2 - 4), (size - 2, size // 2), (size - 8, size // 2 + 4)])
    elif "wing" in name:
        pygame.draw.ellipse(surf, (200, 200, 255), (2, size // 2 - 6, size - 4, 12))
        pygame.draw.ellipse(surf, (150, 150, 255), (2, size // 2 - 6, size - 4, 12), 2)
    elif "shield" in name:
        pygame.draw.polygon(surf, (100, 150, 220), [(size // 2, 2), (size - 2, 8), (size // 2 + 2, size - 2), (size // 2 - 2, size - 2), (2, 8)])
    elif "crown" in name:
        pygame.draw.polygon(surf, (255, 200, 0), [(2, size - 4), (2, 8), (size // 2, 2), (size - 2, 8), (size - 2, size - 4)])
    elif "potion" in name:
        pygame.draw.rect(surf, (200, 50, 50), (size // 2 - 4, 8, 8, size - 12))
        pygame.draw.rect(surf, (100, 100, 100), (size // 2 - 3, 4, 6, 4))
    elif "dash" in name:
        pygame.draw.polygon(surf, (100, 200, 100), [(2, size // 2), (size - 4, 2), (size - 4, size - 2)])
    elif "vampire" in name:
        pygame.draw.polygon(surf, (180, 0, 0), [(size // 2 - 4, 2), (size // 2, size - 2), (size // 2 + 4, 2)])
    elif "crit" in name:
        pygame.draw.ellipse(surf, (255, 50, 50), (4, 4, size - 8, size - 8))
        pygame.draw.line(surf, (255, 255, 255), (8, 8), (size - 8, size - 8), 2)
        pygame.draw.line(surf, (255, 255, 255), (size - 8, 8), (8, size - 8), 2)
    else:
        pygame.draw.rect(surf, (200, 200, 100), (4, 4, size - 8, size - 8))
    return surf


def generate_all_images():
    """生成所有图片资源"""
    if not HAS_PYGAME:
        return
    print("正在生成图片资源...")

    # 玩家精灵
    player_frames = draw_player()
    for name, surf in player_frames.items():
        path = os.path.join(IMAGE_DIR, f"player_{name}.png")
        pygame.image.save(surf, path)
    print("  - 玩家精灵")

    # 敌人精灵
    from constants import ENEMY_DATA
    for name, data in ENEMY_DATA.items():
        surf = draw_enemy(name, data["color"], data["size"])
        path = os.path.join(IMAGE_DIR, f"enemy_{name}.png")
        pygame.image.save(surf, path)
    print("  - 敌人精灵")

    # 投射物
    for pt in ["fireball", "hammer", "magic"]:
        surf = draw_projectile(pt)
        path = os.path.join(IMAGE_DIR, f"proj_{pt}.png")
        pygame.image.save(surf, path)
    print("  - 投射物")

    # 地图块
    for tile in ["ground", "brick", "pipe", "platform", "save_point", "end_gate"]:
        surf = draw_tile(tile)
        path = os.path.join(IMAGE_DIR, f"tile_{tile}.png")
        pygame.image.save(surf, path)
    print("  - 地图块")

    # 背景
    from constants import LEVELS
    for level in LEVELS:
        surf = draw_background(level["theme"])
        path = os.path.join(IMAGE_DIR, f"bg_{level['theme']}.png")
        pygame.image.save(surf, path)
    print("  - 背景")

    # 道具图标
    from constants import SMALL_BUFFS, BIG_BUFFS
    for buff in SMALL_BUFFS + BIG_BUFFS:
        surf = draw_item(buff["icon"])
        path = os.path.join(IMAGE_DIR, f"item_{buff['icon']}.png")
        pygame.image.save(surf, path)
    print("  - 道具图标")

    # UI图标
    for icon in ["heart", "sword", "star", "shield", "clock", "trophy", "flag", "bag", "think", "peace"]:
        surf = draw_item(icon)
        path = os.path.join(IMAGE_DIR, f"icon_{icon}.png")
        pygame.image.save(surf, path)
    print("  - UI图标")

    # 标题画面背景
    surf = create_surface(SCREEN_W, SCREEN_H)
    surf.fill((30, 100, 200))
    # 简单装饰
    for i in range(20):
        x = (i * 80) % SCREEN_W
        y = 50 + (i % 4) * 60
        for j in range(3):
            pygame.draw.ellipse(surf, (255, 255, 255), (x + j * 20, y, 30, 25))
    # 地面
    pygame.draw.rect(surf, (80, 160, 60), (0, SCREEN_H - 60, SCREEN_W, 60))
    pygame.draw.rect(surf, (120, 80, 40), (0, SCREEN_H - 50, SCREEN_W, 50))
    path = os.path.join(IMAGE_DIR, "title_bg.png")
    pygame.image.save(surf, path)
    print("  - 标题画面")

    print("图片资源生成完成!")


# ====================================================================
#  音频资源生成
# ====================================================================

SAMPLE_RATE = 44100


def generate_tone(freq, duration, volume=0.5, wave_type="sine"):
    """生成一个简单的音调"""
    if not HAS_NUMPY:
        return None
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    if wave_type == "sine":
        wave = np.sin(2 * np.pi * freq * t)
    elif wave_type == "square":
        wave = np.sign(np.sin(2 * np.pi * freq * t))
    elif wave_type == "sawtooth":
        wave = 2 * (t * freq - np.floor(t * freq + 0.5))
    elif wave_type == "noise":
        wave = np.random.uniform(-1, 1, len(t))
    else:
        wave = np.sin(2 * np.pi * freq * t)
    # 淡入淡出
    fade = int(SAMPLE_RATE * 0.01)
    if len(wave) > 2 * fade:
        wave[:fade] *= np.linspace(0, 1, fade)
        wave[-fade:] *= np.linspace(1, 0, fade)
    return wave * volume


def save_wav(filename, wave_data, volume=0.7):
    """保存为WAV文件"""
    if not HAS_NUMPY or wave_data is None:
        return
    wave_data = wave_data * volume
    # 转为16位PCM
    audio = np.int16(wave_data * 32767)
    path = os.path.join(SOUND_DIR, filename)
    with wave.open(path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(audio.tobytes())


def generate_sfx():
    """生成所有音效"""
    if not HAS_NUMPY:
        return
    print("正在生成音效资源...")

    # 跳跃音效(频率上滑)
    t = np.linspace(0, 0.2, int(SAMPLE_RATE * 0.2), False)
    freq = 300 + 600 * t / 0.2
    wave = np.sin(2 * np.pi * freq * t) * 0.4
    fade = int(SAMPLE_RATE * 0.02)
    wave[:fade] *= np.linspace(0, 1, fade)
    wave[-fade:] *= np.linspace(1, 0, fade)
    save_wav("sfx_jump.wav", wave, 0.6)

    # 近战攻击音效(短促噪音)
    t = np.linspace(0, 0.1, int(SAMPLE_RATE * 0.1), False)
    wave = (np.random.uniform(-1, 1, len(t)) * np.exp(-t * 30)) * 0.5
    save_wav("sfx_melee.wav", wave, 0.7)

    # 受伤音效(频率下滑)
    t = np.linspace(0, 0.3, int(SAMPLE_RATE * 0.3), False)
    freq = 400 - 200 * t / 0.3
    wave = np.sin(2 * np.pi * freq * t) * 0.4
    wave[:fade] *= np.linspace(0, 1, fade)
    wave[-fade:] *= np.linspace(1, 0, fade)
    save_wav("sfx_hurt.wav", wave, 0.7)

    # 大招音效(强烈的低频+高频)
    t = np.linspace(0, 0.5, int(SAMPLE_RATE * 0.5), False)
    wave = (np.sin(2 * np.pi * 80 * t) + np.sin(2 * np.pi * 800 * t)) * 0.3
    wave[:fade] *= np.linspace(0, 1, fade)
    wave[-fade:] *= np.linspace(1, 0, fade)
    save_wav("sfx_ultimate.wav", wave, 0.8)

    # 敌人死亡音效
    t = np.linspace(0, 0.3, int(SAMPLE_RATE * 0.3), False)
    freq = 500 * np.exp(-t * 3)
    wave = np.sin(2 * np.pi * freq * t) * 0.4
    wave[:fade] *= np.linspace(0, 1, fade)
    wave[-fade:] *= np.linspace(1, 0, fade)
    save_wav("sfx_enemy_die.wav", wave, 0.7)

    # 拾取/增益音效(上升音阶)
    t = np.linspace(0, 0.4, int(SAMPLE_RATE * 0.4), False)
    freq = 400 + 600 * t / 0.4
    wave = np.sin(2 * np.pi * freq * t) * 0.3
    wave[:fade] *= np.linspace(0, 1, fade)
    wave[-fade:] *= np.linspace(1, 0, fade)
    save_wav("sfx_pickup.wav", wave, 0.6)

    # 存档点音效(和弦)
    t = np.linspace(0, 0.6, int(SAMPLE_RATE * 0.6), False)
    wave = (np.sin(2 * np.pi * 523 * t) + np.sin(2 * np.pi * 659 * t) + np.sin(2 * np.pi * 784 * t)) * 0.15
    wave[:fade] *= np.linspace(0, 1, fade)
    wave[-fade:] *= np.linspace(1, 0, fade)
    save_wav("sfx_savepoint.wav", wave, 0.6)

    # 通关音效
    t = np.linspace(0, 1.0, int(SAMPLE_RATE * 1.0), False)
    notes = [523, 659, 784, 1047]
    wave = np.zeros_like(t)
    for i, note in enumerate(notes):
        start = int(i * len(t) / 4)
        end = int((i + 1) * len(t) / 4)
        wave[start:end] = np.sin(2 * np.pi * note * t[start:end]) * 0.3
    wave[:fade] *= np.linspace(0, 1, fade)
    wave[-fade:] *= np.linspace(1, 0, fade)
    save_wav("sfx_level_clear.wav", wave, 0.7)

    # 按钮点击音效
    t = np.linspace(0, 0.05, int(SAMPLE_RATE * 0.05), False)
    wave = np.sin(2 * np.pi * 800 * t) * 0.3
    save_wav("sfx_button.wav", wave, 0.5)

    # 成就解锁音效
    t = np.linspace(0, 0.8, int(SAMPLE_RATE * 0.8), False)
    freq = 600 + 400 * np.sin(2 * np.pi * 5 * t)
    wave = np.sin(2 * np.pi * freq * t) * 0.3
    wave[:fade] *= np.linspace(0, 1, fade)
    wave[-fade:] *= np.linspace(1, 0, fade)
    save_wav("sfx_achievement.wav", wave, 0.6)

    print("  音效生成完成!")


def generate_music():
    """生成背景音乐(简单的循环旋律)"""
    if not HAS_NUMPY:
        return
    print("正在生成背景音乐...")

    # 简单的旋律生成器
    def make_melody(notes, tempo=0.3, total_dur=30):
        """根据音符列表生成旋律"""
        duration = total_dur
        total_samples = int(SAMPLE_RATE * duration)
        wave = np.zeros(total_samples)
        note_dur = tempo
        samples_per_note = int(SAMPLE_RATE * note_dur)
        idx = 0
        while idx < total_samples:
            for note in notes:
                if idx >= total_samples:
                    break
                end = min(idx + samples_per_note, total_samples)
                n = end - idx
                t = np.linspace(0, n / SAMPLE_RATE, n, False)
                w = np.sin(2 * np.pi * note * t) * 0.15
                # 加入低音
                w += np.sin(2 * np.pi * (note / 2) * t) * 0.08
                wave[idx:end] = w
                idx = end
        return wave

    # 音符频率
    C4, D4, E4, F4, G4, A4, B4 = 262, 294, 330, 349, 392, 440, 494
    B3 = 247  # B3低于C4
    C5, D5, E5, F5, G5, A5, B5 = 523, 587, 659, 698, 784, 880, 988

    # 标题画面音乐(欢快)
    melody = make_melody([C4, E4, G4, C5, G4, E4, C4, E4, F4, A4, C5, A4, F4, A4,
                          G4, B4, D5, G5, D5, B4, G4, B4], tempo=0.25, total_dur=40)
    fade = int(SAMPLE_RATE * 0.5)
    if len(melody) > 2 * fade:
        melody[:fade] *= np.linspace(0, 1, fade)
        melody[-fade:] *= np.linspace(1, 0, fade)
    path = os.path.join(MUSIC_DIR, "music_title.wav")
    audio = np.int16(melody * 32767 * 0.5)
    with wave.open(path, "w") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SAMPLE_RATE)
        f.writeframes(audio.tobytes())

    # 第1关：草原(轻快)
    melody = make_melody([E4, G4, C5, G4, E4, G4, A4, G4, F4, A4, C5, A4, F4, A4,
                          G4, B4, D5, B4, G4, B4, C5, G4, E4, C4], tempo=0.22, total_dur=60)
    melody[:fade] *= np.linspace(0, 1, fade)
    melody[-fade:] *= np.linspace(1, 0, fade)
    path = os.path.join(MUSIC_DIR, "music_level1.wav")
    audio = np.int16(melody * 32767 * 0.4)
    with wave.open(path, "w") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SAMPLE_RATE)
        f.writeframes(audio.tobytes())

    # 第2关：地下(神秘)
    melody = make_melody([C4, C4, E4, G4, F4, E4, D4, C4, B3, C4, D4, E4, F4, G4,
                          A4, G4, F4, E4, D4, C4], tempo=0.28, total_dur=60)
    melody[:fade] *= np.linspace(0, 1, fade)
    melody[-fade:] *= np.linspace(1, 0, fade)
    path = os.path.join(MUSIC_DIR, "music_level2.wav")
    audio = np.int16(melody * 32767 * 0.35)
    with wave.open(path, "w") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SAMPLE_RATE)
        f.writeframes(audio.tobytes())

    # 第3关：幽灵(诡异)
    melody = make_melody([A4, A4, C5, E5, D5, C5, B4, A4, G4, A4, B4, C5, B4, A4,
                          G4, F4, E4, D4, E4, A4], tempo=0.30, total_dur=60)
    melody[:fade] *= np.linspace(0, 1, fade)
    melody[-fade:] *= np.linspace(1, 0, fade)
    path = os.path.join(MUSIC_DIR, "music_level3.wav")
    audio = np.int16(melody * 32767 * 0.3)
    with wave.open(path, "w") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SAMPLE_RATE)
        f.writeframes(audio.tobytes())

    # 第4关：熔岩(紧张)
    melody = make_melody([D4, D4, F4, A4, G4, F4, E4, D4, C4, D4, E4, F4, G4, A4,
                          B4, A4, G4, F4, E4, D4, C4, D4], tempo=0.20, total_dur=60)
    melody[:fade] *= np.linspace(0, 1, fade)
    melody[-fade:] *= np.linspace(1, 0, fade)
    path = os.path.join(MUSIC_DIR, "music_level4.wav")
    audio = np.int16(melody * 32767 * 0.4)
    with wave.open(path, "w") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SAMPLE_RATE)
        f.writeframes(audio.tobytes())

    # 第5关：Boss城堡(史诗)
    melody = make_melody([C4, C4, G4, G4, A4, A4, G4, F4, F4, E4, E4, D4, D4, C4,
                          G4, F4, E4, D4, C4, G4, F4, E4, D4, C4], tempo=0.18, total_dur=70)
    melody[:fade] *= np.linspace(0, 1, fade)
    melody[-fade:] *= np.linspace(1, 0, fade)
    path = os.path.join(MUSIC_DIR, "music_level5.wav")
    audio = np.int16(melody * 32767 * 0.45)
    with wave.open(path, "w") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SAMPLE_RATE)
        f.writeframes(audio.tobytes())

    # 胜利音乐
    melody = make_melody([C4, E4, G4, C5, E5, G5, E5, C5, G4, C5, E5, G5, E5, C5,
                          G4, E4, C4], tempo=0.25, total_dur=20)
    melody[:fade] *= np.linspace(0, 1, fade)
    melody[-fade:] *= np.linspace(1, 0, fade)
    path = os.path.join(MUSIC_DIR, "music_victory.wav")
    audio = np.int16(melody * 32767 * 0.5)
    with wave.open(path, "w") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SAMPLE_RATE)
        f.writeframes(audio.tobytes())

    print("  背景音乐生成完成!")


if __name__ == "__main__":
    print("=" * 50)
    print("  马里奥游戏 - 资源生成器")
    print("=" * 50)
    generate_all_images()
    generate_sfx()
    generate_music()
    print("\n所有资源生成完毕！")
    print(f"图片目录: {IMAGE_DIR}")
    print(f"音效目录: {SOUND_DIR}")
    print(f"音乐目录: {MUSIC_DIR}")
