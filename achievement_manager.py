# -*- coding: utf-8 -*-
"""
achievement_manager.py - 成就系统
====================================
管理游戏成就的解锁与查询。
成就数据保存在 saves/achievements.json 中。
包含普通成就和隐藏彩蛋成就。
"""

import json
import os
import time
from constants import ACHIEVEMENTS, SAVE_DIR


class AchievementManager:
    """成就管理器"""

    def __init__(self):
        self.unlocked = {}  # id: unlock_time
        self.progress = {}  # id: current_value (用于计数型成就)
        self.filepath = os.path.join(SAVE_DIR, "achievements.json")
        self.load()

    def load(self):
        """从文件加载成就数据"""
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.unlocked = data.get("unlocked", {})
            self.progress = data.get("progress", {})
        except (FileNotFoundError, json.JSONDecodeError):
            self.unlocked = {}
            self.progress = {}

    def save(self):
        """保存成就数据"""
        os.makedirs(SAVE_DIR, exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump({"unlocked": self.unlocked, "progress": self.progress}, f,
                       ensure_ascii=False, indent=2)

    def unlock(self, achievement_id):
        """解锁成就
        Returns: 是否是新解锁的
        """
        if achievement_id in self.unlocked:
            return False
        # 检查是否有效
        valid = [a["id"] for a in ACHIEVEMENTS]
        if achievement_id not in valid:
            return False
        self.unlocked[achievement_id] = time.strftime("%Y-%m-%d %H:%M")
        self.save()
        return True

    def update_progress(self, achievement_id, value, target):
        """更新进度型成就
        Args:
            achievement_id: 成就ID
            value: 当前进度值
            target: 目标值
        """
        self.progress[achievement_id] = {"current": value, "target": target}
        if value >= target and achievement_id not in self.unlocked:
            self.unlock(achievement_id)
        self.save()

    def get_achievement_info(self, achievement_id):
        """获取成就详情"""
        for ach in ACHIEVEMENTS:
            if ach["id"] == achievement_id:
                info = dict(ach)
                info["unlocked"] = achievement_id in self.unlocked
                info["unlock_time"] = self.unlocked.get(achievement_id, "")
                if achievement_id in self.progress:
                    info["progress"] = self.progress[achievement_id]
                return info
        return None

    def get_all_achievements(self):
        """获取所有成就(含解锁状态)"""
        result = []
        for ach in ACHIEVEMENTS:
            info = dict(ach)
            info["unlocked"] = ach["id"] in self.unlocked
            info["unlock_time"] = self.unlocked.get(ach["id"], "")
            if ach["id"] in self.progress:
                info["progress"] = self.progress[ach["id"]]
            result.append(info)
        return result

    def get_unlocked_count(self):
        """已解锁成就数"""
        return len(self.unlocked)

    def get_total_count(self):
        """总成就数"""
        return len(ACHIEVEMENTS)

    def is_hidden_unlocked(self, achievement_id):
        """隐藏成就是否已解锁"""
        return achievement_id in self.unlocked

    def check_achievements(self, player, level_index, save_data=None):
        """检查游戏进行中的成就(每帧调用)
        只放不依赖"完成关卡"的成就,避免误触发。
        """
        newly_unlocked = []

        # 初次冒险：完成第1关
        if level_index >= 0 and save_data:
            completed = save_data.get("stats", {}).get("levels_completed", 0)
            if completed >= 1 and self.unlock("first_adventure"):
                newly_unlocked.append("first_adventure")
            if completed >= 5 and self.unlock("hero_road"):
                newly_unlocked.append("hero_road")

            # 大招大师：使用50次大招
            ult_count = save_data.get("stats", {}).get("total_ult_used", 0)
            if ult_count >= 50 and self.unlock("ult_master"):
                newly_unlocked.append("ult_master")

            # 百人斩：击败100个敌人
            kills = save_data.get("stats", {}).get("total_enemies_killed", 0)
            if kills >= 100 and self.unlock("slayer"):
                newly_unlocked.append("slayer")

            # 速通达人
            playtime = save_data.get("stats", {}).get("total_playtime", 0)
            if completed >= 5 and playtime < 1800:
                if self.unlock("speedrun"):
                    newly_unlocked.append("speedrun")

        # 彩蛋：哲学家(静止60秒)
        if player.still_timer >= 60:
            if self.unlock("philosopher"):
                newly_unlocked.append("philosopher")

        # 收藏家：收集所有小增益
        from constants import SMALL_BUFFS
        all_small_ids = {b["id"] for b in SMALL_BUFFS}
        if all_small_ids.issubset(player.buffs_collected):
            if self.unlock("collector"):
                newly_unlocked.append("collector")

        return newly_unlocked

    def check_level_complete_achievements(self, player, level_index, save_data=None):
        """关卡完成时检查的成就
        这些成就必须在玩家完成一关的那一刻检查,
        否则会在关卡刚开始时就误触发。
        """
        newly_unlocked = []

        # 无伤通关
        if player.damage_taken_this_level == 0 and level_index is not None:
            if self.unlock("no_damage"):
                newly_unlocked.append("no_damage")

        # 和平主义者(不攻击完成一关)
        if player.no_attack_this_level and level_index is not None:
            if self.unlock("pacifist"):
                newly_unlocked.append("pacifist")

        # 难度大师：困难通关
        if save_data and save_data.get("difficulty") == "hard":
            completed = save_data.get("stats", {}).get("levels_completed", 0)
            if completed >= 5 and self.unlock("hard_master"):
                newly_unlocked.append("hard_master")

        return newly_unlocked