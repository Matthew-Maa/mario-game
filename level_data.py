# -*- coding: utf-8 -*-
"""
level_data.py - 关卡数据生成
====================================
为每一关生成平台布局、敌人位置、存档点位置等数据。
关卡数据是程序化生成的，每次运行相同。
"""

import random
from constants import LEVELS, ENEMY_DATA


def _snap_to_ground(platforms, x, ground_y=480):
    """把 x 坐标吸附到最近的地面上方，避免落在缺口里。

    地面是程序化生成的，随机缺口可能正好位于存档点或敌人脚下，
    导致重生即坠死 / 敌人永久卡在深渊。此函数把坐标钳制进
    离原位置最近的一段地面。
    Returns: 吸附后的 x 坐标(找不到地面时返回原值)
    """
    best = None
    for px, py, pw, ph in platforms:
        if py == ground_y and pw >= 40:
            cx = min(max(x, px + 10), px + pw - 30)
            d = abs(cx - x)
            if best is None or d < best[0]:
                best = (d, cx)
    return best[1] if best else x


def generate_level(level_index, difficulty="normal"):
    """生成关卡数据
    Args:
        level_index: 关卡索引(0-4)
        difficulty: 难度
    Returns:
        dict: 包含 platforms, enemies, save_points, length, theme 等
    """
    from constants import DIFFICULTY

    level = LEVELS[level_index]
    level_data = {
        "id": level["id"],
        "name": level["name"],
        "length": level["length"],
        "theme": level["theme"],
        "bg_color": level["bg_color"],
        "ground_color": level["ground_color"],
        "enemy_types": level["enemies"],
        "save_points": level["save_points"],
        "boss": level.get("boss"),
        "platforms": [],
        "enemies_data": [],  # [(type, x, y), ...]
        "difficulty": difficulty,
    }

    # 固定随机种子，确保关卡布局一致
    rng = random.Random(level["id"] * 1000 + 42)

    diff = DIFFICULTY[difficulty]
    hp_mul = diff["enemy_hp_mul"]
    atk_mul = diff["enemy_atk_mul"]

    length = level["length"]
    ground_y = 480  # 地面高度
    ground_height = 96

    # ===== 地面平台(分段，有缺口) =====
    x = 0
    while x < length:
        gap = rng.randint(0, 1) if x > 200 and x < length - 200 else 0
        if gap:
            gap_width = rng.randint(60, 120)
            x += gap_width
        seg_len = rng.randint(200, 400)
        if x + seg_len > length:
            seg_len = length - x
        level_data["platforms"].append((x, ground_y, seg_len, ground_height))
        x += seg_len

    # ===== 浮空平台 =====
    num_platforms = length // 300
    for i in range(num_platforms):
        px = 150 + i * 300 + rng.randint(-50, 50)
        py = rng.choice([200, 250, 300, 350])
        pw = rng.randint(80, 150)
        level_data["platforms"].append((px, py, pw, 20))

    # ===== 敌人放置 =====
    enemy_types = level["enemies"]
    common_types = [t for t in enemy_types if ENEMY_DATA[t].get("type") == "common"]
    special_type = [t for t in enemy_types if ENEMY_DATA[t].get("type") == "special"]
    boss_type = [t for t in enemy_types if ENEMY_DATA[t].get("type") == "boss"]

    # 普通敌人
    num_enemies = 8 + level_index * 2  # 难度递增
    for i in range(num_enemies):
        ex = 300 + (length - 600) * (i / num_enemies) + rng.randint(-80, 80)
        etype = rng.choice(common_types)
        ex = _snap_to_ground(level_data["platforms"], ex)  # 吸附到地面，避免生成在缺口上方
        level_data["enemies_data"].append((etype, int(ex), ground_y))

    # 特殊敌人
    if special_type:
        num_special = 2 + level_index
        for i in range(num_special):
            ex = 500 + (length - 800) * (i / max(1, num_special)) + rng.randint(-50, 50)
            ex = _snap_to_ground(level_data["platforms"], ex)  # 吸附到地面
            ey = ground_y
            # === 修复：Thwomp 这类"从天而降"的敌人需要悬停在空中 ===
            # 之前直接放在地面，drop 行为完全不会触发(砸下后立刻回到原高度)
            if ENEMY_DATA[special_type[0]].get("behavior") == "drop":
                ey = ground_y - 150
            level_data["enemies_data"].append((special_type[0], int(ex), ey))

    # boss
    if boss_type:
        level_data["enemies_data"].append((boss_type[0], length - 200, ground_y))

    # ===== 存档点 =====
    # === 修复：把存档点吸附到地面，避免正好落在缺口上方 ===
    # 否则玩家在该存档点重生会直接坠死，或在半空中触发增益选择
    level_data["save_points"] = [
        _snap_to_ground(level_data["platforms"], sp) for sp in level["save_points"]
    ]

    return level_data
