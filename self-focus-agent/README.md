# self-focus-agent · 深度工作 / 防干扰引擎

> 进入并守住心流：规划专注块、记录实际专注与打断来源、量化专注力与切换税，看清「什么最常打断我」。

- 版本：2.0.0
- 英文名 / name 字段：`self-focus-agent`
- 定位：self 系列第 11 条，管「当下这一块」的专注与防干扰
- 理论：Newport 深度工作 / Leroy 注意力残留 / Csikszentmihalyi 心流 / Rubinstein 切换成本 / Gloria Mark 中断恢复 / Cirillo 番茄钟 / Zeigarnik 效应

## 文件结构

```
self-focus-agent/
├── SKILL.md
├── scripts/focus.py                 # 真引擎
├── resources/focus-baselines.json  # 阈值与干扰来源词典（含 version）
├── references/focus-theory.md       # 理论根基（8 条，含出处与争议标注）
├── references/focus-method.md       # 防干扰方法论
├── FAQ.md
├── README.md
├── SELF_EVAL.md
└── CHANGELOG.md
```

## 快速开始

```bash
# 规划一个 90 分钟深度块
python scripts/focus.py plan --theme "写季度复盘" --planned-minutes 90

# 结束后回填实际专注与打断
python scripts/focus.py log --actual-minutes 85 --interruptions 1 --sources 微信 --plan-id p1

# 每次被打断记一笔（来源自动归一）
python scripts/focus.py interrupt --source "刷抖音" --block-id b1

# 看这次专注的度量（打断过多→退出1）
python scripts/focus.py measure

# 看趋势与「干扰来源 Top」（长期不足→退出4）
python scripts/focus.py report
```

## 子命令一览

| 命令 | 作用 | 关键产物 |
|---|---|---|
| `plan` | 规划专注块 | `focus-log.jsonl` 写入 plan 事件 |
| `log` | 记录实际专注（时长/打断/来源） | `focus-log.jsonl` 写入 block 事件 |
| `interrupt` | 记录单次干扰 | `focus-log.jsonl` 写入 interrupt 事件 |
| `measure` | 度量时长与打断频次 | `focus-measure.md`（退出 1 若有预警） |
| `report` | 趋势 + 干扰来源 Top + 长期评估 | `focus-report.md`（退出 1/4） |

## 退出码

`0` 正常 · `1` 需关注（打断过多）· `4` 长期警报（日均专注不足）

## 实物证据（4.8 基准）

- `focus-log.jsonl`：纯数据事件流，可重跑。
- `focus-measure.md` / `focus-report.md`：可复核的 markdown 产物。

详见 `SKILL.md` 与 `references/` 两篇长文。
