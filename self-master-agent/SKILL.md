---
name: self-master-agent
display_name: 技能精进与实战检验
version: 2.0.0
description: AI Agent 引擎——把「想精通一门技能」变成可复核的爬坡：技能登顶五层阶梯 + 真实实战检验 + 登顶曲线 + 弱项预警。self-master-agent 帮你从入门一路登顶，每一步都有实物证据。
keywords: [self-master, 自精通, 技能登顶, 刻意练习, 登顶曲线, AI Agent,  mastery, 实战检验, autonomous, self-improvement]
triggers: [精通一门技能, 技能登顶, 从入门到专家, 刻意练习计划, 掌握度评估, 学习路线规划, 能力阶梯]
license: MIT
---

# self-master-agent（自精通：技能登顶阶梯 + 实战检验）

> 第三方立场说明：这是一个**能主动干活的 AI Agent 技能**。它不是「教你如何精通」的文章集合，而是一个**带引擎、留实物证据、可复核**的登顶系统。使用者每登记一门技能、每做一次真实实战，都会被记录、被校准、被推着向上爬。

## 主动触发（何时这个 Agent 会自动介入）

self-master-agent 在下列情形**主动产出**，无需你再想「下一步干嘛」：

- 你登记或想精通一门技能时 → 主动生成**五级登顶阶梯**草稿与首批实战建议。
- 你完成一次真实练习/产出时 → 主动调用 `drill` 记录，并**即时判断能否晋升**。
- 你自评「我会了」时 → 主动用 `measure` + 真实实战**校准你的能力错觉**。
- 你长时间没实战时 → 主动在 `report` 里标**弱项预警**，提醒补练。
- 你想知道「还差什么」时 → 主动用 `plan` 给出**下一步缺口清单**。
- 每周 → 主动生成**掌握度报告 + 登顶曲线**，让你看见长期复利。

## 它能做什么（子命令）

| 子命令 | 作用 | 关键产出 |
|---|---|---|
| `add` | 登记一门要精通的技能 | 技能档案（目标层/当前层） |
| `ladder` | 设定/查看五级登顶阶梯判据 | 每层可核验标准 |
| `drill` | 记录一次真实世界实战 | 实战日志 + 可能触发晋升 |
| `measure` | 自评当前层级得分 | 校准「以为会 vs 真会」 |
| `report` | 掌握度报告 + 登顶曲线 + 弱项预警 | markdown 报告（退出码 1=有弱项） |
| `plan` | 给出冲刺下一级的缺口清单 | 下一步行动 |

## 理论地图（为何这样设计）

self-master-agent 的每一处设计都锚定在经同行评议的学习科学之上，详见 `references/`：

- **Dreyfus 技能习得五阶段**（1980/1986）→ 五级阶梯的直接母本。
- **Ericsson 刻意练习**（1993, *Psychological Review*）→ `drill` 是刻意练习单元。
- **Bloom 大师级表现研究**（1985）→ 「天才可培养」+ 导师阶梯内化。
- **ACT-R 程序性知识**（Anderson 1982）→ 规则编译成自动，解释幂律曲线。
- **Fitts & Posner 三阶段**（1967）→ 自动化只能由表现证明。
- **Kahneman & Klein 直觉专长**（2009）→ L4 直觉判据分领域设边界。
- **Csikszentmihalyi 心流**（1990）→ `drill` 难度=心流通道控制阀。
- **Salomon & Perkins 迁移理论**（1989）→ 强制真实多样情境防不迁移。
- **Dweck 成长型思维**（2006）→ 弱项用「缺口」措辞护信念。
- **Bloom 掌握学习**（1968）→ 未达标不晋下级。
- **Koriat 元认知校准 / 能力错觉**（1993/2008）→ measure+drill 双重校准。

## 与「用 AI 的人」的关系

本系列母题是「**自我 = AI 自改 + 用 AI 的人**」。self-master-agent 落在「用 AI 的人」这一侧：它不替你练，而是当那个**永不下班的陪练与校准器**，把「登顶」这件模糊的事，变成每天可打卡、可复核、不可逆向下的爬坡记录。

## 快速上手

```bash
# 1. 登记技能
python scripts/master.py --data ./my_master add --name "Python 性能优化" \
    --goal "能把慢代码提速10倍" --target 5 --level 1

# 2. 定义登顶阶梯（每层写可核验判据）
python scripts/master.py --data ./my_master ladder --id "#1" \
    --define "L1:能读懂火焰图;L2:能定位一类瓶颈;L3:能稳定提速2倍;L4:能设计缓存策略;L5:能定义团队性能规范"

# 3. 做真实实战（带证据）
python scripts/master.py --data ./my_master drill --id "#1" \
    --task "优化导出脚本" --difficulty 2 --result success --confidence 4 --evidence "export_v2.py"

# 4. 自评校准
python scripts/master.py --data ./my_master measure --id "#1" --score 2 --note "能定位了"

# 5. 看报告与下一步
python scripts/master.py --data ./my_master report
python scripts/master.py --data ./my_master plan --id "#1"
```

退出码：0 正常 / 1 需关注（存在未达标弱项）/ 4 系统性警报（参数或数据错误）。

详见 `README.md`（导航）、`FAQ.md`（疑问）、`references/`（理论长文）、`SELF_EVAL.md`（自评为真引擎的评估）。
