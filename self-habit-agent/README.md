# self-habit-agent 使用导航

> 习惯叠加 / streak 引擎。把新行为接在旧锚点之后，养成就不丢。

- 版本：2.0.0
- 英文名 / name 字段：`self-habit-agent`
- 真引擎：`scripts/habit.py`（5 子命令）
- 实物证据：`habit-log.jsonl` + `habit-report.md`

## 快速开始

```bash
# 定义习惯
python scripts/habit.py define --name 晨读 \
  --anchor "起床刷牙" --behavior "读2页书" --cue "把书摊开在书桌上"

# 每日打卡
python scripts/habit.py checkin --name 晨读 --date 2026-03-10

# 连击 / 中断 / 报告
python scripts/habit.py streak
python scripts/habit.py lapse
python scripts/habit.py report
```

## 子命令一览

| 命令 | 作用 | 退出码 |
|---|---|---|
| `define` | 定义习惯（锚点+新行为+线索） | 0 / 2(缺 name) |
| `checkin` | 每日打卡（去重） | 0 / 2(无此习惯) |
| `streak` | 当前/最长连击 | 0 / 1(有中断) |
| `lapse` | 断签天数与警报 | 0 / 1(中断) / 4(长期未养成) |
| `report` | 养成进度报告（写 md） | 0 / 1 / 4 |

## 文件结构

```
self-habit-agent/
├── SKILL.md
├── scripts/habit.py
├── resources/habit-prompts.json
├── references/habit-theory.md
├── references/habit-method.md
├── FAQ.md
├── README.md
├── SELF_EVAL.md
└── CHANGELOG.md
```

## 关联阅读

- `references/habit-theory.md`：习惯叠加的理论根基（Clear/Duhigg/Lally/Guise/Gollwitzer）
- `references/habit-method.md`：四步法、连击规则、主动触发、与同系列分工
- 同系列：`self-discipline`(承诺) · `self-focus`(专注) · `self-reflect`(洞察)
