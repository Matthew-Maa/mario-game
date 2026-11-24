# -*- coding: utf-8 -*-
"""
enemy.py - 敌人系统
====================================
定义所有敌人类型，包括：
- 普通行走敌人(Goomba, Koopa, Spiny等)
- 远程攻击敌人(Bullet Bill, Lakitu等)
- 特殊行为敌人(Thwomp, Boo, Magikoopa等)
- Boss(Bowser)
- 投射物类(Projectile)
"""

import pygame
import math
import random
from constants import ENEMY_DATA, GRAVITY, WHITE, BLACK, RED


class Projectile:
    """投射物(火球、锤子、魔法等)"""

    def __init__(self, x, y, vx, vy, damage, proj_type="fireball", source="enemy"):
        """初始化投射物
        Args:
            x, y: 初始位置
            vx, vy: 速度
            damage: 伤害
            proj_type: "fireball"/"hammer"/"magic"
            source: "enemy"/"player" (来源，决定伤害谁)
        """
        self.x = float(x)
        self.y = float(y)
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.proj_type = proj_type
        self.source = source
        self.alive = True
        self.life = 3.0  # 存活时间(秒)
        self.width = 16
        self.height = 16

        # 加载精灵
        self._sprite = None

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def get_sprite(self):
        """加载精灵图"""
        if self._sprite is None:
            from constants import IMAGE_DIR
            import os
            path = os.path.join(IMAGE_DIR, f"proj_{self.proj_type}.png")
            if os.path.exists(path):
                self._sprite = pygame.image.load(path).convert_alpha()
            else:
                self._sprite = pygame.Surface((16, 16), pygame.SRCALPHA)
                self._sprite.fill((255, 100, 0))
        return self._sprite

    def update(self, dt, platforms=None):
        """更新投射物"""
        self.life -= dt
        if self.life <= 0:
            self.alive = False
            return

        # 重力(锤子和魔法不受重力)
        if self.proj_type == "fireball":
            self.vy += GRAVITY * 0.3
        # 移动
        self.x += self.vx
        self.y += self.vy

        # 碰撞检测
        if platforms:
            rect = self.rect
            for px, py, pw, ph in platforms:
                if rect.colliderect(pygame.Rect(px, py, pw, ph)):
                    self.alive = False
                    return

    def draw(self, screen, camera_x):
        """绘制投射物"""
        sprite = self.get_sprite()
        screen.blit(sprite, (int(self.x - camera_x), int(self.y)))


class Enemy:
    """敌人基类"""

    def __init__(self, x, y, enemy_type, difficulty_mul_hp=1.0, difficulty_mul_atk=1.0):
        """初始化敌人
        Args:
            x, y: 初始位置
            enemy_type: 敌人类型名(对应ENEMY_DATA的key)
            difficulty_mul_hp: 难度血量倍率
            difficulty_mul_atk: 难度攻击倍率
        """
        data = ENEMY_DATA[enemy_type]
        self.type = enemy_type
        self.name = data["name"]
        self.max_hp = int(data["hp"] * difficulty_mul_hp)
        self.hp = self.max_hp
        self.atk = int(data["atk"] * difficulty_mul_atk)
        self.speed = data["speed"]
        self.xp = data.get("xp", 1)
        self.behavior = data["behavior"]
        self.color = data["color"]
        self.width, self.height = data["size"]
        self.is_special = data.get("type") in ("special", "boss")
        self.is_boss = data.get("type") == "boss"

        self.x = float(x)
        self.y = float(y - self.height)  # 站在地面上
        self.vx = -self.speed  # 默认向左走
        self.vy = 0
        self.alive = True
        self.on_ground = False
        self.facing = -1

        # 行为参数
        self.attack_timer = 0
        self.attack_interval = data.get("attack_interval", 2.0)
        self.projectile_speed = data.get("projectile_speed", 5)
        self.projectile_range = data.get("projectile_range", 400)
        self.fly_height = data.get("fly_height", 0)
        self.teleport_interval = data.get("teleport_interval", 5.0)
        self.teleport_timer = 0
        self.revive_times = data.get("revive_times", 0)
        self.revive_timer = 0
        self.is_reviving = False
        self.drop_range = data.get("drop_range", 200)

        # boss阶段
        self.boss_phase = 1
        self.boss_max_phases = data.get("phases", 1)

        # 受伤闪烁
        self.hurt_timer = 0
        self.walk_frame = 0
        self.walk_timer = 0

        # 原始位置(用于巡逻)
        self.spawn_x = x
        self.spawn_y = self.y

        # 精灵缓存
        self._sprite = None

    @property
    def rect(self):
        """碰撞箱"""
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def get_sprite(self):
        """加载精灵图"""
        if self._sprite is None:
            from constants import IMAGE_DIR
            import os
            path = os.path.join(IMAGE_DIR, f"enemy_{self.type}.png")
            if os.path.exists(path):
                self._sprite = pygame.image.load(path).convert_alpha()
            else:
                # 回退：纯色方块
                self._sprite = pygame.Surface(self.rect.size, pygame.SRCALPHA)
                self._sprite.fill(self.color)
        return self._sprite

    def update(self, dt, player, platforms, projectiles, level_bounds):
        """更新敌人状态
        Args:
            dt: 帧间隔
            player: 玩家对象
            platforms: 平台列表
            projectiles: 投射物列表(用于添加新的投射物)
            level_bounds: (x_min, x_max) 关卡边界
        """
        if not self.alive:
            return

        if self.hurt_timer > 0:
            self.hurt_timer -= dt

        # 根据行为类型更新
        if self.is_reviving:
            self._update_revive(dt)
            return

        method_name = f"_update_{self.behavior}"
        if hasattr(self, method_name):
            getattr(self, method_name)(dt, player, platforms, projectiles, level_bounds)
        else:
            self._update_walk(dt, player, platforms, projectiles, level_bounds)

        # 行走动画
        if self.is_moving():
            self.walk_timer += dt
            if self.walk_timer > 0.2:
                self.walk_timer = 0
                self.walk_frame = (self.walk_frame + 1) % 2

    def is_moving(self):
        """是否在移动"""
        return abs(self.vx) > 0.1

    def _player_in_range(self, player):
        """玩家是否处于远程攻击范围内(projectile_range)"""
        dx = (player.x + player.width / 2) - (self.x + self.width / 2)
        return abs(dx) <= self.projectile_range

    def take_damage(self, damage):
        """受到伤害
        Returns: 实际伤害值
        """
        if not self.alive:
            return 0
        self.hp -= damage
        self.hurt_timer = 0.15

        # 击退
        self.vx += self.facing * -2

        if self.hp <= 0:
            if self.revive_times > 0 and not self.is_reviving:
                self.revive_times -= 1
                self.is_reviving = True
                self.revive_timer = 3.0
                self.hp = self.max_hp // 2  # 复活时半血
                return damage
            self.alive = False
        return damage

    def draw(self, screen, camera_x):
        """绘制敌人"""
        if not self.alive and not self.is_reviving:
            return

        sprite = self.get_sprite()

        # 受伤闪烁
        if self.hurt_timer > 0:
            # 白色闪烁
            sprite = sprite.copy()
            sprite.fill((255, 255, 255, 100), special_flags=pygame.BLEND_RGBA_ADD)

        # 翻转
        if self.facing > 0:
            sprite = pygame.transform.flip(sprite, True, False)

        screen_x = int(self.x - camera_x)
        screen_y = int(self.y)

        if self.is_reviving:
            # 复活时闪烁
            if int(self.revive_timer * 10) % 2 == 0:
                sprite = sprite.copy()
                sprite.set_alpha(128)

        screen.blit(sprite, (screen_x, screen_y))

        # boss血条
        if self.is_boss and self.alive:
            self._draw_boss_health(screen, camera_x)

    def _draw_boss_health(self, screen, camera_x):
        """绘制boss血条"""
        bar_width = 400
        bar_height = 20
        bar_x = (screen.get_width() - bar_width) // 2
        bar_y = 20

        # 背景
        pygame.draw.rect(screen, (60, 20, 20), (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4))
        pygame.draw.rect(screen, BLACK, (bar_x, bar_y, bar_width, bar_height))
        # 血量
        hp_pct = self.hp / self.max_hp if self.max_hp > 0 else 0
        hp_width = int(bar_width * hp_pct)
        color = RED if hp_pct < 0.3 else (255, 165, 0) if hp_pct < 0.6 else (50, 200, 50)
        pygame.draw.rect(screen, color, (bar_x, bar_y, hp_width, bar_height))
        # 边框
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        # 名字
        from constants import get_font
        font = get_font(16)
        text = font.render(f"{self.name}  Phase {self.boss_phase}/{self.boss_max_phases}", True, WHITE)
        screen.blit(text, (bar_x + 10, bar_y + 1))

    # ==================== 行为模式 ====================

    def _update_walk(self, dt, player, platforms, projectiles, level_bounds):
        """普通行走"""
        self.vy += GRAVITY
        self.x += self.vx
        self._check_horizontal_collision(platforms)
        self.y += self.vy
        self._check_vertical_collision(platforms)

        # 遇到边界或墙壁转向
        x_min, x_max = level_bounds
        if self.x < x_min or self.x + self.width > x_max:
            self.vx = -self.vx
            # === 修复：朝向直接由速度方向决定 ===
            # 旧逻辑只在 vx<0 时翻转，向左撞墙后朝右走但朝向仍为左，精灵图反向
            self.facing = 1 if self.vx > 0 else -1
            if self.x < x_min:
                self.x = x_min
            if self.x + self.width > x_max:
                self.x = x_max - self.width

        if self.on_ground:
            # 检查前方是否有平台(不掉下去)
            check_x = self.x + (self.width if self.vx > 0 else 0)
            check_y = self.y + self.height + 5
            found_ground = False
            for px, py, pw, ph in platforms:
                if pygame.Rect(px, py, pw, ph).collidepoint(check_x, check_y):
                    found_ground = True
                    break
            if not found_ground:
                self.vx = -self.vx
                self.facing = 1 if self.vx > 0 else -1

    def _update_walk_fast(self, dt, player, platforms, projectiles, level_bounds):
        """快速行走(刺球)"""
        self._update_walk(dt, player, platforms, projectiles, level_bounds)
        # 加速
        if abs(self.vx) < self.speed:
            self.vx = self.speed * (1 if self.vx > 0 else -1)

    def _update_walk_revive(self, dt, player, platforms, projectiles, level_bounds):
        """会复活的行走(枯骨)"""
        self._update_walk(dt, player, platforms, projectiles, level_bounds)

    def _update_ranged(self, dt, player, platforms, projectiles, level_bounds):
        """远程攻击敌人(Bullet Bill, Hammer Bro等)"""
        # 基本行走
        self.vy += GRAVITY
        self.x += self.vx * 0.5  # 移动较慢
        self._check_horizontal_collision(platforms)
        self.y += self.vy
        self._check_vertical_collision(platforms)

        # 边界
        x_min, x_max = level_bounds
        if self.x < x_min:
            self.x = x_min; self.vx = abs(self.vx)
        if self.x + self.width > x_max:
            self.x = x_max - self.width; self.vx = -abs(self.vx)
        self.facing = 1 if player.x > self.x else -1

        # 定时射击
        # === 修复：只在玩家进入射程后才开火 ===
        # 旧逻辑无视距离，地图另一端的敌人也会持续朝玩家射击
        self.attack_timer += dt
        if self.attack_timer >= self.attack_interval and self._player_in_range(player):
            self.attack_timer = 0
            self._shoot_projectile(player, projectiles)

    def _update_flying_ranged(self, dt, player, platforms, projectiles, level_bounds):
        """飞行远程敌人(Lakitu)"""
        # 在空中悬浮，跟随玩家
        target_x = player.x - self.width // 2
        if self.x < target_x:
            self.x += self.speed
            self.facing = 1
        elif self.x > target_x:
            self.x -= self.speed
            self.facing = -1

        # 保持飞行高度
        target_y = player.y - self.fly_height
        if self.y < target_y:
            self.y += 2
        elif self.y > target_y:
            self.y -= 2

        # 射击
        self.attack_timer += dt
        if self.attack_timer >= self.attack_interval:
            self.attack_timer = 0
            self._shoot_projectile(player, projectiles)

    def _update_ghost(self, dt, player, platforms, projectiles, level_bounds):
        """幽灵(Boo) - 玩家背对时移动"""
        # 检查玩家是否面向敌人
        player_facing = getattr(player, 'facing', 1)
        player_looking = (player.x < self.x and player_facing > 0) or (player.x > self.x and player_facing < 0)

        if not player_looking:
            # 向玩家移动
            dx = player.x - self.x
            dy = player.y - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed
            self.facing = 1 if dx > 0 else -1
        # 面对时不动

    def _update_drop(self, dt, player, platforms, projectiles, level_bounds):
        """从上方砸下(Thwomp)"""
        self.attack_timer += dt
        dist_to_player = abs(player.x - self.x)

        if self.attack_timer >= self.attack_interval:
            if dist_to_player < self.drop_range and self.y < player.y:
                # 下砸
                self.vy = 15
                self.attack_timer = 0
            else:
                self.attack_timer = self.attack_interval - 0.5  # 快速重试

        self.y += self.vy
        # 撞到平台后回升
        if self.vy > 0:
            for px, py, pw, ph in platforms:
                if self.rect.colliderect(pygame.Rect(px, py, pw, ph)):
                    self.y = py - self.height
                    self.vy = -3  # 缓慢回升
                    break
        elif self.vy < 0:
            if self.y <= self.spawn_y:
                self.y = self.spawn_y
                self.vy = 0

    def _update_stationary_ranged(self, dt, player, platforms, projectiles, level_bounds):
        """固定位置远程(Fire Piranha)"""
        self.facing = 1 if player.x > self.x else -1
        # === 修复：超出射程不开火 ===
        self.attack_timer += dt
        if self.attack_timer >= self.attack_interval and self._player_in_range(player):
            self.attack_timer = 0
            self._shoot_projectile(player, projectiles)

    def _update_teleport_ranged(self, dt, player, platforms, projectiles, level_bounds):
        """传送+远程(Magikoopa)"""
        self.facing = 1 if player.x > self.x else -1
        # === 修复：超出射程不开火 ===
        self.attack_timer += dt
        if self.attack_timer >= self.attack_interval and self._player_in_range(player):
            self.attack_timer = 0
            self._shoot_projectile(player, projectiles)

        self.teleport_timer += dt
        if self.teleport_timer >= self.teleport_interval:
            self.teleport_timer = 0
            # 传送到玩家附近
            new_x = player.x + random.choice([-200, -150, 150, 200])
            new_x = max(level_bounds[0], min(level_bounds[1] - self.width, new_x))
            self.x = new_x

    def _update_boss(self, dt, player, platforms, projectiles, level_bounds):
        """Boss(Bowser)行为"""
        # 阶段切换
        hp_pct = self.hp / self.max_hp
        if hp_pct < 0.66 and self.boss_phase < 2:
            self.boss_phase = 2
            self.speed = 1.5
        if hp_pct < 0.33 and self.boss_phase < 3:
            self.boss_phase = 3
            self.speed = 2.0
            self.attack_interval = 1.5

        self.facing = 1 if player.x > self.x else -1

        # 向玩家移动
        dx = player.x - self.x
        if abs(dx) > 100:
            self.vx = self.speed if dx > 0 else -self.speed
        else:
            self.vx = 0

        self.vy += GRAVITY
        self.x += self.vx
        self._check_horizontal_collision(platforms)
        self.y += self.vy
        self._check_vertical_collision(platforms)

        # 边界
        x_min, x_max = level_bounds
        if self.x < x_min:
            self.x = x_min
        if self.x + self.width > x_max:
            self.x = x_max - self.width

        # 攻击
        self.attack_timer += dt
        if self.attack_timer >= self.attack_interval:
            self.attack_timer = 0
            # Phase 3: 散射3发
            num_shots = 3 if self.boss_phase >= 3 else 1
            for i in range(num_shots):
                angle = -0.3 + (i - num_shots // 2) * 0.3
                self._shoot_projectile(player, projectiles, angle_offset=angle)

    def _update_revive(self, dt):
        """复活过程"""
        self.revive_timer -= dt
        if self.revive_timer <= 0:
            self.is_reviving = False
            self.hp = self.max_hp // 2

    def _shoot_projectile(self, player, projectiles, angle_offset=0):
        """发射投射物"""
        # 计算方向
        dx = (player.x + player.width / 2) - (self.x + self.width / 2)
        dy = (player.y + player.height / 2) - (self.y + self.height / 2)
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 0.1:
            return

        # 确定投射物类型
        if "hammer" in self.type:
            proj_type = "hammer"
        elif "magic" in self.type or "magikoopa" in self.type:
            proj_type = "magic"
        elif "fire" in self.type:
            proj_type = "fireball"
        else:
            proj_type = "fireball"

        vx = (dx / dist) * self.projectile_speed
        vy = (dy / dist) * self.projectile_speed + angle_offset * self.projectile_speed

        proj = Projectile(
            self.x + self.width // 2,
            self.y + self.height // 2,
            vx, vy, self.atk, proj_type, source="enemy"
        )
        projectiles.append(proj)

    def _check_horizontal_collision(self, platforms):
        """水平碰撞"""
        rect = self.rect
        for px, py, pw, ph in platforms:
            plat_rect = pygame.Rect(px, py, pw, ph)
            if rect.colliderect(plat_rect):
                if self.vx > 0:
                    self.x = plat_rect.left - self.width
                elif self.vx < 0:
                    self.x = plat_rect.right
                self.vx = -self.vx
                self.facing = 1 if self.vx > 0 else -1
                rect = self.rect

    def _check_vertical_collision(self, platforms):
        """垂直碰撞"""
        rect = self.rect
        self.on_ground = False
        for px, py, pw, ph in platforms:
            plat_rect = pygame.Rect(px, py, pw, ph)
            if rect.colliderect(plat_rect):
                if self.vy > 0:
                    self.y = plat_rect.top - self.height
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.y = plat_rect.bottom
                    self.vy = 0
                rect = self.rect

    def check_player_collision(self, player):
        """检查与玩家的碰撞，造成接触伤害"""
        if self.alive and self.rect.colliderect(player.rect):
            player.take_damage(self.atk)
