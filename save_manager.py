# -*- coding: utf-8 -*-
"""
save_manager.py - 存档管理
====================================
管理3个存档槽，包括：
- 创建新存档(选择难度)
- 加载已有存档继续游戏
- 删除存档
- 保存游戏进度
"""

import json
import os
import time
from constants import SAVE_DIR, PLAYER_BASE, DIFFICULTY


class SaveManager:
    """存档管理器"""

    MAX_SLOTS = 3

    def __init__(self):
        self.slots = [None] * self.MAX_SLOTS
        self.load_all()

    def load_all(self):
        """加载所有存档槽"""
        os.makedirs(SAVE_DIR, exist_ok=True)
        for i in range(self.MAX_SLOTS):
            path = os.path.join(SAVE_DIR, f"save_{i}.json")
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.slots[i] = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                self.slots[i] = None

    def save_slot(self, slot_index):
        """保存存档槽到文件"""
        if 0 <= slot_index < self.MAX_SLOTS and self.slots[slot_index]:
            path = os.path.join(SAVE_DIR, f"save_{slot_index}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.slots[slot_index], f, ensure_ascii=False, indent=2)

    def create_new_save(self, slot_index, difficulty):
        """创建新存档
        Args:
            slot_index: 存档槽(0-2)
            difficulty: 难度 "easy"/"normal"/"hard"
        """
        diff = DIFFICULTY[difficulty]
        self.slots[slot_index] = {
            "difficulty": difficulty,
            "current_level": 0,  # 当前关卡索引(0-4)
            "current_checkpoint": 0,  # 当前存档点索引(0-2)
            "timestamp": time.time(),
            "created_at": time.strftime("%Y-%m-%d %H:%M"),
            "last_played": time.strftime("%Y-%m-%d %H:%M"),
            # 玩家属性快照
            "player_stats": {
                "max_hp": diff["player_hp"],
                "atk": diff["player_atk"],
                "melee_cd": diff["melee_cd"],
                "melee_range": PLAYER_BASE["melee_range"],
                "ultimate_damage": PLAYER_BASE["ultimate_damage"],
                "ultimate_charge_max": PLAYER_BASE["ultimate_charge_max"],
            },
            # 已获得的增益
            "skills": [],
            "items": {},
            "buffs_collected": [],
            # 统计数据
            "stats": {
                "total_enemies_killed": 0,
                "total_ult_used": 0,
                "total_playtime": 0,
                "levels_completed": 0,
                "no_damage_levels": 0,
            },
        }
        self.save_slot(slot_index)

    def get_slot_info(self, slot_index):
        """获取存档槽信息(用于显示)"""
        if 0 > slot_index or slot_index >= self.MAX_SLOTS:
            return None
        slot = self.slots[slot_index]
        if not slot:
            return None
        diff_name = DIFFICULTY[slot["difficulty"]]["name"]
        level = slot["current_level"] + 1
        return {
            "exists": True,
            "difficulty": diff_name,
            "level": level,
            "checkpoint": slot["current_checkpoint"],
            "created": slot.get("created_at", ""),
            "last_played": slot.get("last_played", ""),
            "enemies_killed": slot.get("stats", {}).get("total_enemies_killed", 0),
            "playtime": slot.get("stats", {}).get("total_playtime", 0),
        }

    def is_slot_empty(self, slot_index):
        """存档槽是否为空"""
        return self.slots[slot_index] is None

    def delete_save(self, slot_index):
        """删除存档"""
        if 0 <= slot_index < self.MAX_SLOTS:
            self.slots[slot_index] = None
            path = os.path.join(SAVE_DIR, f"save_{slot_index}.json")
            try:
                os.remove(path)
            except FileNotFoundError:
                pass

    def update_save(self, slot_index, player, level_index, checkpoint_index, stats=None):
        """更新存档(保存游戏进度)
        Args:
            slot_index: 存档槽
            player: 玩家对象
            level_index: 当前关卡
            checkpoint_index: 当前存档点
            stats: 额外统计数据
        """
        if not self.slots[slot_index]:
            return

        save = self.slots[slot_index]
        save["current_level"] = level_index
        save["current_checkpoint"] = checkpoint_index
        save["last_played"] = time.strftime("%Y-%m-%d %H:%M")

        # 更新玩家属性快照
        save["player_stats"] = {
            "max_hp": player.max_hp,
            "atk": player.atk,
            "melee_cd": player.melee_cd_max,
            "melee_range": player.melee_range,
            "ultimate_damage": player.ultimate_damage,
            "ultimate_charge_max": player.ultimate_charge_max,
        }
        save["skills"] = list(player.skills)
        save["items"] = dict(player.items)
        save["buffs_collected"] = list(player.buffs_collected)
        save["player_hp"] = player.hp  # 当前血量

        # 更新统计
        if stats:
            for key, value in stats.items():
                if key in save["stats"]:
                    save["stats"][key] += value
                else:
                    save["stats"][key] = value

        self.save_slot(slot_index)

    def load_player_state(self, slot_index, player):
        """从存档恢复玩家状态"""
        if not self.slots[slot_index]:
            return
        save = self.slots[slot_index]
        stats = save.get("player_stats", {})
        player.max_hp = stats.get("max_hp", player.max_hp)
        player.hp = save.get("player_hp", player.max_hp)
        player.atk = stats.get("atk", player.atk)
        player.melee_cd_max = stats.get("melee_cd", player.melee_cd_max)
        player.melee_range = stats.get("melee_range", player.melee_range)
        player.ultimate_damage = stats.get("ultimate_damage", player.ultimate_damage)
        player.ultimate_charge_max = stats.get("ultimate_charge_max", player.ultimate_charge_max)
        player.skills = set(save.get("skills", []))
        player.items = dict(save.get("items", {}))
        player.buffs_collected = set(save.get("buffs_collected", []))
        # 护盾初始化
        if "shield" in player.skills:
            player.shield_ready = True
            player.shield_timer = 10.0
