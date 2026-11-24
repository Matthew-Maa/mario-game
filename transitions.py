# -*- coding: utf-8 -*-
"""
transitions.py - 页面转场效果
====================================
实现类似PPT中的"平滑"切换效果。
使用透明度渐变实现页面间的平滑过渡。
"""

import pygame


class Transition:
    """转场效果管理器"""

    def __init__(self, duration=0.5):
        """初始化转场
        Args:
            duration: 转场持续时间(秒)
        """
        self.duration = duration
        self.timer = 0
        self.active = False
        self.direction = "out"  # "out"=淡出, "in"=淡入
        self.callback = None  # 转场完成后的回调
        self.overlay_color = (0, 0, 0)

    def start(self, direction="out", callback=None, color=(0, 0, 0)):
        """开始转场
        Args:
            direction: "out"(淡出变黑) 或 "in"(从黑淡入)
            callback: 转场到中点时的回调(用于切换场景)
            color: 遮罩颜色
        """
        self.active = True
        self.direction = direction
        self.callback = callback
        self.overlay_color = color
        self.timer = 0

    def update(self, dt, screen):
        """更新转场并绘制遮罩
        Returns: True=转场进行中, False=转场结束
        """
        if not self.active:
            return False

        self.timer += dt
        progress = self.timer / self.duration

        if progress >= 1.0:
            self.active = False
            if self.callback and self.direction == "out":
                self.callback()
                self.start("in", color=self.overlay_color)
            return False

        # 计算透明度
        if self.direction == "out":
            alpha = int(255 * progress)  # 0->255
        else:
            alpha = int(255 * (1 - progress))  # 255->0

        # 绘制遮罩
        overlay = pygame.Surface(screen.get_size())
        overlay.fill(self.overlay_color)
        overlay.set_alpha(alpha)
        screen.blit(overlay, (0, 0))

        return True

    def is_active(self):
        """转场是否进行中"""
        return self.active


class SmoothTransition:
    """平滑切换(带缩放效果)"""

    def __init__(self, duration=0.2):
        self.duration = duration
        self.timer = 0
        self.active = False
        self.phase = "out"  # "out" 或 "in"
        self.callback = None

    def start(self, callback=None):
        """开始平滑切换"""
        self.active = True
        self.phase = "out"
        self.timer = 0
        self.callback = callback

    def update(self, dt, screen):
        """更新并绘制"""
        if not self.active:
            return False

        self.timer += dt
        progress = min(1.0, self.timer / self.duration)

        if self.phase == "out":
            # 淡出
            alpha = int(255 * progress)
            if progress >= 1.0:
                if self.callback:
                    self.callback()
                self.phase = "in"
                self.timer = 0
                alpha = 255
        else:
            # 淡入
            alpha = int(255 * (1 - progress))
            if progress >= 1.0:
                self.active = False
                alpha = 0

        overlay = pygame.Surface(screen.get_size())
        overlay.fill((0, 0, 0))
        overlay.set_alpha(alpha)
        screen.blit(overlay, (0, 0))
        return True

    def is_active(self):
        return self.active
