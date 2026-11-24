# -*- coding: utf-8 -*-
"""
menu.py - 菜单系统
====================================
包含主菜单、存档选择、难度选择、游戏规则、成就、设置、退出等界面。
页面间使用平滑切换效果。
"""

import pygame
import os
import math
import webbrowser
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, RED, GREEN, BLUE, YELLOW,
    GOLD, GRAY, DARK_GRAY, LIGHT_GRAY, BROWN, ORANGE, PURPLE,
    DIFFICULTY, ACHIEVEMENTS, DEFAULT_CONTROLS, IMAGE_DIR, BASE_DIR,
    get_font
)
from transitions import SmoothTransition

# 玩家指南 PDF 路径(主界面右下角按钮点击后在浏览器中打开)
GUIDE_PDF_PATH = os.path.join(BASE_DIR, "玩家指南.pdf")
# 主界面右下角"玩家指南"按钮区域
GUIDE_BUTTON_RECT = pygame.Rect(SCREEN_WIDTH - 200, SCREEN_HEIGHT - 66, 170, 46)


class MenuSystem:
    """菜单系统 - 管理所有菜单界面"""

    # 菜单状态
    MAIN_MENU = "main_menu"
    SAVE_SELECT = "save_select"
    DIFFICULTY_SELECT = "difficulty_select"
    RULES = "rules"
    ACHIEVEMENTS = "achievements"
    SETTINGS = "settings"
    CONTROLS_SETTINGS = "controls_settings"
    EXIT = "exit"
    DELETE_CONFIRM = "delete_confirm"

    def __init__(self, screen, settings_mgr, save_mgr, achievement_mgr):
        """初始化菜单系统
        Args:
            screen: pygame显示表面
            settings_mgr: SettingsManager实例
            save_mgr: SaveManager实例
            achievement_mgr: AchievementManager实例
        """
        self.screen = screen
        self.settings_mgr = settings_mgr
        self.save_mgr = save_mgr
        self.ach_mgr = achievement_mgr
        self.state = self.MAIN_MENU
        self.prev_state = self.MAIN_MENU
        self.transition = SmoothTransition(duration=0.4)
        self.selected_slot = 0  # 选择的存档槽
        self.menu_buttons = []
        self.hovered_button = -1
        self.exit_timer = 0
        self.exit_duration = 2.5  # 退出动画时长
        self.rebind_action = None  # 正在重新绑定的动作
        self.settings_scroll = 0

        # 加载标题背景
        self.title_bg = self._load_image("title_bg.png")
        if self.title_bg:
            self.title_bg = pygame.transform.scale(self.title_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))

        # 按钮动画
        self.button_anim_timer = 0

        # 通知队列(成就解锁等)
        self.notifications = []

    def _load_image(self, name):
        """加载图片"""
        path = os.path.join(IMAGE_DIR, name)
        if os.path.exists(path):
            return pygame.image.load(path).convert_alpha()
        return None

    def add_notification(self, text, color=GOLD):
        """添加通知"""
        self.notifications.append({"text": text, "color": color, "timer": 3.0})

    def handle_event(self, event):
        """处理输入事件
        Returns: (action, data) - action为字符串表示要执行的动作
        """
        if self.transition.is_active():
            return None, None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state == self.MAIN_MENU:
                    return "exit", None
                elif self.state in (self.RULES, self.ACHIEVEMENTS, self.SETTINGS,
                                   self.CONTROLS_SETTINGS, self.SAVE_SELECT,
                                   self.DIFFICULTY_SELECT):
                    # === 修复：离开按键设置时取消进行中的重绑定 ===
                    # 否则 rebind_action 会残留，下一次按键会被误绑定
                    self.rebind_action = None
                    self._switch_to(self.MAIN_MENU)
                elif self.state == self.DELETE_CONFIRM:
                    self._switch_to(self.SAVE_SELECT)
                return None, None

        if self.state == self.EXIT:
            return None, None  # 退出动画中不响应输入

        # 鼠标点击处理
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            return self._handle_click(mx, my)

        # 鼠标移动处理(悬停)
        if event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)

        # 按键重绑定
        if self.rebind_action and event.type == pygame.KEYDOWN:
            key_name = pygame.key.name(event.key)
            if key_name != "escape":
                self.settings_mgr.set_control(self.rebind_action, key_name)
                self.rebind_action = None
                self._play_sfx("button")
            return None, None

        return None, None

    def update(self, dt):
        """更新菜单状态"""
        self.button_anim_timer += dt
        self.transition.update(dt, self.screen)

        # 更新通知
        for notif in self.notifications[:]:
            notif["timer"] -= dt
            if notif["timer"] <= 0:
                self.notifications.remove(notif)

        # 退出动画
        if self.state == self.EXIT:
            self.exit_timer += dt
            if self.exit_timer >= self.exit_duration:
                return "quit"
        return None

    def draw(self):
        """绘制当前菜单界面"""
        if self.state == self.MAIN_MENU:
            self._draw_main_menu()
        elif self.state == self.SAVE_SELECT:
            self._draw_save_select()
        elif self.state == self.DIFFICULTY_SELECT:
            self._draw_difficulty_select()
        elif self.state == self.RULES:
            self._draw_rules()
        elif self.state == self.ACHIEVEMENTS:
            self._draw_achievements()
        elif self.state == self.SETTINGS:
            self._draw_settings()
        elif self.state == self.CONTROLS_SETTINGS:
            self._draw_controls_settings()
        elif self.state == self.DELETE_CONFIRM:
            self._draw_save_select()  # 底层显示存档选择
            self._draw_delete_confirm()
        elif self.state == self.EXIT:
            self._draw_exit()

        # 绘制转场遮罩
        self.transition.update(0.016, self.screen)

        # 绘制通知
        self._draw_notifications()

    def _switch_to(self, new_state):
        """切换到新状态(带平滑切换)"""
        def do_switch():
            self.state = new_state
        self.transition.start(do_switch)

    # ==================== 主菜单 ====================

    def _draw_main_menu(self):
        """绘制主菜单"""
        # 背景
        if self.title_bg:
            self.screen.blit(self.title_bg, (0, 0))
        else:
            self.screen.fill((30, 100, 200))

        # 标题
        font_big = get_font(64, bold=True)
        font_med = get_font(28, bold=True)
        font_small = get_font(20)

        # 标题阴影效果
        title = "超级马里奥冒险"
        title_surf = font_big.render(title, True, YELLOW)
        shadow_surf = font_big.render(title, True, BLACK)
        title_x = (SCREEN_WIDTH - title_surf.get_width()) // 2
        self.screen.blit(shadow_surf, (title_x + 3, 103))
        self.screen.blit(title_surf, (title_x, 100))

        # 副标题(深棕色 + 白色描边,避免与云朵撞色)
        sub = "SUPER MARIO ADVENTURE"
        sub_x = (SCREEN_WIDTH - font_med.size(sub)[0]) // 2
        sub_y = 170
        # 白色描边
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, -2), (-2, 2), (2, 2)]:
            outline_surf = font_med.render(sub, True, WHITE)
            self.screen.blit(outline_surf, (sub_x + dx, sub_y + dy))
        # 深棕色主文字
        sub_surf = font_med.render(sub, True, (80, 50, 20))
        self.screen.blit(sub_surf, (sub_x, sub_y))

        # 菜单按钮
        buttons = ["开始游戏", "游戏规则", "成就", "设置", "退出游戏"]
        self.menu_buttons = []
        btn_w, btn_h = 260, 46
        start_y = 215
        for i, text in enumerate(buttons):
            bx = (SCREEN_WIDTH - btn_w) // 2
            by = start_y + i * 58
            rect = pygame.Rect(bx, by, btn_w, btn_h)
            self.menu_buttons.append((rect, text))

            # 悬停效果
            is_hovered = (self.hovered_button == i)
            color = GOLD if is_hovered else (200, 100, 30)
            if is_hovered:
                # 动画缩放
                pulse = int(3 * (1 + math.sin(self.button_anim_timer * 8)) / 2)
                rect = rect.inflate(pulse * 2, pulse * 2)

            # 按钮背景
            pygame.draw.rect(self.screen, (40, 20, 10), rect.move(2, 2), border_radius=10)
            pygame.draw.rect(self.screen, color, rect, border_radius=10)
            pygame.draw.rect(self.screen, WHITE, rect, 2, border_radius=10)

            # 按钮文字
            text_surf = font_med.render(text, True, WHITE)
            self.screen.blit(text_surf, (rect.centerx - text_surf.get_width() // 2,
                                        rect.centery - text_surf.get_height() // 2))

        # 右下角"玩家指南"按钮(点击在浏览器中打开 PDF)
        self._draw_guide_button()

    def _draw_guide_button(self):
        """绘制主界面右下角的玩家指南按钮"""
        rect = GUIDE_BUTTON_RECT
        mx, my = pygame.mouse.get_pos()
        is_hover = rect.collidepoint(mx, my)
        color = (60, 130, 200) if is_hover else (40, 90, 150)
        if is_hover:
            rect = rect.inflate(4, 4)
        pygame.draw.rect(self.screen, (10, 25, 45), rect.move(2, 2), border_radius=8)
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, WHITE, rect, 2, border_radius=8)
        font = get_font(18, bold=True)
        text = font.render("📖 玩家指南", True, WHITE)
        self.screen.blit(text, (rect.centerx - text.get_width() // 2,
                                rect.centery - text.get_height() // 2))

    def _open_guide_pdf(self):
        """在系统默认浏览器中打开玩家指南 PDF"""
        try:
            if os.path.exists(GUIDE_PDF_PATH):
                # 使用 file:// URI，确保各平台浏览器都能打开
                uri = "file:///" + os.path.abspath(GUIDE_PDF_PATH).replace(os.sep, "/")
                webbrowser.open(uri)
                self.add_notification("正在浏览器中打开玩家指南...", GREEN)
            else:
                self.add_notification("未找到 玩家指南.pdf", RED)
        except Exception as e:
            print(f"[警告] 打开玩家指南失败: {e}")
            self.add_notification("打开玩家指南失败", RED)

    def _handle_click(self, mx, my):
        """处理鼠标点击"""
        self._play_sfx("button")

        if self.state == self.MAIN_MENU:
            # 主界面右下角"玩家指南"按钮：在浏览器中打开 PDF
            if GUIDE_BUTTON_RECT.collidepoint(mx, my):
                self._open_guide_pdf()
                return None, None
            for i, (rect, _) in enumerate(self.menu_buttons):
                if rect.collidepoint(mx, my):
                    if i == 0:
                        self._switch_to(self.SAVE_SELECT)
                    elif i == 1:
                        self._switch_to(self.RULES)
                    elif i == 2:
                        self._switch_to(self.ACHIEVEMENTS)
                    elif i == 3:
                        self._switch_to(self.SETTINGS)
                    elif i == 4:
                        self.exit_timer = 0
                        self._switch_to(self.EXIT)
                    return None, None

        elif self.state == self.SAVE_SELECT:
            # 存档槽按钮
            for i in range(self.save_mgr.MAX_SLOTS):
                slot_y = 150 + i * 120
                slot_rect = pygame.Rect(150, slot_y, SCREEN_WIDTH - 300, 100)
                if slot_rect.collidepoint(mx, my):
                    self.selected_slot = i
                    if self.save_mgr.is_slot_empty(i):
                        self._switch_to(self.DIFFICULTY_SELECT)
                    else:
                        # 继续游戏
                        return "continue_game", i
                    return None, None
                # 删除按钮
                if not self.save_mgr.is_slot_empty(i):
                    del_rect = pygame.Rect(SCREEN_WIDTH - 170, slot_y + 30, 80, 40)
                    if del_rect.collidepoint(mx, my):
                        self.selected_slot = i
                        self._switch_to(self.DELETE_CONFIRM)
                        return None, None
            # 返回按钮
            back_rect = pygame.Rect(50, SCREEN_HEIGHT - 70, 120, 50)
            if back_rect.collidepoint(mx, my):
                self._switch_to(self.MAIN_MENU)

        elif self.state == self.DIFFICULTY_SELECT:
            # 难度按钮
            diffs = ["easy", "normal", "hard"]
            for i, diff in enumerate(diffs):
                dx = 200 + i * 220
                dy = 250
                drect = pygame.Rect(dx, dy, 200, 120)
                if drect.collidepoint(mx, my):
                    return "new_game", (self.selected_slot, diff)
            # 返回
            back_rect = pygame.Rect(50, SCREEN_HEIGHT - 70, 120, 50)
            if back_rect.collidepoint(mx, my):
                self._switch_to(self.SAVE_SELECT)

        elif self.state == self.DELETE_CONFIRM:
            # 确认删除
            yes_rect = pygame.Rect(SCREEN_WIDTH // 2 - 120, 380, 100, 50)
            no_rect = pygame.Rect(SCREEN_WIDTH // 2 + 20, 380, 100, 50)
            if yes_rect.collidepoint(mx, my):
                self.save_mgr.delete_save(self.selected_slot)
                self._switch_to(self.SAVE_SELECT)
            elif no_rect.collidepoint(mx, my):
                self._switch_to(self.SAVE_SELECT)

        elif self.state == self.SETTINGS:
            # 音量滑块
            # 音乐音量+-
            if pygame.Rect(500, 200, 40, 40).collidepoint(mx, my):
                vol = self.settings_mgr.get_music_volume()
                self.settings_mgr.set_music_volume(min(100, vol + 10))
                # === 修复：音量调节立即对当前播放的音乐生效 ===
                try:
                    pygame.mixer.music.set_volume(self.settings_mgr.get_music_volume() / 100.0)
                except Exception:
                    pass
            if pygame.Rect(560, 200, 40, 40).collidepoint(mx, my):
                vol = self.settings_mgr.get_music_volume()
                self.settings_mgr.set_music_volume(max(0, vol - 10))
                try:
                    pygame.mixer.music.set_volume(self.settings_mgr.get_music_volume() / 100.0)
                except Exception:
                    pass
            # 音效音量+-
            if pygame.Rect(500, 270, 40, 40).collidepoint(mx, my):
                vol = self.settings_mgr.get_sfx_volume()
                self.settings_mgr.set_sfx_volume(min(100, vol + 10))
            if pygame.Rect(560, 270, 40, 40).collidepoint(mx, my):
                vol = self.settings_mgr.get_sfx_volume()
                self.settings_mgr.set_sfx_volume(max(0, vol - 10))
            # 屏幕大小(立即生效)
            sizes = [(1024, 576), (1280, 720), (800, 450)]
            for i, (w, h) in enumerate(sizes):
                sx = 400 + i * 130
                srect = pygame.Rect(sx, 350, 120, 50)
                if srect.collidepoint(mx, my):
                    self.settings_mgr.set_screen_size(w, h)
                    # 立即改变窗口大小
                    try:
                        flags = pygame.SCALED | pygame.RESIZABLE
                        if self.settings_mgr.get_fullscreen():
                            flags |= pygame.FULLSCREEN
                        # === 修复：set_mode 会返回新的显示表面 ===
                        # 必须更新 self.screen，否则后续绘制仍画在旧表面上，画面冻结
                        self.screen = pygame.display.set_mode((w, h), flags)
                    except Exception as e:
                        print(f"[警告] 切换屏幕大小失败: {e}")
            # 全屏切换(立即生效)
            if pygame.Rect(400, 420, 200, 40).collidepoint(mx, my):
                self.settings_mgr.set_fullscreen(not self.settings_mgr.get_fullscreen())
                try:
                    flags = pygame.SCALED | pygame.RESIZABLE
                    if self.settings_mgr.get_fullscreen():
                        flags |= pygame.FULLSCREEN
                    w, h = self.settings_mgr.get_screen_size()
                    self.screen = pygame.display.set_mode((w, h), flags)
                except Exception as e:
                    print(f"[警告] 切换全屏失败: {e}")
            # 控制设置
            if pygame.Rect(400, 480, 250, 40).collidepoint(mx, my):
                self._switch_to(self.CONTROLS_SETTINGS)
            # 返回
            back_rect = pygame.Rect(50, SCREEN_HEIGHT - 70, 120, 50)
            if back_rect.collidepoint(mx, my):
                self._switch_to(self.MAIN_MENU)

        elif self.state == self.CONTROLS_SETTINGS:
            # 返回
            back_rect = pygame.Rect(50, SCREEN_HEIGHT - 70, 120, 50)
            if back_rect.collidepoint(mx, my):
                self.rebind_action = None  # 取消进行中的重绑定
                self._switch_to(self.SETTINGS)
            # 检查是否点击了某个控制项来重新绑定
            controls = self.settings_mgr.get_controls()
            labels = {
                "move_left": "向左移动", "move_right": "向右移动",
                "jump": "跳跃", "melee": "近战攻击",
                "ultimate": "大招", "use_item": "使用道具", "pause": "暂停"
            }
            for i, (action, _) in enumerate(controls.items()):
                item_y = 130 + i * 50
                key_rect = pygame.Rect(550, item_y, 200, 40)
                if key_rect.collidepoint(mx, my):
                    self.rebind_action = action
                    return None, None

        elif self.state in (self.RULES, self.ACHIEVEMENTS):
            back_rect = pygame.Rect(50, SCREEN_HEIGHT - 70, 120, 50)
            if back_rect.collidepoint(mx, my):
                self._switch_to(self.MAIN_MENU)

        return None, None

    def _update_hover(self, pos):
        """更新鼠标悬停"""
        mx, my = pos
        self.hovered_button = -1
        if self.state == self.MAIN_MENU and self.menu_buttons:
            for i, (rect, _) in enumerate(self.menu_buttons):
                if rect.collidepoint(mx, my):
                    self.hovered_button = i
                    break

    # ==================== 存档选择 ====================

    def _draw_save_select(self):
        """绘制存档选择界面"""
        self.screen.fill((20, 30, 60))
        font_big = get_font(36, bold=True)
        font_med = get_font(22)
        font_small = get_font(16)

        title = font_big.render("选择存档", True, GOLD)
        self.screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 60))

        for i in range(self.save_mgr.MAX_SLOTS):
            slot_y = 150 + i * 120
            slot_rect = pygame.Rect(150, slot_y, SCREEN_WIDTH - 300, 100)

            # 背景
            pygame.draw.rect(self.screen, (40, 50, 80), slot_rect, border_radius=8)
            pygame.draw.rect(self.screen, GOLD, slot_rect, 2, border_radius=8)

            if self.save_mgr.is_slot_empty(i):
                # 空存档
                text = font_med.render(f"存档 {i+1}  -  [空白]", True, LIGHT_GRAY)
                self.screen.blit(text, (slot_rect.x + 20, slot_rect.centery - 12))
                hint = font_small.render("点击开始新游戏", True, GREEN)
                self.screen.blit(hint, (slot_rect.x + 20, slot_rect.centery + 10))
            else:
                # 有存档
                info = self.save_mgr.get_slot_info(i)
                text = font_med.render(f"存档 {i+1}", True, WHITE)
                self.screen.blit(text, (slot_rect.x + 20, slot_rect.y + 10))

                info_lines = [
                    f"难度: {info['difficulty']}  |  关卡: {info['level']}/5  |  存档点: {info['checkpoint']+1}/3",
                    f"击杀: {info['enemies_killed']}  |  游戏时间: {info['playtime']//60}分{info['playtime']%60}秒",
                    f"最后游玩: {info['last_played']}",
                ]
                for j, line in enumerate(info_lines):
                    t = font_small.render(line, True, LIGHT_GRAY)
                    self.screen.blit(t, (slot_rect.x + 20, slot_rect.y + 35 + j * 18))

                # 删除按钮
                del_rect = pygame.Rect(SCREEN_WIDTH - 170, slot_y + 30, 80, 40)
                pygame.draw.rect(self.screen, (60, 20, 20), del_rect, border_radius=5)
                pygame.draw.rect(self.screen, RED, del_rect, 2, border_radius=5)
                del_text = font_small.render("删除", True, WHITE)
                self.screen.blit(del_text, (del_rect.centerx - del_text.get_width()//2,
                                            del_rect.centery - del_text.get_height()//2))

        # 返回按钮
        self._draw_back_button()

    # ==================== 难度选择 ====================

    def _draw_difficulty_select(self):
        """绘制难度选择界面"""
        self.screen.fill((20, 30, 60))
        font_big = get_font(36, bold=True)
        font_med = get_font(22, bold=True)
        font_small = get_font(16)

        title = font_big.render(f"存档 {self.selected_slot + 1} - 选择难度", True, GOLD)
        self.screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 80))

        diffs = [("easy", (50, 200, 50)), ("normal", (255, 200, 0)), ("hard", (220, 50, 50))]
        for i, (diff_key, color) in enumerate(diffs):
            diff = DIFFICULTY[diff_key]
            dx = 200 + i * 220
            dy = 250
            drect = pygame.Rect(dx, dy, 200, 120)
            pygame.draw.rect(self.screen, (40, 50, 80), drect, border_radius=8)
            pygame.draw.rect(self.screen, color, drect, 3, border_radius=8)

            name = font_med.render(diff["name"], True, color)
            self.screen.blit(name, (drect.centerx - name.get_width()//2, drect.y + 10))

            desc_lines = [
                f"生命: {diff['player_hp']}",
                f"攻击: {diff['player_atk']}",
                f"冷却: {diff['melee_cd']:.1f}s",
                f"敌人: x{diff['enemy_hp_mul']:.1f}",
            ]
            for j, line in enumerate(desc_lines):
                t = font_small.render(line, True, LIGHT_GRAY)
                self.screen.blit(t, (drect.x + 20, drect.y + 35 + j * 18))

            desc = font_small.render(diff["desc"], True, WHITE)
            self.screen.blit(desc, (drect.centerx - desc.get_width()//2, drect.bottom + 5))

        self._draw_back_button()

    # ==================== 游戏规则 ====================

    def _draw_rules(self):
        """绘制游戏规则"""
        self.screen.fill((20, 30, 60))
        font_big = get_font(32, bold=True)
        font_med = get_font(18)
        font_small = get_font(16)

        title = font_big.render("游戏规则", True, GOLD)
        self.screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 30))

        rules = [
            "【操作说明】",
            f"  ←/→ 或 A/D  -  左右移动",
            f"  空格/W  -  跳跃(有二段跳技能时可连跳)",
            f"  J  -  近战攻击(有冷却时间)",
            f"  K  -  大招(需要攻击敌人蓄满后释放)",
            f"  L  -  使用道具",
            f"  ESC  -  暂停游戏",
            "",
            "【游戏目标】",
            f"  通过5个关卡，击败最终Boss Bowser即可通关。",
            f"  每关有3个存档点(2个中间+1个结尾)，触碰即可激活。",
            "",
            "【存档点增益】",
            f"  中间存档点: 随机3个小增益，三选一",
            f"    - 生命+20 / 攻击+5 / 大招+10 / 冷却-0.1s / 蓄能-1 / 距离+15",
            f"  结尾存档点: 三选一大增益(特殊技能/道具/属性大提升)",
            "",
            "【敌人系统】",
            f"  每关有2种普通怪 + 1种特殊怪(血量更高/远程攻击等)",
            f"  第5关有最终Boss Bowser，有3个战斗阶段",
            "",
            "【难度系统】",
            f"  简单: 生命150, 攻击20, 敌人较弱",
            f"  普通: 生命100, 攻击15, 标准难度",
            f"  困难: 生命70, 攻击12, 敌人强大",
            "",
            "【小提示】",
            f"  注意躲避远程敌人的投射物!",
            f"  合理使用存档点的增益可以大幅提升战斗力!",
            f"  有些隐藏成就需要特殊条件触发...",
        ]

        y = 80
        for line in rules:
            if line.startswith("【"):
                surf = font_med.render(line, True, GOLD)
            else:
                surf = font_small.render(line, True, WHITE)
            self.screen.blit(surf, (80, y))
            y += 24

        self._draw_back_button()

    # ==================== 成就 ====================

    def _draw_achievements(self):
        """绘制成就界面"""
        self.screen.fill((20, 30, 60))
        font_big = get_font(32, bold=True)
        font_med = get_font(20, bold=True)
        font_small = get_font(16)

        all_ach = self.ach_mgr.get_all_achievements()
        unlocked = sum(1 for a in all_ach if a["unlocked"])
        total = len(all_ach)

        title = font_big.render(f"成就  ({unlocked}/{total})", True, GOLD)
        self.screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 30))

        y = 85
        col_w = (SCREEN_WIDTH - 160) // 2
        for i, ach in enumerate(all_ach):
            col = i % 2
            row = i // 2
            ax = 80 + col * (col_w + 0)
            ay = y + row * 75

            # 成就框
            rect = pygame.Rect(ax, ay, col_w, 65)
            if ach["unlocked"]:
                pygame.draw.rect(self.screen, (30, 50, 30), rect, border_radius=6)
                pygame.draw.rect(self.screen, GOLD, rect, 2, border_radius=6)
                name_color = GOLD
                desc_color = WHITE
            else:
                pygame.draw.rect(self.screen, (30, 30, 30), rect, border_radius=6)
                pygame.draw.rect(self.screen, DARK_GRAY, rect, 2, border_radius=6)
                if ach.get("hidden") and not ach["unlocked"]:
                    name_color = GRAY
                    desc_color = DARK_GRAY
                else:
                    name_color = LIGHT_GRAY
                    desc_color = GRAY

            # 图标占位
            icon_rect = pygame.Rect(ax + 5, ay + 5, 55, 55)
            if ach["unlocked"]:
                pygame.draw.rect(self.screen, GOLD, icon_rect, border_radius=4)
                icon_text = font_big.render("?", True, BLACK)
                self.screen.blit(icon_text, (icon_rect.centerx - 8, icon_rect.centery - 16))
            else:
                pygame.draw.rect(self.screen, DARK_GRAY, icon_rect, border_radius=4)

            # 文字
            name_text = ach["name"] if not ach.get("hidden") or ach["unlocked"] else "???"
            name = font_med.render(name_text, True, name_color)
            self.screen.blit(name, (ax + 70, ay + 8))

            desc_text = ach["desc"] if not ach.get("hidden") or ach["unlocked"] else "隐藏成就 - 特殊条件触发"
            desc = font_small.render(desc_text, True, desc_color)
            self.screen.blit(desc, (ax + 70, ay + 32))

            if ach["unlocked"] and ach.get("unlock_time"):
                time_text = font_small.render(ach["unlock_time"], True, GREEN)
                self.screen.blit(time_text, (ax + col_w - time_text.get_width() - 10, ay + 8))

        self._draw_back_button()

    # ==================== 设置 ====================

    def _draw_settings(self):
        """绘制设置界面"""
        self.screen.fill((20, 30, 60))
        font_big = get_font(32, bold=True)
        font_med = get_font(22, bold=True)
        font_small = get_font(18)

        title = font_big.render("设置", True, GOLD)
        self.screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 30))

        # 音乐音量
        y = 200
        label = font_med.render("背景音乐音量:", True, WHITE)
        self.screen.blit(label, (100, y + 8))
        vol = self.settings_mgr.get_music_volume()
        bar_rect = pygame.Rect(350, y + 8, 150, 25)
        pygame.draw.rect(self.screen, (50, 50, 50), bar_rect)
        pygame.draw.rect(self.screen, GREEN, (350, y + 8, int(150 * vol / 100), 25))
        pygame.draw.rect(self.screen, WHITE, bar_rect, 2)
        vol_text = font_small.render(f"{vol}", True, WHITE)
        self.screen.blit(vol_text, (515, y + 8))
        # + - 按钮
        pygame.draw.rect(self.screen, (60, 60, 60), (500, y, 40, 40), border_radius=5)
        pygame.draw.rect(self.screen, WHITE, (500, y, 40, 40), 2, border_radius=5)
        self.screen.blit(font_med.render("+", True, WHITE), (513, y + 5))
        pygame.draw.rect(self.screen, (60, 60, 60), (560, y, 40, 40), border_radius=5)
        pygame.draw.rect(self.screen, WHITE, (560, y, 40, 40), 2, border_radius=5)
        self.screen.blit(font_med.render("-", True, WHITE), (575, y + 5))

        # 音效音量
        y = 270
        label = font_med.render("音效音量:", True, WHITE)
        self.screen.blit(label, (100, y + 8))
        vol = self.settings_mgr.get_sfx_volume()
        bar_rect = pygame.Rect(350, y + 8, 150, 25)
        pygame.draw.rect(self.screen, (50, 50, 50), bar_rect)
        pygame.draw.rect(self.screen, ORANGE, (350, y + 8, int(150 * vol / 100), 25))
        pygame.draw.rect(self.screen, WHITE, bar_rect, 2)
        vol_text = font_small.render(f"{vol}", True, WHITE)
        self.screen.blit(vol_text, (515, y + 8))
        pygame.draw.rect(self.screen, (60, 60, 60), (500, y, 40, 40), border_radius=5)
        pygame.draw.rect(self.screen, WHITE, (500, y, 40, 40), 2, border_radius=5)
        self.screen.blit(font_med.render("+", True, WHITE), (513, y + 5))
        pygame.draw.rect(self.screen, (60, 60, 60), (560, y, 40, 40), border_radius=5)
        pygame.draw.rect(self.screen, WHITE, (560, y, 40, 40), 2, border_radius=5)
        self.screen.blit(font_med.render("-", True, WHITE), (575, y + 5))

        # 屏幕大小
        y = 340
        label = font_med.render("屏幕大小:", True, WHITE)
        self.screen.blit(label, (100, y + 8))
        sizes = [(1024, 576, "1024x576"), (1280, 720, "1280x720"), (800, 450, "800x450")]
        current_size = self.settings_mgr.get_screen_size()
        for i, (w, h, label_text) in enumerate(sizes):
            sx = 400 + i * 130
            srect = pygame.Rect(sx, y, 120, 50)
            is_current = (w == current_size[0])
            color = GREEN if is_current else (60, 60, 60)
            pygame.draw.rect(self.screen, color, srect, border_radius=5)
            pygame.draw.rect(self.screen, WHITE, srect, 2, border_radius=5)
            t = font_small.render(label_text, True, WHITE)
            self.screen.blit(t, (srect.centerx - t.get_width()//2, srect.centery - t.get_height()//2))

        # 提示
        hint = font_small.render("(点击后改变窗口大小)", True, LIGHT_GRAY)
        self.screen.blit(hint, (400, y + 55))

        # 全屏
        y = 420
        label = font_med.render("全屏模式:", True, WHITE)
        self.screen.blit(label, (100, y + 8))
        fs_rect = pygame.Rect(400, y, 200, 40)
        is_fs = self.settings_mgr.get_fullscreen()
        pygame.draw.rect(self.screen, GREEN if is_fs else (60, 60, 60), fs_rect, border_radius=5)
        pygame.draw.rect(self.screen, WHITE, fs_rect, 2, border_radius=5)
        t = font_small.render("开启" if is_fs else "关闭", True, WHITE)
        self.screen.blit(t, (fs_rect.centerx - t.get_width()//2, fs_rect.centery - t.get_height()//2))

        # 控制设置按钮
        ctrl_rect = pygame.Rect(400, 480, 250, 40)
        pygame.draw.rect(self.screen, (60, 60, 100), ctrl_rect, border_radius=5)
        pygame.draw.rect(self.screen, WHITE, ctrl_rect, 2, border_radius=5)
        t = font_small.render("按键设置 →", True, WHITE)
        self.screen.blit(t, (ctrl_rect.centerx - t.get_width()//2, ctrl_rect.centery - t.get_height()//2))

        self._draw_back_button()

    def _draw_controls_settings(self):
        """绘制按键设置界面"""
        self.screen.fill((20, 30, 60))
        font_big = get_font(28, bold=True)
        font_med = get_font(20, bold=True)
        font_small = get_font(18)

        title = font_big.render("按键设置", True, GOLD)
        self.screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 30))

        title2 = font_small.render("(点击按键框后按任意键重新绑定)", True, LIGHT_GRAY)
        self.screen.blit(title2, ((SCREEN_WIDTH - title2.get_width()) // 2, 65))

        controls = self.settings_mgr.get_controls()
        labels = {
            "move_left": "向左移动", "move_right": "向右移动",
            "jump": "跳跃", "melee": "近战攻击",
            "ultimate": "大招", "use_item": "使用道具", "pause": "暂停"
        }

        y = 110
        for i, (action, key) in enumerate(controls.items()):
            item_y = y + i * 50
            # 标签
            label = font_med.render(labels.get(action, action), True, WHITE)
            self.screen.blit(label, (100, item_y + 5))

            # 按键框
            key_rect = pygame.Rect(550, item_y, 200, 40)
            if self.rebind_action == action:
                pygame.draw.rect(self.screen, GOLD, key_rect, border_radius=5)
                key_text = font_small.render("按任意键...", True, BLACK)
            else:
                pygame.draw.rect(self.screen, (40, 50, 80), key_rect, border_radius=5)
                pygame.draw.rect(self.screen, WHITE, key_rect, 2, border_radius=5)
                key_text = font_small.render(key.upper(), True, WHITE)
            self.screen.blit(key_text, (key_rect.centerx - key_text.get_width()//2,
                                        key_rect.centery - key_text.get_height()//2))

        self._draw_back_button()

    # ==================== 退出动画 ====================

    def _draw_exit(self):
        """绘制退出画面"""
        progress = min(1.0, self.exit_timer / self.exit_duration)
        # 先显示文字，然后逐渐变暗
        if progress < 0.4:
            alpha = int(255 * progress / 0.4)
        else:
            alpha = 255

        # 背景
        self.screen.fill((20, 30, 60))

        # 感谢文字
        font_big = get_font(48, bold=True)
        text = "感谢游玩！"
        text_surf = font_big.render(text, True, WHITE)
        text_surf.set_alpha(alpha)
        self.screen.blit(text_surf, ((SCREEN_WIDTH - text_surf.get_width()) // 2,
                                     (SCREEN_HEIGHT - text_surf.get_height()) // 2))

        # 淡出覆盖
        if progress > 0.3:
            fade_alpha = int(255 * (progress - 0.3) / 0.7)
            overlay = pygame.Surface(self.screen.get_size())
            overlay.fill(BLACK)
            overlay.set_alpha(fade_alpha)
            self.screen.blit(overlay, (0, 0))

    # ==================== 通知 ====================

    def _draw_notifications(self):
        """绘制通知(如成就解锁)"""
        font = get_font(18, bold=True)
        y_offset = 0
        for notif in self.notifications:
            alpha = min(1.0, notif["timer"] / 0.5) if notif["timer"] < 0.5 else 1.0
            text_surf = font.render(notif["text"], True, notif["color"])
            text_surf.set_alpha(int(255 * alpha))
            bg_rect = pygame.Rect(SCREEN_WIDTH - text_surf.get_width() - 40,
                                  SCREEN_HEIGHT - 130 - y_offset,  # 上移，避开右下角"玩家指南"按钮
                                  text_surf.get_width() + 30, 35)
            bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            bg_surf.fill((0, 0, 0, int(180 * alpha)))
            self.screen.blit(bg_surf, bg_rect)
            self.screen.blit(text_surf, (bg_rect.x + 15, bg_rect.y + 8))
            y_offset += 45

    # ==================== 辅助方法 ====================

    def _draw_back_button(self):
        """绘制返回按钮"""
        font = get_font(18, bold=True)
        rect = pygame.Rect(50, SCREEN_HEIGHT - 70, 120, 50)
        mx, my = pygame.mouse.get_pos()
        is_hover = rect.collidepoint(mx, my)
        color = GOLD if is_hover else (80, 60, 30)
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, WHITE, rect, 2, border_radius=8)
        text = font.render("← 返回", True, WHITE)
        self.screen.blit(text, (rect.centerx - text.get_width()//2,
                                rect.centery - text.get_height()//2))

    def _draw_delete_confirm(self):
        """绘制删除确认对话框"""
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        font_big = get_font(28, bold=True)
        font_med = get_font(20, bold=True)
        font_small = get_font(16)

        # 对话框
        dlg_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, 280, 400, 180)
        pygame.draw.rect(self.screen, (30, 40, 70), dlg_rect, border_radius=10)
        pygame.draw.rect(self.screen, RED, dlg_rect, 3, border_radius=10)

        text = font_big.render("确认删除？", True, RED)
        self.screen.blit(text, (dlg_rect.centerx - text.get_width()//2, dlg_rect.y + 20))

        desc = font_small.render(f"存档 {self.selected_slot + 1} 的所有进度将丢失", True, WHITE)
        self.screen.blit(desc, (dlg_rect.centerx - desc.get_width()//2, dlg_rect.y + 60))

        # 按钮
        yes_rect = pygame.Rect(SCREEN_WIDTH//2 - 120, 380, 100, 50)
        no_rect = pygame.Rect(SCREEN_WIDTH//2 + 20, 380, 100, 50)
        pygame.draw.rect(self.screen, (80, 20, 20), yes_rect, border_radius=5)
        pygame.draw.rect(self.screen, RED, yes_rect, 2, border_radius=5)
        pygame.draw.rect(self.screen, (20, 80, 20), no_rect, border_radius=5)
        pygame.draw.rect(self.screen, GREEN, no_rect, 2, border_radius=5)
        self.screen.blit(font_med.render("删除", True, WHITE),
                         (yes_rect.centerx - 30, yes_rect.centery - 12))
        self.screen.blit(font_med.render("取消", True, WHITE),
                         (no_rect.centerx - 30, no_rect.centery - 12))

    def _play_sfx(self, name):
        """播放音效"""
        try:
            from constants import SOUND_DIR
            import os
            path = os.path.join(SOUND_DIR, f"sfx_{name}.wav")
            if os.path.exists(path):
                vol = self.settings_mgr.get_sfx_volume() / 100.0
                sound = pygame.mixer.Sound(path)
                sound.set_volume(vol)
                sound.play()
        except Exception:
            pass
