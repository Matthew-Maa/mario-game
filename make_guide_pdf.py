# -*- coding: utf-8 -*-
"""生成《玩家指南.pdf》 - 超级马里奥冒险"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

OUT = r"D:\Kimi 工作区\mario_game\玩家指南.pdf"

# 注册中文字体
regular = os.environ.get('DAIMON_CJK_FONT_REGULAR')
bold = os.environ.get('DAIMON_CJK_FONT_BOLD')
if not regular or not bold:
    raise RuntimeError('CJK 字体不可用')
pdfmetrics.registerFont(TTFont('CJK', regular))
pdfmetrics.registerFont(TTFont('CJK-Bold', bold))
pdfmetrics.registerFontFamily('CJK', normal='CJK', bold='CJK-Bold',
                              italic='CJK', boldItalic='CJK-Bold')

NAVY = HexColor('#1a3a5c')
DARK = HexColor('#333333')
GRAY = HexColor('#666666')
GOLD = HexColor('#8a6d1a')

def st(name, **kw):
    base = dict(fontName='CJK', fontSize=10.5, leading=17, textColor=DARK)
    base.update(kw)
    return ParagraphStyle(name, **base)

S = {
    'title':   st('t',  fontName='CJK-Bold', fontSize=26, leading=34, textColor=NAVY, alignment=1),
    'subtitle':st('st', fontSize=13, leading=20, textColor=GRAY, alignment=1),
    'h1':      st('h1', fontName='CJK-Bold', fontSize=15, leading=22, textColor=NAVY,
                  spaceBefore=16, spaceAfter=6),
    'h2':      st('h2', fontName='CJK-Bold', fontSize=12, leading=18, textColor=NAVY,
                  spaceBefore=10, spaceAfter=4),
    'body':    st('b'),
    'bullet':  st('bu', leftIndent=14, bulletIndent=4),
    'note':    st('n', fontSize=9.5, leading=15, textColor=GRAY),
}

def header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFont('CJK', 9)
    canvas.setFillColor(GRAY)
    canvas.drawCentredString(w / 2, h - 1.4 * cm, "超级马里奥冒险 · 玩家指南")
    canvas.setStrokeColor(HexColor('#cccccc'))
    canvas.setLineWidth(0.5)
    canvas.line(2.5 * cm, h - 1.6 * cm, w - 2.5 * cm, h - 1.6 * cm)
    canvas.drawCentredString(w / 2, 1.3 * cm, f"第 {doc.page} 页")
    canvas.restoreState()

def first_page(canvas, doc):
    pass

story = []

# ===== 封面区 =====
story.append(Spacer(1, 3.2 * cm))
story.append(Paragraph("超级马里奥冒险", S['title']))
story.append(Spacer(1, 0.3 * cm))
story.append(Paragraph("玩 家 指 南", S['title']))
story.append(Spacer(1, 0.8 * cm))
story.append(Paragraph("2D 横版动作冒险 · 五关征程 · 击败 Bowser 拯救王国", S['subtitle']))
story.append(Spacer(1, 0.3 * cm))
story.append(Paragraph("版本 1.0 · 2026 年 9 月", S['subtitle']))
story.append(Spacer(1, 1.6 * cm))

# ===== 一、快速上手 =====
story.append(Paragraph("一、快速上手", S['h1']))
story.append(Paragraph(
    "《超级马里奥冒险》是一款 2D 横版动作游戏。你将穿越草原、洞窟、幽灵屋、熔岩城堡，"
    "最终攻入 Bowser 的城堡。每关从左向右推进，触碰 3 个存档点、击败沿途敌人、"
    "到达最右侧的终点门即算过关。生命归零则游戏结束，可从最近的存档点继续。", S['body']))
story.append(Spacer(1, 6))
story.append(Paragraph("流程一览", S['h2']))
for txt in [
    "<bullet>1.</bullet> 主菜单点击「开始游戏」，选择存档槽（共 3 个）与难度（简单 / 普通 / 困难）。",
    "<bullet>2.</bullet> 进入关卡后向右推进，跳跃躲避缺口，攻击或踩头消灭敌人。",
    "<bullet>3.</bullet> 经过金色旗杆存档点会触发增益三选一，选完继续冒险。",
    "<bullet>4.</bullet> 抵达关卡最右侧的终点门过关；第 5 关击败 Boss Bowser 即通关。",
]:
    story.append(Paragraph(txt, S['bullet']))

# ===== 二、操作说明 =====
story.append(Paragraph("二、操作说明", S['h1']))
story.append(Paragraph("默认按键如下，可在「设置 → 按键设置」中自由改绑：", S['body']))
story.append(Spacer(1, 4))

ctrl_data = [
    [Paragraph("功能", S['h2']), Paragraph("默认按键", S['h2']), Paragraph("说明", S['h2'])],
    ["向左 / 向右移动", "← / → 方向键", "地面与空中均可控制方向"],
    ["跳跃", "空格", "支持跳跃缓冲与土狼时间，手感宽松；获得二段跳后可连跳两次"],
    ["近战攻击", "J", "朝面向方向挥击，命中敌人积攒大招能量"],
    ["释放大招", "K", "能量蓄满后释放，对大范围内敌人造成高额伤害并短暂无敌"],
    ["使用道具", "L", "使用已获得的道具（无敌星星 / 速度药水）"],
    ["暂停游戏", "ESC", "打开暂停菜单：继续 / 保存并退出 / 设置 / 返回主菜单"],
]
ctrl_data = [[Paragraph(str(c), S['body']) if i > 0 else c for c in row] for i, row in enumerate(ctrl_data)]
t = Table(ctrl_data, colWidths=[3.2 * cm, 3.2 * cm, 8.6 * cm])
t.setStyle(TableStyle([
    ('FONTNAME', (0, 0), (-1, -1), 'CJK'),
    ('FONTNAME', (0, 0), (-1, 0), 'CJK-Bold'),
    ('LINEABOVE', (0, 0), (-1, 0), 1.2, NAVY),
    ('LINEBELOW', (0, 0), (-1, 0), 0.6, NAVY),
    ('LINEBELOW', (0, -1), (-1, -1), 1.2, NAVY),
    ('TOPPADDING', (0, 0), (-1, -1), 5),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
]))
story.append(t)

# ===== 三、战斗与判定 =====
story.append(Paragraph("三、战斗与判定规则", S['h1']))
for txt in [
    "<bullet>·</bullet> <b>踩头：</b>从上方落到敌人头上可造成大量伤害并自动弹起；弹起瞬间有短暂无敌。",
    "<bullet>·</bullet> <b>接触伤害：</b>从侧面碰到敌人会受到伤害并被击退，受伤后有 1 秒无敌时间。",
    "<bullet>·</bullet> <b>近战：</b>有冷却时间（HUD 有冷却条），命中回复大招能量；可击毁敌方投射物。",
    "<bullet>·</bullet> <b>大招：</b>能量蓄满后按 K 释放，以自身为中心的大范围高额伤害，并清除附近投射物。",
    "<bullet>·</bullet> <b>坠落：</b>掉入地面缺口会判定坠落死亡，请留意随机出现的缺口并提前起跳。",
]:
    story.append(Paragraph(txt, S['bullet']))
story.append(Spacer(1, 4))
story.append(Paragraph(
    "提示：护盾技能每 10 秒自动获得一次免伤机会；无敌星星提供 5 秒完全无敌；"
    "速度药水让移速翻倍 10 秒。三者是挑战高难度关卡的利器。", S['body']))

# ===== 四、存档点与增益 =====
story.append(Paragraph("四、存档点与增益系统", S['h1']))
story.append(Paragraph(
    "每关有 3 个存档点（前 2 个为中间存档点，最后 1 个紧邻终点）。经过存档点即自动保存进度，"
    "下次可从该位置继续。每次激活存档点都会触发「增益三选一」：", S['body']))
story.append(Spacer(1, 4))
story.append(Paragraph("小增益（中间存档点，属性强化）", S['h2']))
small = [["生命强化 最大生命 +20", "力量强化 攻击 +5", "大招强化 大招伤害 +10"],
         ["敏捷强化 近战冷却 -0.1 秒", "蓄能加速 大招需求 -1", "范围扩大 攻击距离 +15"]]
t = Table(small, colWidths=[5 * cm, 5 * cm, 5 * cm])
t.setStyle(TableStyle([
    ('FONTNAME', (0, 0), (-1, -1), 'CJK'),
    ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('GRID', (0, 0), (-1, -1), 0.4, HexColor('#bbbbbb')),
    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f0f4f8')),
    ('TOPPADDING', (0, 0), (-1, -1), 5),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
]))
story.append(t)
story.append(Spacer(1, 6))
story.append(Paragraph("大增益（结尾存档点，技能 / 道具 / 属性）", S['h2']))
big = [["二段跳 可二次跳跃", "冲刺攻击 近战突进且伤害 +50%", "护盾 每 10 秒一次免伤"],
       ["无敌星星 获得道具：5 秒无敌", "速度药水 获得道具：10 秒提速", "属性大提升 生命+50 攻击+10 大招+15"],
       ["吸血之力 近战回血 20%", "暴击精通 30% 概率双倍伤害", ""]]
t = Table(big, colWidths=[5 * cm, 5 * cm, 5 * cm])
t.setStyle(TableStyle([
    ('FONTNAME', (0, 0), (-1, -1), 'CJK'),
    ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('GRID', (0, 0), (-1, -1), 0.4, HexColor('#bbbbbb')),
    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f8f4e8')),
    ('TOPPADDING', (0, 0), (-1, -1), 5),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
]))
story.append(t)

story.append(PageBreak())

# ===== 五、敌人图鉴 =====
story.append(Paragraph("五、敌人图鉴", S['h1']))
story.append(Paragraph("每关由 2 种普通敌人 + 1 种特殊敌人组成；第 5 关为最终 Boss 战。", S['body']))
story.append(Spacer(1, 4))

def enemy_table(title, rows):
    story.append(Paragraph(title, S['h2']))
    data = [[Paragraph("敌人", S['h2']), Paragraph("特点与应对", S['h2'])]]
    for name, desc in rows:
        data.append([Paragraph(name, S['body']), Paragraph(desc, S['body'])])
    t = Table(data, colWidths=[3 * cm, 12 * cm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'CJK'),
        ('LINEABOVE', (0, 0), (-1, 0), 1, NAVY),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, NAVY),
        ('LINEBELOW', (0, -1), (-1, -1), 1, NAVY),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 4))

enemy_table("第 1 关 · 草原冒险", [
    ("栗子仔 / 乌龟", "基础近战敌人，走走停停；踩头或近战均可轻松解决。"),
    ("炮弹刺客", "定时发射追踪弹；近战可以打落炮弹，贴近后快速输出。"),
])
enemy_table("第 2 关 · 地底洞窟", [
    ("刺球 / 铁甲虫", "移速较快；铁甲虫血厚攻低，适合用大招速杀。"),
    ("云龟", "悬浮在玩家头顶持续投掷刺球；跳跃近战或等它降低到射程内攻击。"),
])
enemy_table("第 3 关 · 幽灵之屋", [
    ("枯骨", "被击败后 3 秒会原地半血复活，注意补刀节奏。"),
    ("幽灵", "只在玩家背对它时移动；面对它即可使其静止，再找机会绕后攻击。"),
    ("巨石怪", "悬停在通道上方，玩家经过时砸下；等它落地后再通过。"),
])
enemy_table("第 4 关 · 熔岩城堡", [
    ("锤子龟 / 火焰龟", "中距离投掷武器；利用跳跃接近或大招清场。"),
    ("魔法龟", "会瞬移拉开距离并发射高速魔法弹；追着打，别让它拉开射程。"),
])
enemy_table("第 5 关 · Bowser 的城堡", [
    ("火焰花 / 枯骨精英", "守门敌人；火焰花固定不动但火力密集，优先解决。"),
    ("Bowser（Boss）", "三阶段：血量低于 66% 加速、低于 33% 散射三发。保持移动，"
     "在其攻击间隙近战输出，大招留给第三阶段。"),
])

# ===== 六、难度与成就 =====
story.append(Paragraph("六、难度与成就", S['h1']))
story.append(Paragraph("难度对比", S['h2']))
diff = [[Paragraph(x, S['h2']) for x in ["难度", "生命", "攻击", "近战冷却", "敌人强度"]],
        ["简单", "150", "20", "0.8 秒", "x0.7（适合新手）"],
        ["普通", "100", "15", "1.0 秒", "x1.0（标准体验）"],
        ["困难", "70", "12", "1.2 秒", "x1.3（硬核挑战）"]]
t = Table(diff, colWidths=[2.4 * cm, 2 * cm, 2 * cm, 3 * cm, 6 * cm])
t.setStyle(TableStyle([
    ('FONTNAME', (0, 0), (-1, -1), 'CJK'),
    ('LINEABOVE', (0, 0), (-1, 0), 1, NAVY),
    ('LINEBELOW', (0, 0), (-1, 0), 0.5, NAVY),
    ('LINEBELOW', (0, -1), (-1, -1), 1, NAVY),
    ('TOPPADDING', (0, 0), (-1, -1), 5),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
]))
story.append(t)
story.append(Spacer(1, 8))
story.append(Paragraph("成就一览（主菜单 → 成就）", S['h2']))
for txt in [
    "初次冒险：完成第 1 关；　勇者之路：通关全部 5 关；　无伤通关：不受任何伤害完成一关。",
    "大招大师：累计使用大招 50 次；　收藏家：收集所有小增益；　速通达人：30 分钟内通关。",
    "百人斩：累计击败 100 个敌人；　难度大师：困难难度通关。",
    "隐藏彩蛋：哲学家（一关中静止 60 秒）、和平主义者（不攻击任何敌人完成一关）。",
]:
    story.append(Paragraph(txt, S['bullet']))

story.append(Spacer(1, 10))
story.append(Paragraph(
    "祝你冒险顺利！如遇问题，可在主界面右下角点击「玩家指南」随时查看本文档。", S['note']))

doc = SimpleDocTemplate(OUT, pagesize=A4,
                        topMargin=2.2 * cm, bottomMargin=2 * cm,
                        leftMargin=2.5 * cm, rightMargin=2.5 * cm,
                        title="超级马里奥冒险 · 玩家指南",
                        author="Kimi")
doc.build(story, onFirstPage=first_page, onLaterPages=header_footer)
print("OK:", OUT)
