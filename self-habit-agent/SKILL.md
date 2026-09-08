---
name: self-habit-agent
display_name: 习惯养成与连击
description: 习惯叠加 / streak 引擎。把新行为「接」在既有锚点行为之后，自动记录每日打卡、算连击、检测断签、生成养成进度报告，让「日日做的小事」靠机制而非意志长成自动化。基于习惯叠加(Clear)/习惯回路(Duhigg)/养成天数(Lally)/微习惯(Guise)/执行意图(Gollwitzer)。确定性代码记录，留 jsonl+markdown 实物证据。
version: 2.0.0
license: MIT
---

# self-habit-agent · 习惯叠加 / streak 引擎

把新行为「焊」在已经自动化的旧行为之后，养成就不丢。本 agent 不喊口号、不灌鸡汤，而是把 **habit stacking** 落成可重跑的数据与算法：定义锚点→新行为→提示线索，每日打卡，自动算连击、断签、养成进度，并对长期未养成发出警报。

## 主动触发（什么情形下本 agent 应主动启动）

- 用户说「我想养成……习惯」「我要坚持……」「又没坚持住」「坚持了 X 天」→ 主动 `define` / `checkin` / `report`。
- 每日固定时段（如睡前复盘）→ 主动跑 `report` 把进度推给用户。
- 检测到用户连续多日未打卡 → 主动 `lapse` 并给微习惯重启建议。
- 与 self-discipline（承诺装置）、self-focus（深度专注）、self-reflect（模式洞察）配合，不抢彼此职责。

## 真引擎（scripts/habit.py）

| 子命令 | 作用 | 实物证据 |
|---|---|---|
| `define` | 定义习惯：锚点行为 + 新行为 + 提示线索 → 输出叠加公式 | 追加 `habit-log.jsonl` |
| `checkin` | 每日打卡（按 `--name`/`--id`；`--date` 回溯；同日去重） | 追加 `habit-log.jsonl` |
| `streak` | 连击统计：当前连击 / 最长连击 | 屏幕输出 |
| `lapse` | 中断检测：断签天数、是否触发长期警报 | 屏幕输出 |
| `report` | 养成进度报告：逐习惯进度%、最稳/最易断、下一步建议 | `habit-report.md` |

退出码约定（对齐 self 系列）：`0` 正常 / `1` 需关注（中断或停滞）/ `4` 长期未养成警报（连续断签 ≥7 天）。

## 用法示例

```bash
# 1) 定义习惯（锚点 + 新行为 + 提示线索）
python scripts/habit.py define \
  --name 晨读 --anchor "起床刷牙" \
  --behavior "读2页书" --cue "把书摊开在书桌上"

# 2) 每日打卡（可回溯 --date，同日自动去重）
python scripts/habit.py checkin --name 晨读 --date 2026-03-10

# 3) 连击统计
python scripts/habit.py streak

# 4) 中断检测（断签天数与警报）
python scripts/habit.py lapse

# 5) 周期报告（产出 habit-report.md）
python scripts/habit.py report
```

## 理论根基（详见 references/）

| 理论 | 来源 | 在本引擎的落点 |
|---|---|---|
| 习惯叠加 habit stacking | James Clear《Atomic Habits》 | `define` 强制锚点+新行为+线索三件套 |
| 习惯回路 线索-渴求-反应-奖赏 | Duhigg | `cue` 把线索外显化，降低对自觉依赖 |
| 养成天数 中位 66 / 区间 18–254 | Lally et al. 2009 | 默认目标 66 天，进度条标注区间，防焦虑 |
| 微习惯 | Guise | 断签≥7 天给「降到 1 分钟版本」重启建议 |
| 执行意图 implementation intentions | Gollwitzer 1999 | 叠加公式即一句执行意图 |

## 红线与诚实边界

- 引擎只记录「你打了卡」，不验证「你真的做了」。需客观验证请接入外部数据，本 agent 不伪造。
- 养成天数 66 是中位数不是 KPI；进度到 100% 仅代表达到中位养成窗口。
- 习惯叠加对「情境稳定」的人最有效；生活高度不规律者优先选更稳定的锚点。
- 本 agent 不替代医疗/心理干预；成瘾、重度拖延等应寻求专业帮助。

## 与同系列分工

- **self-discipline（#9）**：管「这条承诺算数不算数」（期限/后果/监督人），偏单次大额约束。
- **self-habit（本包 #10）**：管「日日做的小事」，偏长线自动化，无惩罚只有连击与进度。
- **self-focus（#11）**：管「做的时候不分心」。
- **self-reflect（#8）**：定期把习惯数据升维成自我洞察。

## 文件结构

```
self-habit-agent/
├── SKILL.md                      # 本文件
├── scripts/habit.py              # 真引擎（5 子命令）
├── resources/habit-prompts.json  # 锚点池/线索池/微习惯降级/version
├── references/habit-theory.md    # 理论根基长文
├── references/habit-method.md    # 实操方法长文
├── FAQ.md
├── README.md
├── SELF_EVAL.md
└── CHANGELOG.md
```
