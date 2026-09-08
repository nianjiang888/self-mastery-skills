# self 自我管理技能系列

一套把「想改变」变成可追踪数据的自我管理技能集。不灌鸡汤，每个技能都有可重跑的引擎。

共 **20** 个技能包，全部自包含（包内即可跑通，无需额外依赖）。

## 技能一览

| # | 技能包 | 名称 | 做什么 |
|---|---|---|---|
| 1 | `self-budget-agent` | 个人记账与存钱 | 个人记账与存钱 AI Agent：帮你记下每笔花销，算清钱都去哪了、储蓄率多少、应急金够撑几个月、哪个分类在漏钱，并… |
| 2 | `self-communicate-agent` | 沟通表达复盘 | 沟通表达复盘 AI Agent：帮你记下每次重要对话、量化达成率与对方防御反应、自动判断谈崩卡在哪一层（事实/情绪/… |
| 3 | `self-create-agent` | 创作产出 | 创作产出 AI Agent：帮你持续产出、越创越强。捕获灵感、记录每件作品走到哪一步（启动/完成/打磨/发布），量化… |
| 4 | `self-debug-agent` | 自主调试 | 自主调试引擎。让 Agent（或你）自主复现一个失败、用探针归类病灶、在沙箱里打补丁、用回归测试验证修复，最关键的是… |
| 5 | `self-decide-agent` | 决策日志与回放评分 | 决策日志与回放评分引擎。事前用 pre-mortem/单向门/二阶思考逼出盲点，事中记录选项与可逆性，事后回放打分、… |
| 6 | `self-discipline-agent` | 自律承诺装置 | AI 自律承诺装置引擎。登记承诺（后果/监督人/类别）+ 到期打卡履约 + 自动违约检测 + 问责报告暴露最易破类型… |
| 7 | `self-evaluate-agent` | 元认知评估与反思 | 元认知评估与反思引擎：按 rubric 给任意产出逐维打分并点名证据，跑 Reflexion 多轮闭环（打分→反思→… |
| 8 | `self-fitness-agent` | 健身训练管理 | 健身训练管理 AI Agent：帮你记录每次训练、算清训练负荷与恢复、提前预警伤痛风险、给出渐进式下周计划。适合想增… |
| 9 | `self-focus-agent` | 深度工作与防干扰 | 深度工作/防干扰引擎。规划专注块、记录实际专注与打断来源、量化专注力与切换税，看清「什么最常打断我」，并在干扰过多或… |
| 10 | `self-habit-agent` | 习惯养成与连击 | 习惯叠加 / streak 引擎。把新行为「接」在既有锚点行为之后，自动记录每日打卡、算连击、检测断签、生成养成进度… |
| 11 | `self-improvement-agent` | AI 自我改进 | AI 自我改进 v1.1.0（主动 Agent）。你每次纠正 AI、AI 报错、你想要的缺失功能，它都自动记成永久记… |
| 12 | `self-learn-agent` | 知识消化与抗遗忘 | 知识消化与抗遗忘间隔重复的主动学习 Agent。把书/课吃透成你的私有库——自动排程间隔复习、主动回忆测试、精细质询… |
| 13 | `self-master-agent` | 技能精进与实战检验 | AI Agent 引擎——把「想精通一门技能」变成可复核的爬坡：技能登顶五层阶梯 + 真实实战检验 + 登顶曲线 +… |
| 14 | `self-optimize-agent` | 受控自我实验优化 | 受控自我实验优化引擎：把自评/验证分数当目标函数，跑 A/B 实验，显著胜出才晋升 baseline，用贝叶斯式采集… |
| 15 | `self-protect-agent` | 自我边界守护 | 动手前的自我边界守护引擎。扫描即将执行的操作是否越界/不可逆/超权限/伤己伤人，按"影响×可逆性"分级路由（阻断/警… |
| 16 | `self-reflect-agent` | 每日三省反思 | AI 日三省引擎。记录反省日志、跨时间识别思维惯性、对照自称价值探测言行盲点、四问复盘推向双环学习。与 self-e… |
| 17 | `self-sleep-agent` | 睡眠质量管理 | 睡眠质量管理 AI Agent：记录每晚睡眠、学出你的生理节律与时型、量化睡眠债与规律性、预警弱项并给出可执行的本周… |
| 18 | `self-soothe-agent` | 情绪调节与疏导 | 情绪调节与认知行为（CBT）工具包：帮你把「一来情绪就乱、越想越糟、用错方式自我安慰反而更累」这件模糊的难受，变成可… |
| 19 | `self-teach-agent` | 自我教学与知识内化 | 自我教学与知识内化引擎：把任意外部材料（文章/论文/书/对话/代码库）通过摄入→结构化→排课(由易到难)→自测→间隔… |
| 20 | `self-verify-agent` | 正确性验证与交付门禁 | 正确性验证与交付门禁引擎：在"相信/发布"之前，跑执行门禁(测试/断言)+自洽性(Self-Consistency … |

## 目录结构

```
self/
├── self-budget-agent/
├── self-communicate-agent/
├── self-create-agent/
├── self-debug-agent/
├── self-decide-agent/
├── ...（共 20 个技能目录）
```

每个技能包结构一致：`SKILL.md`（技能定义）、`scripts/`（引擎与冒烟测试）、`resources/`（规则与数据）、`references/`（依据）、`examples/`（输入输出样例）、`README.md`、`FAQ.md`、`CHANGELOG.md`。

## 本地使用

```
git clone <仓库地址>
```

把需要的技能目录整体复制到你的 Agent skills 目录即可。单个技能这样跑：

```
python <技能目录>/scripts/<引擎>.py --help
```

## 从 GitHub 导入到 SkillHub

每个技能独立目录，目录根即 `SKILL.md`，不含二进制文件。在 SkillHub 发布页选「从 GitHub 导入」，绑定账号后会自动扫出候选技能。

**注意：平台单次最多导入 5 个技能，20 个需要分 4 批。**

| 批次 | 技能 |
|---|---|
| 第 1 批 | `self-budget-agent`、`self-communicate-agent`、`self-create-agent`、`self-debug-agent`、`self-decide-agent` |
| 第 2 批 | `self-discipline-agent`、`self-evaluate-agent`、`self-fitness-agent`、`self-focus-agent`、`self-habit-agent` |
| 第 3 批 | `self-improvement-agent`、`self-learn-agent`、`self-master-agent`、`self-optimize-agent`、`self-protect-agent` |
| 第 4 批 | `self-reflect-agent`、`self-sleep-agent`、`self-soothe-agent`、`self-teach-agent`、`self-verify-agent` |

## 许可

MIT
