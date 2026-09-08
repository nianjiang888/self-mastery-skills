---
name: self-focus-agent
display_name: 深度工作与防干扰
description: 深度工作/防干扰引擎。规划专注块、记录实际专注与打断来源、量化专注力与切换税，看清「什么最常打断我」，并在干扰过多或长期专注严重不足时主动报警（理论：Newport深度工作/Leroy注意力残留/Csikszentmihalyi心流/Rubinstein切换成本/Gloria Mark中断恢复/Cirillo番茄钟/Zeigarnik效应）。配套确定性代码与退出码 0/1/4，不靠模型自觉。
version: 2.0.0
license: MIT
---

# self-focus-agent · 深度工作 / 防干扰引擎

帮用户进入并守住心流：规划专注块、记录实际专注与干扰、量化专注力与打断频次，看清「什么最常打断我」，并在干扰过多或长期专注严重不足时主动报警。

## 主动触发（何时自己启动，而非等用户问）

- 用户说「帮我专注写 X」「给我定个 90 分钟深度块」「今天总被打断」→ 主动 `plan` 规划并提示 `log` 回填。
- 用户抱怨「又分心了」「效率好低」→ 主动建议 `report` 看「干扰来源 Top」，把焦虑变成可消除清单。
- 用户刚结束一段工作 → 主动提醒 `log` 记录实际时长与打断，避免「凭感觉复盘」。
- 周期性（如每日定时）：主动跑 `report`，非 0 退出码即提示用户「本周专注偏低/打断偏多」。

## 理论根基（每条均有可核验出处，争议处诚实标注）

| 理论 | 提出者 / 年份 | 对本引擎的落点 |
|---|---|---|
| 深度工作 vs 浮浅工作；高质量产出=时间×专注度 | Cal Newport, 2016 | `plan` 排深度块；`report` 看日均专注区间 |
| 心流通道（挑战-技能平衡）；四阶段序列 | Csikszentmihalyi, 1975/1990 | 计划时长过高→焦虑放弃、过低→无聊；用时长不足预警反向校准 |
| 注意力残留（未完成任务切换损耗贯穿全程） | Sophie Leroy, 2009 | `interrupt`+`report` 可视化来源；建议「复工便签」收尾 |
| 任务切换成本（单切换可达 50% 额外耗时） | Rubinstein, Meyer & Evans, 2001 | 退出码 1/4 倒逼减少切换 |
| 中断后恢复约 23 分 15 秒（中位数） | Gloria Mark, 2008 等 | 保护「不被打断的时间」比总时长更关键 |
| 番茄工作法（25 分钟不可分割） | Francesco Cirillo, 1980s–1992 | `plan --planned-minutes` 不锁死 25，尊重个体节奏 |
| 未完成任务记忆优势（开放循环占带宽） | Zeigarnik, 1927 | 把「干扰来源 Top」当待办逐个消除 |
| 多项目切换超线性损耗（启发式） | Weinberg, 1992 | 一次只排一个深度块、批量浅工作 |

**诚实标注：** ① 深度工作有「特权」属性，非所有人都能抽身数小时；② 番茄钟对长程创造任务可能过短；③ 网络流传的「残留降低 17–25%」「注意力仅 8 秒」等精确百分比多无可靠出处，本引擎不引用；④ 所有阈值是启发式基线，非医学标准。详见 `references/focus-theory.md`。

## 与系列内其他包的分工

- **self-focus（本包）**：管「当下这一块」——进入并守住专注、量化打断。
- **self-reflect (#8)**：管「事后回看」——跨时间模式与盲点。focus 记实时，reflect 看长线。
- **self-discipline (#9) / self-habit (#10)**：管「承诺与习惯」，与专注块互补但不重叠。
- **self-protect (#7)**：管「动手前的边界」，与专注无冲突。

## 命令（确定性代码闸门，非清单式空壳）

```bash
# 1) 规划一个专注块（主题 / 计划时长）
python scripts/focus.py plan --theme "写季度复盘" --planned-minutes 90

# 2) 记录一次专注块实际（实际时长 / 打断次数 / 来源）
python scripts/focus.py log --actual-minutes 85 --interruptions 1 --sources 微信 --plan-id p1

# 3) 记录单次干扰（来源会被自动归一：刷抖音→自己刷手机）
python scripts/focus.py interrupt --source "刷抖音" --block-id b1

# 4) 度量：实际专注时长 + 打断频次 + 来源分布（打断过多/时长不足 → 退出 1）
python scripts/focus.py measure

# 5) 报告：每日趋势 + 干扰来源 Top + 长期专注评估（长期不足 → 退出 4）
python scripts/focus.py report
```

## 退出码

- `0` 正常
- `1` 需关注：单块打断过多，或窗口内打断/块均值 ≥ 阈值
- `4` 长期警报：窗口内（默认 7 天）≥3 个活跃天且日均专注 < 基线（默认 90 分钟）

## 实物证据（4.8 基准：留可重跑文件）

- `focus-log.jsonl`：每次 `plan`/`log`/`interrupt` 一行纯数据，可任意时刻重跑分析。
- `focus-measure.md` / `focus-report.md`：各命令生成的产物，均为可复核的 markdown。

## 文件结构

```
self-focus-agent/
├── SKILL.md
├── scripts/focus.py              # 真引擎：plan/log/interrupt/measure/report
├── resources/focus-baselines.json # 阈值与干扰来源词典（含 version 字段）
├── references/focus-theory.md    # 理论根基（8 条，含出处与争议标注）
├── references/focus-method.md    # 防干扰方法论（把理论变机制）
├── FAQ.md
├── README.md
├── SELF_EVAL.md
└── CHANGELOG.md
```
