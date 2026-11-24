# 超级马里奥冒险（Mario Adventure）

用 Python + pygame 写的 2D 横版动作游戏。5 个关卡、10 个成就、存档点机制。
所有美术、音效、背景音乐都由 `asset_generator.py` 用代码生成，没有一张外部图片。

## 怎么跑

需要 Python 3.10 以上。

```bash
pip install pygame-ce numpy
python main.py
```

Windows 上也可以直接双击 `run.bat`（会自动查找 Python、缺依赖时自动装）。

## 玩法

5 个关卡，从左往右推进：

| 关 | 主题 |
|---|---|
| 1 | 草原冒险 |
| 2 | 地底洞窟 |
| 3 | 幽灵之屋 |
| 4 | 熔岩城堡 |
| 5 | Bowser 城堡 |

每关沿途有存档点，碰到就记录进度；走到最右侧的终点门过关。生命归零回到最近存档点。

操作（可在设置里改键）：

| 键 | 动作 |
|---|---|
| A / D | 左右移动 |
| W | 跳跃 |
| J | 近战 |
| K | 大招（攒满能量后） |
| L | 使用道具 |
| Esc | 暂停 |

10 个成就，其中有一个是隐藏的。

## 关于素材

`assets/` 下的精灵图、音效、背景音乐**全部是程序化生成的**，由 `asset_generator.py` 完成：
图片用 pygame 绘图，音频用 numpy 合成正弦波（`generate_tone`）。

仓库里**没有包含背景音乐**——7 个未压缩 WAV 加起来 31MB，对仓库来说太重。
需要音乐就跑一次：

```bash
python asset_generator.py
```

它会重新生成 `assets/` 下的全部图片、音效与音乐。**缺音乐不影响游戏运行**，
只是关卡里没有背景音乐（代码里有 `os.path.exists` 判断，找不到就跳过）。

如果你只想补音乐、不想覆盖已经画好的图，可以先备份 `assets/images/` 再运行。

## 目录结构

```
mario_game/
├── main.py                 入口
├── game.py                 主循环、渲染、粒子、音乐/音效调度
├── menu.py                 菜单、选关、成就、设置
├── player.py               玩家角色与技能
├── enemy.py                敌人与投射物
├── constants.py            关卡参数、敌人属性、成就定义
├── level_data.py           关卡地形生成
├── transitions.py          场景切换
├── save_manager.py         存档读写
├── settings_manager.py     设置读写
├── achievement_manager.py  成就判定
├── asset_generator.py      资产生成器（图片 + 音效 + 音乐）
├── make_guide_pdf.py       生成玩家指南 PDF
├── assets/
│   ├── images/             精灵图（59 个 PNG，脚本生成）
│   ├── sounds/             音效（10 个 WAV，脚本合成）
│   └── music/              背景音乐（空，跑 asset_generator.py 生成）
├── 玩家指南.pdf
└── 维护指南.md
```

存档写在 `saves/` 下（`save_0.json`、`achievements.json`、`settings.json`），
首次运行自动创建，该目录不进版本库。

## 打包成 exe

```bash
build.bat
```

用 PyInstaller 打成 `dist/MarioAdventure/`（onedir 模式），整个文件夹拷给别人就能双击运行，
对方不需要装 Python。

## 许可

个人学习作品。代码可供参考学习；如需转载、二次分发或商用，请先联系作者。
