# -*- coding: utf-8 -*-
"""
player.py - 玩家(马里奥)类
====================================
包含玩家移动、跳跃、近战攻击、大招、血量管理、增益效果等功能。
"""

import pygame
import math
import random
from constants import (
    GRAVITY, JUMP_POWER, MOVE_SPEED, MAX_FALL_SPEED,
    PLAYER_BASE, WHITE, RED, BLUE, YELLOW, GREEN, BLACK
)


class Player:
    """马里奥玩家角色"""

    def __init__(self, x, y, difficulty="normal"):
        """初始化玩家
        Args:
            x, y: 初始位置
            difficulty: 难度等级 "easy"/"normal"/"hard"
        """
        from constants import DIFFICULTY

        # 基础属性
        diff = DIFFICULTY[difficulty]
        self.max_hp = diff["player_hp"]
        self.hp = self.max_hp
        self.atk = diff["player_atk"]
        self.melee_cd_max = diff["melee_cd"]
        self.melee_cd = 0  # 当前冷却剩余时间
        self.melee_range = PLAYER_BASE["melee_range"]
        self.ultimate_damage = PLAYER_BASE["ultimate_damage"]
        self.ultimate_charge = 0  # 当前蓄能
        self.ultimate_charge_max = PLAYER_BASE["ultimate_charge_max"]
        self.move_speed = PLAYER_BASE["move_speed"]
        self.jump_power = PLAYER_BASE["jump_power"]

        # 位置与速度
        self.x = float(x)
        self.y = float(y)
        self.vx = 0  # 水平速度
        self.vy = 0  # 垂直速度
        self.width = 28
        self.height = 40
        self.facing = 1  # 朝向: 1=右, -1=左
        self.on_ground = False

        # 状态
        self.alive = True
        self.invincible = False
        self.invincible_timer = 0  # 受伤无敌时间
        self.attack_anim_timer = 0  # 攻击动画计时器
        self.walk_frame = 0
        self.walk_timer = 0
        self.is_moving = False

        # 技能与道具
        self.skills = set()  # 已获得的技能
        self.items = {}  # 道具名: 数量
        self.has_double_jumped = False  # 二段跳标记

        # 跳跃缓冲(让跳跃更灵敏: 按键后短暂内落地仍可跳)
        self.jump_buffer_timer = 0  # 跳跃缓冲计时器(>0表示有缓冲的跳跃请求)
        self.coyote_timer = 0  # 土狼时间(离开地面后短暂内仍可跳)

        # 增益统计(用于成就)
        self.buffs_collected = set()
        self.ult_used_count = 0
        self.enemies_killed = 0
        self.damage_taken_this_level = 0
        self.attacked_this_level = False
        self.still_timer = 0  # 静止计时(彩蛋)
        self.no_attack_this_level = True  # 本关是否未攻击(彩蛋)

        # 护盾技能
        self.shield_ready = False
        self.shield_timer = 0

        # 精灵图缓存
        self._sprites = None

    @property
    def rect(self):
        """碰撞箱"""
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def get_sprites(self):
        """加载精灵图"""
        if self._sprites is None:
            from constants import IMAGE_DIR
            import os
            self._sprites = {}
            for state in ["idle", "walk1", "walk2", "jump", "attack"]:
                path = os.path.join(IMAGE_DIR, f"player_{state}.png")
                if os.path.exists(path):
                    self._sprites[state] = pygame.image.load(path).convert_alpha()
                else:
                    # 如果图片不存在，用纯色方块
                    surf = pygame.Surface((32, 44), pygame.SRCALPHA)
                    surf.fill((220, 30, 30))
                    self._sprites[state] = surf
        return self._sprites

    def update(self, dt, keys, platforms, controls, level_length):
        """更新玩家状态
        Args:
            dt: 帧间隔(秒)
            keys: pygame.key.get_pressed() 的结果
            platforms: 平台列表[(x,y,w,h), ...]
            controls: 按键设置字典
            level_length: 关卡长度
        """
        if not self.alive:
            return

        # ===== 移动输入 =====
        left_key = self._get_key(keys, controls.get("move_left", "left"))
        right_key = self._get_key(keys, controls.get("move_right", "right"))

        was_moving = self.is_moving
        if left_key:
            self.vx = -self.move_speed
            self.facing = -1
            self.is_moving = True
        elif right_key:
            self.vx = self.move_speed
            self.facing = 1
            self.is_moving = True
        else:
            self.vx *= 0.8  # 摩擦力
            if abs(self.vx) < 0.1:
                self.vx = 0
            self.is_moving = False

        # 静止计时(彩蛋: 哲学家)
        if not self.is_moving and abs(self.vy) < 0.1:
            self.still_timer += dt
        else:
            self.still_timer = 0

        # ===== 重力 =====
        self.vy += GRAVITY
        if self.vy > MAX_FALL_SPEED:
            self.vy = MAX_FALL_SPEED

        # ===== 移动与碰撞检测 =====
        # 水平移动
        self.x += self.vx
        self._check_horizontal_collision(platforms)
        # 边界
        if self.x < 0:
            self.x = 0
        if self.x + self.width > level_length:
            self.x = level_length - self.width

        # 垂直移动
        was_on_ground = self.on_ground
        self.y += self.vy
        self.on_ground = False
        self._check_vertical_collision(platforms)

        # 土狼时间: 刚离开地面时给予短暂跳跃宽限
        if was_on_ground and not self.on_ground and self.vy >= 0:
            self.coyote_timer = 0.1
        elif self.on_ground:
            self.coyote_timer = 0.1
        else:
            self.coyote_timer = max(0, self.coyote_timer - dt)

        # 跳跃缓冲: 落地时如果有缓冲的跳跃请求则自动跳
        if self.jump_buffer_timer > 0:
            self.jump_buffer_timer -= dt
            if self.on_ground:
                self._try_jump()

        # ===== 计时器更新 =====
        if self.melee_cd > 0:
            self.melee_cd -= dt
        if self.invincible_timer > 0:
            self.invincible_timer -= dt
            if self.invincible_timer <= 0:
                self.invincible = False
        if self.attack_anim_timer > 0:
            self.attack_anim_timer -= dt
        if self.shield_timer > 0:
            self.shield_timer -= dt
            if self.shield_timer <= 0 and "shield" in self.skills:
                self.shield_ready = True

        # ===== 行走动画 =====
        if self.is_moving and self.on_ground:
            self.walk_timer += dt
            if self.walk_timer > 0.15:
                self.walk_timer = 0
                self.walk_frame = (self.walk_frame + 1) % 2
        else:
            self.walk_frame = 0

    def jump(self):
        """跳跃 - 带跳跃缓冲和土狼时间，让操作更灵敏"""
        # 设置跳跃缓冲(0.12秒内落地自动跳)
        self.jump_buffer_timer = 0.12
        return self._try_jump()

    def _try_jump(self):
        """实际执行跳跃判定"""
        # 地面跳跃 或 土狼时间(离开地面0.1秒内仍可跳)
        if self.on_ground or self.coyote_timer > 0:
            self.vy = -self.jump_power
            self.has_double_jumped = False
            self.jump_buffer_timer = 0
            self.coyote_timer = 0
            return True
        elif "double_jump" in self.skills and not self.has_double_jumped:
            self.vy = -self.jump_power * 0.85
            self.has_double_jumped = True
            self.jump_buffer_timer = 0
            return True
        return False

    def melee_attack(self, enemies, projectiles=None):
        """近战攻击
        Args:
            enemies: 敌人列表
            projectiles: 投射物列表(可选)
        Returns: 攻击是否成功
        """
        if self.melee_cd > 0:
            return False

        self.melee_cd = self.melee_cd_max
        self.attack_anim_timer = 0.25
        self.attacked_this_level = True
        self.no_attack_this_level = False

        # 计算攻击区域
        attack_x = self.x + (self.width // 2) + self.facing * 10
        attack_rect = pygame.Rect(0, 0, self.melee_range, self.height + 10)
        if self.facing > 0:
            attack_rect.midleft = (self.x + self.width, self.y + self.height // 2)
        else:
            attack_rect.midright = (self.x, self.y + self.height // 2)

        damage = self.atk
        # 暴击
        if "crit_strike" in self.skills and random.random() < 0.3:
            damage *= 2
        # 冲刺攻击
        if "dash_attack" in self.skills:
            damage = int(damage * 1.5)
            self.x += self.facing * 15  # 冲刺位移

        hits = 0
        for enemy in enemies:
            if enemy.alive and attack_rect.colliderect(enemy.rect):
                actual_dmg = enemy.take_damage(int(damage))
                hits += 1
                # 吸血
                if "lifesteal" in self.skills and actual_dmg > 0:
                    heal = int(actual_dmg * 0.2)
                    self.hp = min(self.max_hp, self.hp + heal)
                # 蓄能
                if actual_dmg > 0:
                    self.ultimate_charge = min(self.ultimate_charge_max, self.ultimate_charge + 1)

        # 击毁投射物
        if projectiles:
            for proj in projectiles:
                if proj.alive and attack_rect.colliderect(proj.rect):
                    proj.alive = False
                    hits += 1

        return hits > 0

    def use_ultimate(self, enemies, projectiles=None):
        """使用大招
        Args:
            enemies: 敌人列表
            projectiles: 投射物列表(可选)
        Returns: 是否成功释放
        """
        if self.ultimate_charge < self.ultimate_charge_max:
            return False

        self.ultimate_charge = 0
        self.ult_used_count += 1

        # 大招范围：以玩家为中心的较大范围
        ult_range = 200
        ult_rect = pygame.Rect(
            self.x + self.width // 2 - ult_range,
            self.y + self.height // 2 - ult_range,
            ult_range * 2,
            ult_range * 2
        )

        for enemy in enemies:
            if enemy.alive and ult_rect.colliderect(enemy.rect):
                enemy.take_damage(self.ultimate_damage)

        # 清除附近投射物
        if projectiles:
            for proj in projectiles:
                if proj.alive and ult_rect.colliderect(proj.rect):
                    proj.alive = False

        # 短暂无敌
        self.invincible = True
        self.invincible_timer = 1.0

        return True

    def use_item(self):
        """使用道具
        Returns: 是否成功使用
        """
        if not self.items:
            return False
        # 使用第一个可用道具
        for item_name in list(self.items.keys()):
            if self.items[item_name] > 0:
                if item_name == "invincible_star":
                    self.invincible = True
                    self.invincible_timer = 5.0
                    self.items[item_name] -= 1
                    if self.items[item_name] <= 0:
                        del self.items[item_name]
                    return True
                elif item_name == "speed_potion":
                    self.move_speed = PLAYER_BASE["move_speed"] * 2
                    # 使用一个计时器(简化：直接临时加速)
                    self.items[item_name] -= 1
                    if self.items[item_name] <= 0:
                        del self.items[item_name]
                    return True
        return False

    def take_damage(self, damage):
        """受到伤害
        Returns: 实际受到的伤害
        """
        if self.invincible or not self.alive:
            return 0

        # 护盾免伤
        if self.shield_ready:
            self.shield_ready = False
            self.shield_timer = 10.0  # 重新计时
            return 0

        self.hp -= damage
        self.damage_taken_this_level += damage
        self.invincible = True
        self.invincible_timer = 1.0  # 1秒无敌

        # 击退
        self.vx = -self.facing * 4
        self.vy = -6

        if self.hp <= 0:
            self.hp = 0
            self.alive = False

        return damage

    def apply_buff(self, buff):
        """应用增益效果
        Args:
            buff: 增益字典(来自SMALL_BUFFS或BIG_BUFFS)
        """
        self.buffs_collected.add(buff["id"])
        effect = buff["effect"]

        if effect["type"] == "hp_max":
            self.max_hp += effect["value"]
            self.hp += effect["value"]  # 同时恢复
        elif effect["type"] == "atk":
            self.atk += effect["value"]
        elif effect["type"] == "ult_dmg":
            self.ultimate_damage += effect["value"]
        elif effect["type"] == "melee_cd":
            self.melee_cd_max = max(0.2, self.melee_cd_max + effect["value"])
        elif effect["type"] == "ult_charge":
            self.ultimate_charge_max = max(3, self.ultimate_charge_max + effect["value"])
        elif effect["type"] == "melee_range":
            self.melee_range += effect["value"]
        elif effect["type"] == "skill":
            self.skills.add(effect["value"])
            if effect["value"] == "shield":
                self.shield_ready = True
                self.shield_timer = 10.0
        elif effect["type"] == "item":
            item_name = effect["value"]
            self.items[item_name] = self.items.get(item_name, 0) + 1
        elif effect["type"] == "stat_boost":
            vals = effect["values"]
            if "hp_max" in vals:
                self.max_hp += vals["hp_max"]
                self.hp += vals["hp_max"]
            if "atk" in vals:
                self.atk += vals["atk"]
            if "ult_dmg" in vals:
                self.ultimate_damage += vals["ult_dmg"]

    def get_ult_charge_pct(self):
        """获取大招蓄能百分比(0-1)"""
        return self.ultimate_charge / self.ultimate_charge_max

    def get_hp_pct(self):
        """获取血量百分比(0-1)"""
        return self.hp / self.max_hp if self.max_hp > 0 else 0

    def get_current_sprite(self):
        """获取当前应显示的精灵"""
        sprites = self.get_sprites()
        if self.attack_anim_timer > 0:
            return sprites.get("attack", sprites.get("idle"))
        if not self.on_ground:
            return sprites.get("jump", sprites.get("idle"))
        if self.is_moving:
            return sprites.get(f"walk{self.walk_frame + 1}", sprites.get("walk1", sprites.get("idle")))
        return sprites.get("idle")

    def draw(self, screen, camera_x):
        """绘制玩家"""
        sprite = self.get_current_sprite()
        # 闪烁效果(受伤无敌)
        if self.invincible and self.invincible_timer > 0:
            if int(self.invincible_timer * 20) % 2 == 0:
                return  # 闪烁：跳过此帧

        # 翻转精灵
        if self.facing < 0:
            sprite = pygame.transform.flip(sprite, True, False)

        screen_x = int(self.x - camera_x)
        screen_y = int(self.y)
        screen.blit(sprite, (screen_x, screen_y - 4))

        # 大招特效(蓄满时周围有光晕)
        if self.ultimate_charge >= self.ultimate_charge_max:
            cx = screen_x + self.width // 2
            cy = screen_y + self.height // 2
            for i in range(3):
                radius = 30 + i * 8
                alpha = 30 - i * 8
                glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow, (255, 215, 0, alpha), (radius, radius), radius)
                screen.blit(glow, (cx - radius, cy - radius))

    def _get_key(self, keys, key_name):
        """从按键名获取按键状态"""
        key_map = {
            "left": keys[pygame.K_LEFT], "right": keys[pygame.K_RIGHT],
            "up": keys[pygame.K_UP], "down": keys[pygame.K_DOWN],
            "space": keys[pygame.K_SPACE],
            "a": keys[pygame.K_a], "d": keys[pygame.K_d],
            "w": keys[pygame.K_w], "s": keys[pygame.K_s],
            "j": keys[pygame.K_j], "k": keys[pygame.K_k],
            "l": keys[pygame.K_l], "escape": keys[pygame.K_ESCAPE],
            "f": keys[pygame.K_f], "g": keys[pygame.K_g],
            "h": keys[pygame.K_h], "i": keys[pygame.K_i],
            "q": keys[pygame.K_q], "e": keys[pygame.K_e],
            "r": keys[pygame.K_r], "t": keys[pygame.K_t],
            "u": keys[pygame.K_u], "o": keys[pygame.K_o],
            "p": keys[pygame.K_p], "z": keys[pygame.K_z],
            "x": keys[pygame.K_x], "c": keys[pygame.K_c],
            "v": keys[pygame.K_v], "b": keys[pygame.K_b],
            "n": keys[pygame.K_n], "m": keys[pygame.K_m],
            "1": keys[pygame.K_1], "2": keys[pygame.K_2],
            "3": keys[pygame.K_3], "4": keys[pygame.K_4],
            "5": keys[pygame.K_5], "6": keys[pygame.K_6],
            "7": keys[pygame.K_7], "8": keys[pygame.K_8],
            "9": keys[pygame.K_9], "0": keys[pygame.K_0],
            "shift": keys[pygame.K_LSHIFT], "ctrl": keys[pygame.K_LCTRL],
            "tab": keys[pygame.K_TAB], "enter": keys[pygame.K_RETURN],
        }
        return key_map.get(key_name, False)

    def _check_horizontal_collision(self, platforms):
        """水平碰撞检测"""
        rect = self.rect
        for px, py, pw, ph in platforms:
            plat_rect = pygame.Rect(px, py, pw, ph)
            if rect.colliderect(plat_rect):
                if self.vx > 0:  # 向右碰撞
                    self.x = plat_rect.left - self.width
                elif self.vx < 0:  # 向左碰撞
                    self.x = plat_rect.right
                rect = self.rect
                self.vx = 0

    def _check_vertical_collision(self, platforms):
        """垂直碰撞检测"""
        rect = self.rect
        for px, py, pw, ph in platforms:
            plat_rect = pygame.Rect(px, py, pw, ph)
            if rect.colliderect(plat_rect):
                if self.vy > 0:  # 向下碰撞(落地)
                    self.y = plat_rect.top - self.height
                    self.vy = 0
                    self.on_ground = True
                    rect = self.rect
                elif self.vy < 0:  # 向上碰撞(顶到)
                    self.y = plat_rect.bottom
                    self.vy = 0
                    rect = self.rect
