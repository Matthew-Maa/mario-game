# -*- coding: utf-8 -*-
"""
constants.py - 游戏常量与平衡数据
====================================
所有游戏数值、难度设定、敌人属性、关卡数据均在此文件中定义。
修改此文件可调整游戏平衡性。
"""

import os

# ==================== 路径常量 ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(BASE_DIR, "assets")
IMAGE_DIR = os.path.join(ASSET_DIR, "images")
SOUND_DIR = os.path.join(ASSET_DIR, "sounds")
MUSIC_DIR = os.path.join(ASSET_DIR, "music")
SAVE_DIR = os.path.join(BASE_DIR, "saves")
SPRITE_DIR = os.path.join(ASSET_DIR, "sprites")

# ==================== 屏幕常量 ====================
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 576  # 16:9 比例
FPS = 60
TITLE = "超级马里奥冒险"

# ==================== 颜色常量 ====================
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 50, 50)
GREEN = (50, 200, 50)
BLUE = (50, 100, 220)
YELLOW = (255, 215, 0)
ORANGE = (255, 165, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)
BROWN = (139, 90, 43)
SKY_BLUE = (135, 206, 235)
DARK_GREEN = (34, 120, 34)
PURPLE = (128, 0, 128)
GOLD = (255, 180, 0)

# ==================== 物理常量 ====================
GRAVITY = 0.8
JUMP_POWER = 16
MOVE_SPEED = 5
MAX_FALL_SPEED = 20

# ==================== 难度设定 ====================
# 每个难度的玩家与敌人修正倍率
DIFFICULTY = {
    "easy": {
        "name": "简单",
        "player_hp": 150,
        "player_atk": 20,
        "melee_cd": 0.8,        # 近战冷却(秒)
        "enemy_hp_mul": 0.7,    # 敌人血量倍率
        "enemy_atk_mul": 0.7,   # 敌人攻击倍率
        "desc": "适合新手，敌人较弱，主角更强",
    },
    "normal": {
        "name": "普通",
        "player_hp": 100,
        "player_atk": 15,
        "melee_cd": 1.0,
        "enemy_hp_mul": 1.0,
        "enemy_atk_mul": 1.0,
        "desc": "标准体验，平衡的挑战",
    },
    "hard": {
        "name": "困难",
        "player_hp": 70,
        "player_atk": 12,
        "melee_cd": 1.2,
        "enemy_hp_mul": 1.3,
        "enemy_atk_mul": 1.3,
        "desc": "硬核挑战，敌人强大，主角脆弱",
    },
}

# ==================== 玩家基础属性 ====================
PLAYER_BASE = {
    "hp": 100,
    "atk": 15,
    "melee_cd": 1.0,       # 近战冷却(秒)
    "melee_range": 65,     # 近战范围(像素)
    "melee_damage": 15,   # 近战伤害(=atk)
    "ultimate_damage": 50, # 大招伤害
    "ultimate_charge_max": 8,  # 大招蓄能所需攻击次数
    "move_speed": 5,
    "jump_power": 16,
}

# ==================== 小增益(存档点中间) ====================
# 每次随机出现3个，玩家三选一
SMALL_BUFFS = [
    {"id": "hp_up",      "name": "生命强化", "desc": "最大生命值 +20",  "icon": "heart",
     "effect": {"type": "hp_max", "value": 20}},
    {"id": "atk_up",     "name": "力量强化", "desc": "攻击力 +5",       "icon": "sword",
     "effect": {"type": "atk", "value": 5}},
    {"id": "ult_up",     "name": "大招强化", "desc": "大招伤害 +10",    "icon": "star",
     "effect": {"type": "ult_dmg", "value": 10}},
    {"id": "cd_down",    "name": "敏捷强化", "desc": "近战冷却 -0.1秒", "icon": "boot",
     "effect": {"type": "melee_cd", "value": -0.1}},
    {"id": "charge_down","name": "蓄能加速", "desc": "大招蓄能需求 -1",  "icon": "lightning",
     "effect": {"type": "ult_charge", "value": -1}},
    {"id": "range_up",   "name": "范围扩大", "desc": "近战攻击距离 +15", "icon": "arrow",
     "effect": {"type": "melee_range", "value": 15}},
]

# ==================== 大增益(存档点结尾) ====================
# 三选一，每次随机出现3个
BIG_BUFFS = [
    {"id": "double_jump", "name": "二段跳", "desc": "获得二段跳跃能力，跳得更高更远",
     "icon": "wing", "effect": {"type": "skill", "value": "double_jump"}},
    {"id": "dash_attack", "name": "冲刺攻击", "desc": "近战时向前冲刺，伤害提升50%",
     "icon": "dash", "effect": {"type": "skill", "value": "dash_attack"}},
    {"id": "shield", "name": "护盾", "desc": "每10秒自动获得一次免伤护盾",
     "icon": "shield", "effect": {"type": "skill", "value": "shield"}},
    {"id": "invincible_star", "name": "无敌星星", "desc": "获得一个无敌星星道具，使用后无敌5秒",
     "icon": "star_item", "effect": {"type": "item", "value": "invincible_star"}},
    {"id": "speed_potion", "name": "速度药水", "desc": "获得速度药水，使用后移速翻倍10秒",
     "icon": "potion", "effect": {"type": "item", "value": "speed_potion"}},
    {"id": "big_boost", "name": "属性大提升", "desc": "生命+50, 攻击+10, 大招伤害+15",
     "icon": "crown", "effect": {"type": "stat_boost", "values": {"hp_max": 50, "atk": 10, "ult_dmg": 15}}},
    {"id": "lifesteal", "name": "吸血之力", "desc": "近战攻击恢复造成伤害的20%生命值",
     "icon": "vampire", "effect": {"type": "skill", "value": "lifesteal"}},
    {"id": "crit_strike", "name": "暴击精通", "desc": "近战攻击有30%概率造成2倍伤害",
     "icon": "crit", "effect": {"type": "skill", "value": "crit_strike"}},
]

# ==================== 敌人数据 ====================
# 基础属性(普通难度)，实际数值会乘以难度倍率
ENEMY_DATA = {
    # --- 第1关：草原 ---
    "goomba": {
        "name": "栗子仔", "hp": 25, "atk": 10, "speed": 1.5, "xp": 1,
        "behavior": "walk", "color": (160, 90, 40), "size": (32, 32),
        "level": 1, "type": "common",
    },
    "koopa": {
        "name": "乌龟", "hp": 40, "atk": 12, "speed": 1.2, "xp": 2,
        "behavior": "walk", "color": (50, 180, 50), "size": (36, 40),
        "level": 1, "type": "common",
    },
    "bullet_bill": {
        "name": "子弹", "hp": 50, "atk": 15, "speed": 2.0, "xp": 3,
        "behavior": "ranged", "color": (40, 40, 40), "size": (40, 24),
        "level": 1, "type": "special",
        "attack_interval": 2.5, "projectile_speed": 6, "projectile_range": 400,
    },
    # --- 第2关：地下 ---
    "spiny": {
        "name": "刺球", "hp": 30, "atk": 14, "speed": 2.0, "xp": 2,
        "behavior": "walk_fast", "color": (200, 50, 50), "size": (32, 32),
        "level": 2, "type": "common",
    },
    "buzzy_beetle": {
        "name": "铁甲虫", "hp": 55, "atk": 8, "speed": 1.0, "xp": 3,
        "behavior": "walk", "color": (60, 60, 120), "size": (36, 36),
        "level": 2, "type": "common",
    },
    "lakitu": {
        "name": "云龟", "hp": 60, "atk": 16, "speed": 1.0, "xp": 5,
        "behavior": "flying_ranged", "color": (180, 180, 60), "size": (40, 40),
        "level": 2, "type": "special",
        "attack_interval": 3.0, "projectile_speed": 4, "projectile_range": 500,
        "fly_height": 100,
    },
    # --- 第3关：幽灵屋 ---
    "dry_bones": {
        "name": "枯骨", "hp": 50, "atk": 14, "speed": 1.3, "xp": 3,
        "behavior": "walk_revive", "color": (200, 200, 180), "size": (32, 40),
        "level": 3, "type": "common", "revive_times": 1,
    },
    "boo": {
        "name": "幽灵", "hp": 30, "atk": 12, "speed": 2.5, "xp": 2,
        "behavior": "ghost", "color": (255, 255, 255), "size": (36, 36),
        "level": 3, "type": "common",
    },
    "thwomp": {
        "name": "巨石怪", "hp": 120, "atk": 25, "speed": 0, "xp": 8,
        "behavior": "drop", "color": (100, 100, 100), "size": (64, 64),
        "level": 3, "type": "special",
        "attack_interval": 4.0, "drop_range": 200,
    },
    # --- 第4关：熔岩城堡 ---
    "hammer_bro": {
        "name": "锤子龟", "hp": 50, "atk": 18, "speed": 1.5, "xp": 4,
        "behavior": "ranged", "color": (180, 100, 40), "size": (36, 44),
        "level": 4, "type": "common",
        "attack_interval": 2.0, "projectile_speed": 5, "projectile_range": 400,
    },
    "fire_bro": {
        "name": "火焰龟", "hp": 50, "atk": 18, "speed": 1.5, "xp": 4,
        "behavior": "ranged", "color": (220, 80, 30), "size": (36, 44),
        "level": 4, "type": "common",
        "attack_interval": 2.5, "projectile_speed": 5, "projectile_range": 400,
    },
    "magikoopa": {
        "name": "魔法龟", "hp": 90, "atk": 22, "speed": 1.0, "xp": 7,
        "behavior": "teleport_ranged", "color": (128, 0, 128), "size": (40, 44),
        "level": 4, "type": "special",
        "attack_interval": 2.0, "projectile_speed": 7, "projectile_range": 500,
        "teleport_interval": 5.0,
    },
    # --- 第5关：Bowser城堡 ---
    "fire_piranha": {
        "name": "火焰花", "hp": 50, "atk": 15, "speed": 0, "xp": 3,
        "behavior": "stationary_ranged", "color": (200, 50, 50), "size": (40, 48),
        "level": 5, "type": "common",
        "attack_interval": 2.0, "projectile_speed": 5, "projectile_range": 350,
    },
    "dry_bones_5": {
        "name": "枯骨精英", "hp": 55, "atk": 16, "speed": 1.3, "xp": 4,
        "behavior": "walk_revive", "color": (220, 220, 200), "size": (32, 40),
        "level": 5, "type": "common", "revive_times": 1,
    },
    "bowser": {
        "name": "Bowser", "hp": 400, "atk": 30, "speed": 1.0, "xp": 50,
        "behavior": "boss", "color": (60, 140, 40), "size": (80, 96),
        "level": 5, "type": "boss",
        "attack_interval": 2.0, "projectile_speed": 6, "projectile_range": 600,
        "phases": 3,  # boss有三个阶段
    },
}

# ==================== 关卡定义 ====================
# 每关: 长度(像素), 背景主题色, 平台布局, 敌人配置, 存档点位置
LEVELS = [
    {
        "id": 1,
        "name": "草原冒险",
        "length": 3200,
        "theme": "grassland",
        "bg_color": (135, 206, 235),  # 天空蓝
        "ground_color": (100, 180, 80),
        "enemies": ["goomba", "koopa", "bullet_bill"],
        "save_points": [1066, 2133, 3100],  # 约1/3, 2/3, 结尾
        "boss": None,
    },
    {
        "id": 2,
        "name": "地底洞窟",
        "length": 3400,
        "theme": "underground",
        "bg_color": (40, 40, 60),
        "ground_color": (80, 60, 100),
        "enemies": ["spiny", "buzzy_beetle", "lakitu"],
        "save_points": [1133, 2266, 3300],
        "boss": None,
    },
    {
        "id": 3,
        "name": "幽灵之屋",
        "length": 3600,
        "theme": "ghost",
        "bg_color": (50, 50, 70),
        "ground_color": (70, 70, 90),
        "enemies": ["dry_bones", "boo", "thwomp"],
        "save_points": [1200, 2400, 3500],
        "boss": None,
    },
    {
        "id": 4,
        "name": "熔岩城堡",
        "length": 3800,
        "theme": "lava",
        "bg_color": (80, 30, 20),
        "ground_color": (60, 30, 20),
        "enemies": ["hammer_bro", "fire_bro", "magikoopa"],
        "save_points": [1266, 2533, 3700],
        "boss": None,
    },
    {
        "id": 5,
        "name": "Bowser的城堡",
        "length": 4000,
        "theme": "castle",
        "bg_color": (40, 20, 20),
        "ground_color": (50, 50, 50),
        "enemies": ["fire_piranha", "dry_bones_5", "bowser"],
        "save_points": [1333, 2666, 3900],
        "boss": "bowser",
    },
]

# ==================== 成就定义 ====================
ACHIEVEMENTS = [
    {"id": "first_adventure", "name": "初次冒险", "desc": "完成第1关", "icon": "flag",
     "hidden": False},
    {"id": "hero_road", "name": "勇者之路", "desc": "通关全部5关", "icon": "crown",
     "hidden": False},
    {"id": "no_damage", "name": "无伤通关", "desc": "不受到任何伤害完成一关", "icon": "shield",
     "hidden": False},
    {"id": "ult_master", "name": "大招大师", "desc": "累计使用大招50次", "icon": "star",
     "hidden": False},
    {"id": "collector", "name": "收藏家", "desc": "收集所有类型的小增益", "icon": "bag",
     "hidden": False},
    {"id": "speedrun", "name": "速通达人", "desc": "30分钟内通关", "icon": "clock",
     "hidden": False},
    {"id": "slayer", "name": "百人斩", "desc": "累计击败100个敌人", "icon": "sword",
     "hidden": False},
    {"id": "hard_master", "name": "难度大师", "desc": "困难难度通关", "icon": "trophy",
     "hidden": False},
    # --- 彩蛋成就 ---
    {"id": "philosopher", "name": "哲学家", "desc": "在一关中静止不动60秒",
     "icon": "think", "hidden": True},
    {"id": "pacifist", "name": "和平主义者", "desc": "不攻击任何敌人完成一关",
     "icon": "peace", "hidden": True},
]

# ==================== 默认按键设置 ====================
DEFAULT_CONTROLS = {
    "move_left": "left",     # 向左移动
    "move_right": "right",   # 向右移动
    "jump": "space",         # 跳跃
    "melee": "j",           # 近战攻击
    "ultimate": "k",        # 大招
    "use_item": "l",        # 使用道具
    "pause": "escape",      # 暂停
}

# ==================== 默认设置 ====================
DEFAULT_SETTINGS = {
    "controls": DEFAULT_CONTROLS,
    "music_volume": 50,    # 0-100
    "sfx_volume": 70,      # 0-100
    "screen_width": 1024,
    "screen_height": 576,
    "fullscreen": False,
}


# ==================== 字体缓存 ====================
_font_cache = {}

def get_font(size, bold=False):
    """获取字体(带缓存)
    使用系统中文字体，确保中文显示正常。
    """
    key = (size, bold)
    if key not in _font_cache:
        # 尝试多个中文字体
        font_names = ["microsoft yahei", "simhei", "arial", None]
        for name in font_names:
            try:
                font = pygame.font.SysFont(name, size, bold=bold)
                _font_cache[key] = font
                break
            except Exception:
                continue
        else:
            _font_cache[key] = pygame.font.Font(None, size)
    return _font_cache[key]


# 需要在文件顶部导入pygame
try:
    import pygame
except ImportError:
    pass
