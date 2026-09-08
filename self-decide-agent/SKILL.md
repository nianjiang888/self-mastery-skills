---
name: self-decide-agent
display_name: 决策日志与回放评分
description: 决策日志与回放评分引擎。事前用 pre-mortem/单向门/二阶思考逼出盲点，事中记录选项与可逆性，事后回放打分、检测可逆性误判、识别反复认知偏差并生成问责报告。理论落地为可重跑代码，不靠模型自觉。
version: 2.0.0
license: MIT
---

# self-decide-agent · 决策日志与回放评分引擎

帮用户把「做决定」从一句口号变成可复盘的数据闭环：事前逼出盲点、事中锁定真实想法、事后最小化后悔地复盘。它不是给建议的聊天框，而是一套**强制调用 System 2 的外部脚手架**——每一条理论都对应一个子命令、一种退出码、一份可复核的产物。

## 主动触发

满足任一即主动启动（无需等用户发问）：

- 用户表达重大决策犹豫（「要不要…」「纠结…」「选 A 还是 B」）。
- 用户刚做完一个可逆性高或后果重的决定，需要立刻 `log` 锁定，避免记忆自美化。
- 用户复盘过去决定、发现「总在同一个坑里摔跤」。
- 周期性（如周/月）主动 `report` 一次，把反复偏差变成检查清单。

## 它能做什么（7 子命令）

```bash
decide frameworks                       # 列出/查看 12 个决策框架库
decide log --context "..." --options "A;B" --chosen A \
           --expected "..." --reversibility reversible|irreversible \
           [--framework bezos_doors]    # 记录一次决策（含偏差预检）
decide replay --id d1 --actual "..." [--score 0-100] [--regret 0-100] \
           [--reversibility reversible]  # 事后回放打分，纠正可逆性误判
decide premortem --context "..." [--reversibility ...]  # 事前验尸 + 二阶 + 可逆校验
decide bias                             # 跨决策识别反复认知偏差
decide report                           # 聚合：误判率 / 常犯偏差 / 后悔最小化
decide list                             # 列出已记录决策
```

退出码：`0` 正常 / `1` 反复偏差或误判率偏高或单次重大不可逆误判 / `4` 重大不可逆误判 ≥2 次（系统性判断缺陷）。

## 理论根基（12 条，均带可核验出处）

| # | 理论 | 提出者 / 出处 | 落点 |
|---|---|---|---|
| 1 | 单向门 / 双向门（可逆性框架） | Bezos，亚马逊 2015/2016 股东信 | `log` 强制标可逆性；`report` 算误判率 |
| 2 | 后悔最小化框架 | Bezos 1994（Gilovich 提供根基） | `replay` 后悔度字段；`premortem` 第五步 |
| 3 | 事前验尸 Pre-Mortem | Gary Klein 2007（HBR 85(9):18-19） | `premortem` 子命令 |
| 4 | 二阶思考 | Howard Marks 2011（《The Most Important Thing》，溯 Bastiat 1850） | `premortem` 第三步 |
| 5 | 损失厌恶 | Kahneman & Tversky 1979（Econometrica 47(2):263-291，λ≈2.25） | 偏差库 `loss_aversion` |
| 6 | 锚定效应 | Tversky & Kahneman 1974（Science） | 偏差库 `anchoring` |
| 7 | 沉没成本 / 升级承诺 | Staw 1976（OBHDP 16(1):27-44） | 偏差库 `sunk_cost` |
| 8 | 外部视角 / 计划谬误 | Kahneman, Lovallo & Sibony 2011（HBR） | 框架库 `external_view` |
| 9 | 10-10-10 三时窗 | Suzy Welch 2008（《10-10-10》） | 框架库 `ten_ten_ten` |
| 10 | Cynefin 复杂情境 | Snowden & Boone 2007（HBR，PMID 18159787） | 框架库 `cynefin` |
| 11 | OODA 循环 | John Boyd 1987 | 框架库 `ooda` |
| 12 | 实物期权 / 灵活性价值 | Dixit & Pindyck 1994（《Investment Under Uncertainty》） | 框架库 `real_options` |
| 13 | 决策疲劳 / System 2 损耗 | Baumeister 等（ego depletion） | `bias` 报告末尾提示 |

> 各理论的详细推导、原文出处与「怎么落地成机制」见 `references/` 下 10 篇长文。

## 与系列内其他包的分工

- **self-evaluate**（#2）：评「物」——对单条产出打分、闭环改进。
- **self-reflect**（#8）：省「己」——跨时间模式与思维盲点。
- **self-protect**（#7）：挡「险」——动手前的红线闸门。
- **self-decide**（本包）：管「择」——做选择本身，并把选择变成可复盘数据。四者不重叠。

## 文件结构

```text
SKILL.md
scripts/decide.py                  真引擎（7 子命令）
resources/biases.json              偏差库（13 条，含 version）
resources/decision-frameworks.json 框架库（12 个，含 version）
resources/decision-prompts.json    三阶段自问清单（含 version）
references/decide-theory.md        理论总论 + 闭环 + System 1/2
references/reversible-framework.md
references/pre-mortem-method.md
references/second-order-thinking.md
references/decision-biases-catalog.md
references/regret-minimization.md
references/cynefin-ooda.md
references/10-10-10-method.md
references/external-view-planning-fallacy.md
references/real-options-flexibility.md
FAQ.md  README.md  SELF_EVAL.md  CHANGELOG.md
examples/sample-decision-log.md
```

## 诚实边界（防误用）

- 偏差检测 = 确定性子串命中，覆盖面受 `biases.json` 词表限制；生僻表达会漏检，这是「不臆测」的代价。
- 满意度 / 后悔度是用户自评输入，引擎不做心理测量，只负责结构化与追踪。
- 可逆性分类由用户判断，引擎只记录并事后比对误判，不替用户定义什么叫不可逆。
- 不联网、不收集外部数据，所有产物留在用户指定的 `--store`。

## 4.8 实物证据（可重跑）

- `decision-log.jsonl`：每条决策一行纯数据，任意时刻重跑 `bias`/`report` 结论一致。
- `replay-<id>.md` / `bias-report.md` / `decision-report.md` / `premortem-<slug>.md`：各命令生成的可复核 markdown。
