# -*- coding: utf-8 -*-
"""
game.py - 主游戏逻辑
====================================
包含游戏主循环、关卡渲染、战斗系统、存档点/增益选择、
暂停菜单、游戏结束/胜利画面等。
这是游戏的核心引擎文件。
"""

import pygame
import os
import math
import random
import json
import time

from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, WHITE, BLACK, RED, GREEN, BLUE,
    YELLOW, GOLD, GRAY, DARK_GRAY, LIGHT_GRAY, BROWN, ORANGE, PURPLE,
    GRAVITY, SMALL_BUFFS, BIG_BUFFS, LEVELS, ENEMY_DATA, DIFFICULTY,
    IMAGE_DIR, SOUND_DIR, MUSIC_DIR, SAVE_DIR, get_font
)
from player import Player
from enemy import Enemy, Projectile
from level_data import generate_level
from transitions import SmoothTransition


class Game:
    """主游戏类 - 管理游戏状态和循环"""

    # 游戏状态
    STATE_MENU = "menu"
    STATE_PLAYING = "playing"
    STATE_PAUSED = "paused"
    STATE_BUFF_SELECT = "buff_select"
    STATE_LEVEL_COMPLETE = "level_complete"
    STATE_GAME_OVER = "game_over"
    STATE_VICTORY = "victory"

    def __init__(self, screen, settings_mgr, save_mgr, achievement_mgr):
        """初始化游戏"""
        self.screen = screen
        self.settings_mgr = settings_mgr
        self.save_mgr = save_mgr
        self.ach_mgr = achievement_mgr
        self.clock = pygame.time.Clock()

        # 状态
        self.state = self.STATE_MENU
        self.prev_state = None
        self.transition = SmoothTransition(duration=0.4)

        # 菜单系统
        from menu import MenuSystem
        self.menu = MenuSystem(screen, settings_mgr, save_mgr, achievement_mgr)

        # 游戏数据
        self.player = None
        self.current_slot = 0
        self.current_level_index = 0
        self.current_checkpoint = 0
        self.level_data = None
        self.enemies = []
        self.projectiles = []
        self.platforms = []
        self.camera_x = 0
        self.camera_y = 0
        self.level_start_time = 0
        self.total_playtime = 0

        # 存档点状态
        self.activated_checkpoints = set()
        self.buff_selection = []  # 当前可选的增益列表
        self.buff_is_big = False  # 是否是大增益

        # 音频
        self.current_music = None
        self.music_channel = None

        # 效果
        self.particles = []
        self.flash_timer = 0
        self.shake_timer = 0
        self.shake_intensity = 0

        # 存档计时器
        self.save_cooldown = 0

        # 暂停菜单选项
        self.pause_selected = 0

    # ==================== 主循环 ====================

    def run(self):
        """主游戏循环"""
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)

            try:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    else:
                        result = self.handle_event(event)
                        if result == "quit":
                            running = False

                update_result = self.update(dt)
                if update_result == "quit":
                    running = False

                # === 修复：设置里切换分辨率/全屏后，旧的 screen 表面会失效 ===
                # 每帧同步引用当前显示表面，避免画面冻结在黑屏
                self.screen = pygame.display.get_surface()
                self.menu.screen = self.screen

                self.draw()
                pygame.display.flip()

            except Exception as e:
                # 捕获异常，输出到日志文件，防止游戏直接闪退
                import traceback
                err_msg = traceback.format_exc()
                print(f"[游戏异常] {err_msg}")
                try:
                    with open(os.path.join(SAVE_DIR, "crash_log.txt"), "a", encoding="utf-8") as f:
                        f.write(f"\n==== {time.strftime('%Y-%m-%d %H:%M:%S')} ====\n")
                        f.write(err_msg)
                except Exception:
                    pass
                # 重置状态，避免因单个错误陷入死循环
                self.projectiles = []
                self.particles = []
                # 如果玩家已经死亡，进入结算画面
                if self.player and not self.player.alive and self.state == self.STATE_PLAYING:
                    self.state = self.STATE_GAME_OVER

        # 清理
        self._stop_music()
        self._save_settings()

    def handle_event(self, event):
        """处理输入事件"""
        # 菜单状态
        if self.state == self.STATE_MENU:
            action, data = self.menu.handle_event(event)
            return self._handle_menu_action(action, data)

        # 游戏状态
        elif self.state == self.STATE_PLAYING:
            return self._handle_game_event(event)

        # 暂停状态
        elif self.state == self.STATE_PAUSED:
            return self._handle_pause_event(event)

        # 增益选择
        elif self.state == self.STATE_BUFF_SELECT:
            return self._handle_buff_event(event)

        # 游戏结束/胜利
        elif self.state in (self.STATE_GAME_OVER, self.STATE_VICTORY, self.STATE_LEVEL_COMPLETE):
            return self._handle_end_event(event)

        return None

    def update(self, dt):
        """更新游戏状态"""
        # 转场期间仍然更新游戏逻辑(避免输入丢失)
        if self.transition.is_active():
            self.transition.update(dt, self.screen)

        if self.state == self.STATE_MENU:
            if not self.transition.is_active():
                result = self.menu.update(dt)
                if result == "quit":
                    return "quit"
            return None

        elif self.state == self.STATE_PLAYING:
            if not self.transition.is_active():
                self._update_game(dt)

        elif self.state == self.STATE_BUFF_SELECT:
            pass  # 增益选择不需要更新

        # 更新特效
        self._update_particles(dt)
        if self.flash_timer > 0:
            self.flash_timer -= dt
        if self.shake_timer > 0:
            self.shake_timer -= dt

        # 存档冷却
        if self.save_cooldown > 0:
            self.save_cooldown -= dt

        return None

    def draw(self):
        """绘制游戏"""
        if self.state == self.STATE_MENU:
            self.menu.draw()
        elif self.state == self.STATE_PLAYING:
            self._draw_game()
        elif self.state == self.STATE_PAUSED:
            self._draw_game()
            self._draw_pause_menu()
        elif self.state == self.STATE_BUFF_SELECT:
            self._draw_game()
            self._draw_buff_select()
        elif self.state == self.STATE_LEVEL_COMPLETE:
            self._draw_game()
            self._draw_level_complete()
        elif self.state == self.STATE_GAME_OVER:
            self._draw_game()
            self._draw_game_over()
        elif self.state == self.STATE_VICTORY:
            self._draw_victory()

        # 绘制特效
        self._draw_particles()

        # 闪屏效果
        if self.flash_timer > 0:
            flash = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            alpha = int(150 * (self.flash_timer / 0.3))
            flash.fill((255, 255, 255, alpha))
            self.screen.blit(flash, (0, 0))

    # ==================== 菜单动作处理 ====================

    def _handle_menu_action(self, action, data):
        """处理菜单返回的动作"""
        if action == "exit":
            return None  # 菜单自己处理退出动画

        if action == "quit":
            return "quit"

        if action == "new_game":
            slot, difficulty = data
            self._start_new_game(slot, difficulty)

        elif action == "continue_game":
            slot = data
            self._continue_game(slot)

        return None

    def _start_new_game(self, slot, difficulty):
        """开始新游戏"""
        self.current_slot = slot
        self.save_mgr.create_new_save(slot, difficulty)
        self.current_level_index = 0
        self.current_checkpoint = 0
        self._load_level(0, 0)
        self._switch_state(self.STATE_PLAYING)
        self._play_level_music(0)

    def _continue_game(self, slot):
        """继续游戏"""
        self.current_slot = slot
        save = self.save_mgr.slots[slot]
        if not save:
            return
        self.current_level_index = save["current_level"]
        self.current_checkpoint = save["current_checkpoint"]
        self._load_level(self.current_level_index, self.current_checkpoint)
        # 恢复玩家状态
        self.save_mgr.load_player_state(slot, self.player)
        self._switch_state(self.STATE_PLAYING)
        self._play_level_music(self.current_level_index)

    # ==================== 关卡加载 ====================

    def _load_level(self, level_index, checkpoint=0):
        """加载关卡"""
        save = self.save_mgr.slots[self.current_slot]
        difficulty = save["difficulty"]
        self.level_data = generate_level(level_index, difficulty)

        # 平台
        self.platforms = self.level_data["platforms"]

        # 地面边界
        ground_y = 480
        level_bounds = (0, self.level_data["length"])

        # 玩家(从存档点位置开始)
        diff = DIFFICULTY[difficulty]
        if checkpoint == 0:
            px = 100
        else:
            px = self.level_data["save_points"][checkpoint - 1]

        py = ground_y - 50
        self.player = Player(px, py, difficulty)
        self.save_mgr.load_player_state(self.current_slot, self.player)
        self.player.hp = self.player.max_hp  # 每关满血开始

        # 敌人
        self.enemies = []
        for etype, ex, ey in self.level_data["enemies_data"]:
            # boss只在到达最终区域后才激活
            enemy = Enemy(ex, ey, etype,
                          diff["enemy_hp_mul"], diff["enemy_atk_mul"])
            self.enemies.append(enemy)

        self.projectiles = []
        self.camera_x = 0
        self.activated_checkpoints = set()
        self.level_start_time = time.time()
        self.player.damage_taken_this_level = 0
        self.player.attacked_this_level = False
        self.player.no_attack_this_level = True

    # ==================== 游戏更新 ====================

    def _update_game(self, dt):
        """更新游戏逻辑"""
        if not self.player or not self.level_data:
            return

        controls = self.settings_mgr.get_controls()
        keys = pygame.key.get_pressed()

        # 玩家更新
        self.player.update(dt, keys, self.platforms, controls, self.level_data["length"])

        # 防卡死:确保玩家在有效位置
        if self.player.x < 0:
            self.player.x = 0
        if self.player.x + self.player.width > self.level_data["length"]:
            self.player.x = self.level_data["length"] - self.player.width

        # ===== 坠落死亡检测 =====
        # 玩家掉出屏幕下方时，扣除大量伤害(基本必死)
        if self.player.y > SCREEN_HEIGHT + 80:
            self.player.take_damage(self.player.max_hp)
            if not self.player.alive:
                self._switch_state(self.STATE_GAME_OVER)
                self._stop_music()
                return

        # 相机跟随
        target_cam_x = self.player.x - SCREEN_WIDTH // 2
        target_cam_x = max(0, min(target_cam_x, self.level_data["length"] - SCREEN_WIDTH))
        self.camera_x += (target_cam_x - self.camera_x) * 0.1

        # 屏幕震动
        cam_shake_x = 0
        cam_shake_y = 0
        if self.shake_timer > 0:
            cam_shake_x = random.randint(-self.shake_intensity, self.shake_intensity)
            cam_shake_y = random.randint(-self.shake_intensity, self.shake_intensity)

        # ===== 更新敌人 + 踩头碰撞检测 =====
        level_bounds = (0, self.level_data["length"])
        for enemy in self.enemies:
            enemy.update(dt, self.player, self.platforms, self.projectiles, level_bounds)
            # === 修复：敌人掉入深渊(如被击退到缺口下方)直接移除 ===
            # 否则会一直在屏幕下方存活并继续射击，且永远不会被清理
            if enemy.alive and enemy.y > SCREEN_HEIGHT + 200:
                enemy.alive = False
                enemy._fell_off = True  # 标记为坠落死亡，不计入玩家击杀
                continue
            # 检查与玩家碰撞
            if enemy.alive and not enemy.is_reviving and self.player.alive:
                if enemy.rect.colliderect(self.player.rect):
                    # === 修复：更稳健的踩头判定 ===
                    # 使用"上一帧位置"判断玩家是否从上方落下
                    # 注意 player 更新后的 vy 已经受到重力影响，用当前位置 - vy 近似上一帧位置
                    prev_player_bottom = self.player.rect.bottom - self.player.vy
                    # 只有当玩家底部在敌人顶部附近(上下 20 像素范围内)，才认为是踩头
                    # 同时玩家必须在下落
                    is_stomping = (
                        self.player.vy > 0
                        and prev_player_bottom <= enemy.rect.top + 20
                        and self.player.rect.bottom >= enemy.rect.top
                    )
            
                    if is_stomping:
                        damage = max(self.player.atk, int(enemy.max_hp * 0.3))
                        enemy.take_damage(damage)
                        # 弹起
                        self.player.vy = -self.player.jump_power * 0.7
                        self.player.has_double_jumped = False
                        # === 修复：把玩家移出敌人碰撞箱，避免下一帧重复触发 ===
                        self.player.y = enemy.rect.top - self.player.height - 1
                        # 蓄能
                        self.player.ultimate_charge = min(
                            self.player.ultimate_charge_max, 
                            self.player.ultimate_charge + 1
                        )
                        self.player.attacked_this_level = True
                        self.player.no_attack_this_level = False
                        # 特效
                        self._add_particles(
                            enemy.x + enemy.width // 2,
                            enemy.y, 
                            enemy.color, 8
                        )
                        self._play_sfx("melee")
                        # === 修复：踩头后短暂无敌，防止同一帧被其它敌人伤害 ===
                        self.player.invincible = True
                        self.player.invincible_timer = max(self.player.invincible_timer, 0.3)
                    else:
                        # 非踩头 = 接触伤害
                        self.player.take_damage(enemy.atk)
                        # 击退
                        self.player.vx = -self.player.facing * 4
                        # === 修复：把玩家推离敌人，避免卡在里面每帧掉血 ===
                        if self.player.facing > 0:
                            self.player.x = enemy.rect.left - self.player.width - 1
                        else:
                            self.player.x = enemy.rect.right + 1

        # 更新投射物
        for proj in self.projectiles:
            proj.update(dt, self.platforms)
            # 检查命中玩家
            if proj.alive and proj.source == "enemy" and proj.rect.colliderect(self.player.rect):
                self.player.take_damage(proj.damage)
                proj.alive = False
                self._add_particles(proj.x, proj.y, RED, 8)

        # 统计击杀(必须在过滤之前)
        # 坠落的敌人(_fell_off)不算玩家击杀，也不播放击杀特效
        dead_enemies = [e for e in self.enemies if not e.alive and not e.is_reviving]
        for e in dead_enemies:
            if getattr(e, "_fell_off", False):
                continue
            self.player.enemies_killed += 1
            self._add_particles(e.x + e.width // 2, e.y + e.height // 2, e.color, 12)
            self._play_sfx("enemy_die")

        # 清理死亡敌人和投射物
        self.enemies = [e for e in self.enemies if e.alive or e.is_reviving]
        self.projectiles = [p for p in self.projectiles if p.alive]

        # 检查存档点
        self._check_save_points()

        # 检查关卡完成
        self._check_level_complete()

        # 检查玩家死亡
        if not self.player.alive:
            self._switch_state(self.STATE_GAME_OVER)
            self._stop_music()

        # 速度药水效果恢复
        if self.player.move_speed > 5:
            # 简单处理：5秒后恢复
            if not hasattr(self.player, '_speed_timer'):
                self.player._speed_timer = 5.0
            self.player._speed_timer -= dt
            if self.player._speed_timer <= 0:
                from constants import PLAYER_BASE
                self.player.move_speed = PLAYER_BASE["move_speed"]

        # 更新游戏时间
        self.total_playtime += dt

        # 检查成就
        save = self.save_mgr.slots[self.current_slot]
        save["stats"]["total_enemies_killed"] = save.get("stats", {}).get("total_enemies_killed", 0)
        newly_unlocked = self.ach_mgr.check_achievements(
            self.player, self.current_level_index, save
        )
        for ach_id in newly_unlocked:
            ach_info = self.ach_mgr.get_achievement_info(ach_id)
            if ach_info:
                self.menu.add_notification(f"成就解锁: {ach_info['name']}!", GOLD)
                self._play_sfx("achievement")

    def _handle_game_event(self, event):
        """处理游戏中的输入事件"""
        if not self.player or not self.player.alive:
            return None
        if event.type != pygame.KEYDOWN:
            return None

        controls = self.settings_mgr.get_controls()

        # 跳跃
        if self._check_key(event, controls.get("jump", "space")):
            if self.player.jump():
                self._play_sfx("jump")
            return None

        # 近战攻击(只要不在冷却中就算成功)
        if self._check_key(event, controls.get("melee", "j")):
            self.player.melee_attack(self.enemies, self.projectiles)
            # 不管有没有打中敌人，只要触发了攻击动作就播放音效
            if self.player.attack_anim_timer > 0:
                self._play_sfx("melee")
                ax = self.player.x + (self.player.width if self.player.facing > 0 else -20)
                self._add_particles(ax, self.player.y + 20, WHITE, 5)
            return None

        # 大招
        if self._check_key(event, controls.get("ultimate", "k")):
            if self.player.use_ultimate(self.enemies, self.projectiles):
                self._play_sfx("ultimate")
                self.flash_timer = 0.3
                self.shake_timer = 0.3
                self.shake_intensity = 8
                self._add_particles(
                    self.player.x + self.player.width//2,
                    self.player.y + self.player.height//2,
                    GOLD, 30
                )
            return None

        # 使用道具
        if self._check_key(event, controls.get("use_item", "l")):
            self.player.use_item()
            return None

        # 暂停
        if self._check_key(event, controls.get("pause", "escape")):
            self._switch_state(self.STATE_PAUSED)
            return None

        return None

    def _handle_pause_event(self, event):
        """处理暂停菜单事件"""
        controls = self.settings_mgr.get_controls()
        if event.type == pygame.KEYDOWN:
            if self._check_key(event, controls.get("pause", "escape")):
                self._switch_state(self.STATE_PLAYING)
            elif event.key == pygame.K_UP:
                self.pause_selected = (self.pause_selected - 1) % 4
            elif event.key == pygame.K_DOWN:
                self.pause_selected = (self.pause_selected + 1) % 4
            elif event.key == pygame.K_RETURN:
                if self.pause_selected == 0:  # 继续
                    self._switch_state(self.STATE_PLAYING)
                elif self.pause_selected == 1:  # 保存并退出
                    self._save_and_exit()
                elif self.pause_selected == 2:  # 设置
                    # 保存当前进度后返回主菜单的设置
                    self._save_and_exit()
                elif self.pause_selected == 3:  # 返回主菜单
                    self._switch_state(self.STATE_MENU)

    def _handle_buff_event(self, event):
        """处理增益选择事件"""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_1, pygame.K_a):
                self._select_buff(0)
            elif event.key in (pygame.K_2, pygame.K_s):
                self._select_buff(1)
            elif event.key in (pygame.K_3, pygame.K_d):
                self._select_buff(2)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for i in range(3):
                bx = SCREEN_WIDTH // 2 - 360 + i * 240
                by = SCREEN_HEIGHT // 2 - 80
                if pygame.Rect(bx, by, 220, 160).collidepoint(mx, my):
                    self._select_buff(i)

    def _handle_end_event(self, event):
        """处理结束画面事件"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                if self.state == self.STATE_GAME_OVER:
                    self._switch_state(self.STATE_MENU)
                elif self.state == self.STATE_LEVEL_COMPLETE:
                    self._next_level()
                elif self.state == self.STATE_VICTORY:
                    self._switch_state(self.STATE_MENU)

    def _check_key(self, event, key_name):
        """检查按键是否匹配"""
        key_map = {
            "space": pygame.K_SPACE, "escape": pygame.K_ESCAPE,
            "left": pygame.K_LEFT, "right": pygame.K_RIGHT,
            "up": pygame.K_UP, "down": pygame.K_DOWN,
            "enter": pygame.K_RETURN,
        }
        for c in "abcdefghijklmnopqrstuvwxyz0123456789":
            key_map[c] = ord(c)
        key_map["shift"] = pygame.K_LSHIFT
        key_map["ctrl"] = pygame.K_LCTRL
        key_map["tab"] = pygame.K_TAB

        target = key_map.get(key_name)
        return event.key == target

    # ==================== 存档点 ====================

    def _check_save_points(self):
        """检查是否到达存档点"""
        # 玩家死亡或坠落时不触发存档点
        if self.save_cooldown > 0:
            return
        if not self.player or not self.player.alive:
            return
        # 玩家正在坠落(掉下悬崖)时不触发
        if self.player.y > SCREEN_HEIGHT:
            return
        # === 修复：玩家掉入地面缺口(地面顶部y=480)时不触发 ===
        # 否则会在半空中打开增益界面，选完继续往下掉直接摔死
        if self.player.y > 480:
            return

        save_points = self.level_data["save_points"]
        for i, sp_x in enumerate(save_points):
            if i in self.activated_checkpoints:
                continue
            # 检查玩家是否经过存档点
            if self.player.x > sp_x:
                self.activated_checkpoints.add(i)
                self.current_checkpoint = i
                self._play_sfx("savepoint")

                # 自动保存
                save = self.save_mgr.slots[self.current_slot]
                self.save_mgr.update_save(
                    self.current_slot, self.player,
                    self.current_level_index, i
                )

                # 触发增益选择
                if i < 2:  # 中间存档点 -> 小增益
                    self.buff_is_big = False
                    self.buff_selection = random.sample(SMALL_BUFFS, 3)
                else:  # 结尾存档点 -> 大增益
                    self.buff_is_big = True
                    self.buff_selection = random.sample(BIG_BUFFS, 3)

                self._switch_state(self.STATE_BUFF_SELECT)
                self.save_cooldown = 1.0
                break

    def _select_buff(self, index):
        """选择增益"""
        if 0 <= index < len(self.buff_selection):
            buff = self.buff_selection[index]
            self.player.apply_buff(buff)
            self._play_sfx("pickup")
            self._add_particles(
                self.player.x + self.player.width//2,
                self.player.y + self.player.height//2,
                GREEN, 15
            )
            self.buff_selection = []
            self._switch_state(self.STATE_PLAYING)

    # ==================== 关卡完成 ====================

    def _check_level_complete(self):
        """检查是否完成关卡"""
        # 到达关卡末尾
        if self.player.x > self.level_data["length"] - 50:
            # 检查所有敌人是否清除(简化：只需到达终点)
            self._switch_state(self.STATE_LEVEL_COMPLETE)
            self._stop_music()

            # 更新存档
            save = self.save_mgr.slots[self.current_slot]
            save["stats"]["levels_completed"] = self.current_level_index + 1
            save["stats"]["total_enemies_killed"] = save["stats"].get("total_enemies_killed", 0) + self.player.enemies_killed
            save["stats"]["total_ult_used"] = save["stats"].get("total_ult_used", 0) + self.player.ult_used_count
            save["stats"]["total_playtime"] = int(self.total_playtime)
            if self.player.damage_taken_this_level == 0:
                save["stats"]["no_damage_levels"] = save["stats"].get("no_damage_levels", 0) + 1
            self.save_mgr.save_slot(self.current_slot)

            # 检查成就(关卡完成专用)
            newly_unlocked = self.ach_mgr.check_level_complete_achievements(
                self.player, self.current_level_index, save
            )            
            for ach_id in newly_unlocked:
                ach_info = self.ach_mgr.get_achievement_info(ach_id)
                if ach_info:
                    self.menu.add_notification(f"成就解锁: {ach_info['name']}!", GOLD)

    def _next_level(self):
        """进入下一关"""
        self.current_level_index += 1
        if self.current_level_index >= len(LEVELS):
            # 通关!
            self._switch_state(self.STATE_VICTORY)
            self._play_music("music_victory.wav")
            save = self.save_mgr.slots[self.current_slot]
            save["stats"]["levels_completed"] = 5
            self.save_mgr.save_slot(self.current_slot)
        else:
            self.current_checkpoint = 0
            self._load_level(self.current_level_index, 0)
            self._switch_state(self.STATE_PLAYING)
            self._play_level_music(self.current_level_index)

    def _save_and_exit(self):
        """保存并退出到菜单"""
        save = self.save_mgr.slots[self.current_slot]
        self.save_mgr.update_save(
            self.current_slot, self.player,
            self.current_level_index, self.current_checkpoint
        )
        self._stop_music()
        self._switch_state(self.STATE_MENU)

    # ==================== 绘制 ====================

    def _draw_game(self):
        """绘制游戏画面"""
        if not self.level_data:
            return

        # 屏幕震动偏移
        cam_shake_x = 0
        cam_shake_y = 0
        if self.shake_timer > 0:
            cam_shake_x = random.randint(-self.shake_intensity, self.shake_intensity)
            cam_shake_y = random.randint(-self.shake_intensity, self.shake_intensity)

        cam_x = int(self.camera_x + cam_shake_x)

        # 背景
        bg = self._load_image(f"bg_{self.level_data['theme']}.png")
        if bg:
            bg = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
            # 背景视差(轻微滚动)
            parallax = int(cam_x * 0.3) % SCREEN_WIDTH
            self.screen.blit(bg, (-parallax, 0))
            self.screen.blit(bg, (SCREEN_WIDTH - parallax, 0))
        else:
            self.screen.fill(self.level_data["bg_color"])

        # 地面
        ground_color = self.level_data["ground_color"]
        ground_tile = self._load_image("tile_ground.png")
        if ground_tile:
            for px, py, pw, ph in self.platforms:
                # === 修复：按平台实际高度缩放瓦片 ===
                # 之前固定 96 高，会把 20px 的浮空平台画成高柱子
                tile = pygame.transform.scale(ground_tile, (32, ph))
                for tx in range(px, px + pw, 32):
                    screen_x = tx - cam_x
                    if -32 <= screen_x <= SCREEN_WIDTH:
                        self.screen.blit(tile, (screen_x, py))
        else:
            for px, py, pw, ph in self.platforms:
                screen_x = px - cam_x
                if screen_x + pw > 0 and screen_x < SCREEN_WIDTH:
                    pygame.draw.rect(self.screen, ground_color, (screen_x, py, pw, ph))

        # 存档点
        save_img = self._load_image("tile_save_point.png")
        for i, sp_x in enumerate(self.level_data["save_points"]):
            screen_x = sp_x - cam_x
            if -50 <= screen_x <= SCREEN_WIDTH + 50:
                if save_img:
                    self.screen.blit(save_img, (screen_x, 420))
                else:
                    pygame.draw.rect(self.screen, GOLD, (screen_x, 420, 4, 60))
                    pygame.draw.polygon(self.screen, GREEN, [(screen_x+4, 422), (screen_x+24, 430), (screen_x+4, 438)])

                # 标记已激活的存档点
                if i in self.activated_checkpoints:
                    font = get_font(12)
                    text = font.render("✓", True, GREEN)
                    self.screen.blit(text, (screen_x - 5, 410))

        # 终点门
        end_x = self.level_data["length"] - 50
        screen_x = end_x - cam_x
        if -50 <= screen_x <= SCREEN_WIDTH + 50:
            end_img = self._load_image("tile_end_gate.png")
            if end_img:
                self.screen.blit(end_img, (screen_x, 420))
            else:
                pygame.draw.rect(self.screen, BROWN, (screen_x, 420, 32, 60))
                pygame.draw.rect(self.screen, GOLD, (screen_x+4, 424, 24, 6))

        # 敌人
        for enemy in self.enemies:
            enemy.draw(self.screen, cam_x)

        # 投射物
        for proj in self.projectiles:
            proj.draw(self.screen, cam_x)

        # 玩家
        if self.player:
            self.player.draw(self.screen, cam_x)

        # HUD
        self._draw_hud(cam_x)

    def _draw_hud(self, cam_x):
        """绘制HUD(血量、大招能量等)"""
        if not self.player:
            return

        # 血量条
        hp_bar_w = 200
        hp_bar_h = 20
        hp_bar_x = 20
        hp_bar_y = 20
        pygame.draw.rect(self.screen, (60, 20, 20), (hp_bar_x-1, hp_bar_y-1, hp_bar_w+2, hp_bar_h+2))
        pygame.draw.rect(self.screen, BLACK, (hp_bar_x, hp_bar_y, hp_bar_w, hp_bar_h))
        hp_w = int(hp_bar_w * self.player.get_hp_pct())
        color = RED if hp_w < hp_bar_w * 0.3 else (255, 165, 0) if hp_w < hp_bar_w * 0.6 else GREEN
        pygame.draw.rect(self.screen, color, (hp_bar_x, hp_bar_y, hp_w, hp_bar_h))
        pygame.draw.rect(self.screen, WHITE, (hp_bar_x, hp_bar_y, hp_bar_w, hp_bar_h), 2)
        font = get_font(14, bold=True)
        hp_text = font.render(f"HP: {self.player.hp}/{self.player.max_hp}", True, WHITE)
        self.screen.blit(hp_text, (hp_bar_x + 5, hp_bar_y + 2))

        # 大招能量条
        ult_bar_w = 200
        ult_bar_h = 16
        ult_bar_x = 20
        ult_bar_y = 48
        pygame.draw.rect(self.screen, (40, 40, 20), (ult_bar_x-1, ult_bar_y-1, ult_bar_w+2, ult_bar_h+2))
        pygame.draw.rect(self.screen, BLACK, (ult_bar_x, ult_bar_y, ult_bar_w, ult_bar_h))
        ult_w = int(ult_bar_w * self.player.get_ult_charge_pct())
        ult_color = GOLD if self.player.ultimate_charge >= self.player.ultimate_charge_max else (180, 140, 0)
        pygame.draw.rect(self.screen, ult_color, (ult_bar_x, ult_bar_y, ult_w, ult_bar_h))
        pygame.draw.rect(self.screen, WHITE, (ult_bar_x, ult_bar_y, ult_bar_w, ult_bar_h), 2)
        ult_text = font.render(f"大招: {self.player.ultimate_charge}/{self.player.ultimate_charge_max}", True, WHITE)
        self.screen.blit(ult_text, (ult_bar_x + 5, ult_bar_y + 1))

        # 近战冷却指示
        if self.player.melee_cd > 0:
            cd_pct = self.player.melee_cd / self.player.melee_cd_max
            cd_w = int(60 * cd_pct)
            pygame.draw.rect(self.screen, (40, 40, 40), (230, 48, 60, 16))
            pygame.draw.rect(self.screen, BLUE, (230, 48, 60 - cd_w, 16))
            pygame.draw.rect(self.screen, WHITE, (230, 48, 60, 16), 1)
        else:
            font_s = get_font(12)
            ready = font_s.render("攻击就绪", True, GREEN)
            self.screen.blit(ready, (230, 50))

        # 关卡信息
        font_med = get_font(18, bold=True)
        level_name = self.level_data["name"]
        level_text = font_med.render(f"第{self.current_level_index+1}关: {level_name}", True, WHITE)
        self.screen.blit(level_text, (SCREEN_WIDTH - level_text.get_width() - 20, 20))

        # 难度
        save = self.save_mgr.slots[self.current_slot]
        diff_name = DIFFICULTY[save["difficulty"]]["name"]
        diff_text = font.render(f"难度: {diff_name}", True, LIGHT_GRAY)
        self.screen.blit(diff_text, (SCREEN_WIDTH - diff_text.get_width() - 20, 45))

        # 道具显示
        if self.player.items:
            ix = 20
            iy = 70
            for item_name, count in self.player.items.items():
                pygame.draw.rect(self.screen, (60, 60, 100), (ix, iy, 100, 20))
                pygame.draw.rect(self.screen, WHITE, (ix, iy, 100, 20), 1)
                name_map = {"invincible_star": "无敌星", "speed_potion": "速度药水"}
                t = font.render(f"{name_map.get(item_name, item_name)} x{count}", True, WHITE)
                self.screen.blit(t, (ix + 5, iy + 2))
                iy += 24

        # 技能显示
        if self.player.skills:
            ix = SCREEN_WIDTH - 150
            iy = 70
            skill_map = {
                "double_jump": "二段跳", "dash_attack": "冲刺攻击",
                "shield": "护盾", "lifesteal": "吸血", "crit_strike": "暴击"
            }
            for skill in self.player.skills:
                t = font.render(f"[{skill_map.get(skill, skill)}]", True, GOLD)
                self.screen.blit(t, (ix, iy))
                iy += 18

        # 护盾状态
        if "shield" in self.player.skills:
            if self.player.shield_ready:
                t = font.render("护盾: 就绪", True, GREEN)
            else:
                t = font.render(f"护盾: {self.player.shield_timer:.1f}s", True, GRAY)
            self.screen.blit(t, (230, 70))

    def _draw_pause_menu(self):
        """绘制暂停菜单"""
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        font_big = get_font(40, bold=True)
        font_med = get_font(24, bold=True)

        title = font_big.render("已暂停", True, WHITE)
        self.screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 150))

        options = ["继续游戏", "保存并退出", "设置", "返回主菜单"]
        for i, opt in enumerate(options):
            color = GOLD if i == self.pause_selected else WHITE
            text = font_med.render(opt, True, color)
            x = (SCREEN_WIDTH - text.get_width()) // 2
            y = 250 + i * 50
            self.screen.blit(text, (x, y))

        hint = get_font(14).render("↑↓选择  Enter确认  ESC继续", True, LIGHT_GRAY)
        self.screen.blit(hint, ((SCREEN_WIDTH - hint.get_width()) // 2, SCREEN_HEIGHT - 40))

    def _draw_buff_select(self):
        """绘制增益选择界面"""
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        font_big = get_font(32, bold=True)
        font_med = get_font(20, bold=True)
        font_small = get_font(16)

        title_text = "选择大增益!" if self.buff_is_big else "选择小增益!"
        title_color = GOLD if self.buff_is_big else GREEN
        title = font_big.render(title_text, True, title_color)
        self.screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 100))

        for i, buff in enumerate(self.buff_selection):
            bx = SCREEN_WIDTH // 2 - 360 + i * 240
            by = SCREEN_HEIGHT // 2 - 80
            rect = pygame.Rect(bx, by, 220, 160)

            # 卡片背景
            color = GOLD if self.buff_is_big else GREEN
            pygame.draw.rect(self.screen, (30, 40, 60), rect, border_radius=10)
            pygame.draw.rect(self.screen, color, rect, 3, border_radius=10)

            # 图标
            icon_path = os.path.join(IMAGE_DIR, f"item_{buff['icon']}.png")
            if os.path.exists(icon_path):
                icon = pygame.image.load(icon_path).convert_alpha()
                icon = pygame.transform.scale(icon, (40, 40))
                self.screen.blit(icon, (rect.centerx - 20, rect.y + 15))
            else:
                pygame.draw.rect(self.screen, color, (rect.centerx - 20, rect.y + 15, 40, 40))

            # 名称
            name = font_med.render(buff["name"], True, color)
            self.screen.blit(name, (rect.centerx - name.get_width()//2, rect.y + 60))

            # 描述
            desc = font_small.render(buff["desc"], True, WHITE)
            self.screen.blit(desc, (rect.centerx - desc.get_width()//2, rect.y + 90))

            # 编号
            num = font_big.render(f"{i+1}", True, LIGHT_GRAY)
            self.screen.blit(num, (rect.x + 5, rect.y + 5))

        hint = font_small.render("按 1/2/3 或 点击选择", True, LIGHT_GRAY)
        self.screen.blit(hint, ((SCREEN_WIDTH - hint.get_width()) // 2, SCREEN_HEIGHT - 80))

    def _draw_level_complete(self):
        """绘制关卡完成画面"""
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 50, 0, 180))
        self.screen.blit(overlay, (0, 0))

        font_big = get_font(40, bold=True)
        font_med = get_font(24, bold=True)
        font_small = get_font(18)

        title = font_big.render(f"第{self.current_level_index+1}关完成!", True, GOLD)
        self.screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 150))

        stats_lines = [
            f"击败敌人: {self.player.enemies_killed}",
            f"使用大招: {self.player.ult_used_count}",
            f"受到伤害: {self.player.damage_taken_this_level}",
            f"获得增益: {len(self.player.buffs_collected)}",
        ]
        for i, line in enumerate(stats_lines):
            t = font_med.render(line, True, WHITE)
            self.screen.blit(t, ((SCREEN_WIDTH - t.get_width()) // 2, 230 + i * 35))

        if self.current_level_index + 1 < len(LEVELS):
            next_name = LEVELS[self.current_level_index + 1]["name"]
            t = font_small.render(f"下一关: {next_name}", True, GREEN)
            self.screen.blit(t, ((SCREEN_WIDTH - t.get_width()) // 2, 400))

        hint = font_small.render("按 Enter 继续冒险", True, LIGHT_GRAY)
        self.screen.blit(hint, ((SCREEN_WIDTH - hint.get_width()) // 2, 450))

    def _draw_game_over(self):
        """绘制游戏结束画面"""
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((50, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        font_big = get_font(48, bold=True)
        font_med = get_font(24, bold=True)

        title = font_big.render("游戏结束", True, RED)
        self.screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 200))

        t = font_med.render(f"在第{self.current_level_index+1}关倒下了...", True, WHITE)
        self.screen.blit(t, ((SCREEN_WIDTH - t.get_width()) // 2, 280))

        hint = get_font(18).render("按 Enter 返回主菜单", True, LIGHT_GRAY)
        self.screen.blit(hint, ((SCREEN_WIDTH - hint.get_width()) // 2, 380))

    def _draw_victory(self):
        """绘制胜利画面"""
        self.screen.fill((20, 30, 60))

        font_huge = get_font(56, bold=True)
        font_big = get_font(32, bold=True)
        font_med = get_font(22, bold=True)
        font_small = get_font(18)

        title = font_huge.render("胜利!", True, GOLD)
        self.screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 80))

        sub = font_big.render("你击败了Bowser，拯救了王国!", True, WHITE)
        self.screen.blit(sub, ((SCREEN_WIDTH - sub.get_width()) // 2, 160))

        save = self.save_mgr.slots[self.current_slot]
        stats_lines = [
            f"难度: {DIFFICULTY[save['difficulty']]['name']}",
            f"总击杀: {save['stats'].get('total_enemies_killed', 0)}",
            f"总游戏时间: {int(self.total_playtime)//60}分{int(self.total_playtime)%60}秒",
            f"成就解锁: {self.ach_mgr.get_unlocked_count()}/{self.ach_mgr.get_total_count()}",
        ]
        for i, line in enumerate(stats_lines):
            t = font_med.render(line, True, WHITE)
            self.screen.blit(t, ((SCREEN_WIDTH - t.get_width()) // 2, 240 + i * 35))

        hint = font_small.render("按 Enter 返回主菜单", True, LIGHT_GRAY)
        self.screen.blit(hint, ((SCREEN_WIDTH - hint.get_width()) // 2, SCREEN_HEIGHT - 60))

    # ==================== 粒子系统 ====================

    def _add_particles(self, x, y, color, count=10):
        """添加粒子效果"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 6)
            self.particles.append({
                "x": x, "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - 2,
                "color": color,
                "life": random.uniform(0.3, 0.6),
                "max_life": 0.5,
                "size": random.randint(2, 5),
            })

    def _update_particles(self, dt):
        """更新粒子"""
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.3  # 重力
            p["life"] -= dt
        self.particles = [p for p in self.particles if p["life"] > 0]

    def _draw_particles(self):
        """绘制粒子"""
        for p in self.particles:
            alpha = int(255 * (p["life"] / p["max_life"]))
            size = max(1, int(p["size"] * (p["life"] / p["max_life"])))
            color = (*p["color"][:3], alpha)
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (size, size), size)
            self.screen.blit(surf, (p["x"] - size - self.camera_x, p["y"] - size))

    # ==================== 状态切换 ====================

    def _switch_state(self, new_state):
        """切换游戏状态(带转场)"""
        def do_switch():
            self.prev_state = self.state
            self.state = new_state
        self.transition.start(do_switch)

    # ==================== 音频 ====================

    _image_cache = {}

    def _load_image(self, name):
        """加载并缓存图片"""
        if name not in self._image_cache:
            path = os.path.join(IMAGE_DIR, name)
            if os.path.exists(path):
                self._image_cache[name] = pygame.image.load(path).convert()
            else:
                self._image_cache[name] = None
        return self._image_cache[name]

    def _play_level_music(self, level_index):
        """播放关卡音乐"""
        music_files = [
            "music_level1.wav", "music_level2.wav", "music_level3.wav",
            "music_level4.wav", "music_level5.wav"
        ]
        if level_index < len(music_files):
            self._play_music(music_files[level_index])

    def _play_music(self, filename):
        """播放音乐"""
        path = os.path.join(MUSIC_DIR, filename)
        if os.path.exists(path):
            vol = self.settings_mgr.get_music_volume() / 100.0
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(vol)
            pygame.mixer.music.play(-1)  # 循环播放

    def _stop_music(self):
        """停止音乐"""
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    def _play_sfx(self, name):
        """播放音效"""
        try:
            path = os.path.join(SOUND_DIR, f"sfx_{name}.wav")
            if os.path.exists(path):
                vol = self.settings_mgr.get_sfx_volume() / 100.0
                sound = pygame.mixer.Sound(path)
                sound.set_volume(vol)
                sound.play()
        except Exception:
            pass

    def _save_settings(self):
        """保存设置"""
        self.settings_mgr.save()
