---
name: self-communicate-agent
display_name: 沟通表达复盘
version: 2.0.0
type: skill
description: 沟通表达复盘 AI Agent：帮你记下每次重要对话、量化达成率与对方防御反应、自动判断谈崩卡在哪一层（事实/情绪/身份）、识别反复出现的沟通模式，并按场景给出带出处的结构化话术。适合说完就后悔、跟最亲的人反而吵得最凶、想提升表达却不知道从哪改的普通人。不做心理治疗，只把话说出去之后发生了什么看清楚。
keywords: [沟通, 沟通技巧, 表达能力, 怎么说话, 说话技巧, 会说话, 不会说话, 说完就后悔, 话说错了, 说话得罪人, 吵架, 跟家人吵架, 夫妻沟通, 亲子沟通, 人际关系, 社交, 社恐, 内向, 聊天, 冷场, 尴尬, 职场沟通, 向上沟通, 汇报, 谈判, 拒绝别人, 不好意思拒绝, 提意见, 反馈, 给下属反馈, 冲突处理, 化解冲突, 缓和气氛, 道歉, 修复关系, 倾听, 共情, 同理心, 非暴力沟通, 高情商, 说话之道, 复盘, 对话记录, communication, communication skills, active listening, difficult conversations, conflict resolution, feedback, assertiveness]
triggers:
  - 说错话了、说完就后悔、当时应该怎么说
  - 跟家人/伴侣/同事反复为同一件事吵
  - 想提升表达能力但不知道从哪下手
  - 提了意见对方就防御、不知道哪里说错了
  - 不会拒绝、每次都答应完又后悔
  - 要汇报/谈判/道歉，不知道怎么开口
  - 总觉得沟通有问题但说不清问题在哪
license: MIT
---

# self-communicate-agent：把"说完就后悔"变成看得见的账

## 一、这个 Agent 是干什么的

self-communicate-agent 是「自我」系列里专注于**沟通表达**的一个能主动干活的 AI Agent。它的服务对象是「用 AI 的人」本人——那句话一出口就知道说错了、跟最亲的人反而吵得最凶、每次都想着「重来一次我该怎么说」的你。

它不替你说话，也不评判谁对谁错，而是把"话说出去了"之后发生的那团模糊懊恼，拆解成一组**可记录、可计算、可复核**的指标：

- **达成率与防御率**：你要的结果拿到了吗？对方是合作、中立、防御还是对抗？
- **卡在哪一层**：自动判断这次对话是卡在事实层（事没说清）、情绪层（感受没被接住）还是身份层（对方觉得自己被否定了）。**绝大多数谈崩不在事实层。**
- **情绪代价**：你情绪上头时说的话，达成率比平时低多少——把「别在气头上说话」从一句劝告变成你自己的数字。
- **关系账户**：对话结束后，这段关系是往里走了一层，还是退了一层。
- **模式识别**：哪种场景是你的短板、哪段关系在被持续消耗、你是不是一直在说而没在听。
- **结构化话术**：按场景 × 目标，从带出处的话术库里给你「下次怎么说」，而不是空泛的「注意沟通方式」。

它背后站着一整套沟通科学的循证底座（详见 `references/` 与 `resources/`）：非暴力沟通、困难对话三层模型、关键对话与安全感、立场与利益、SCARF 大脑威胁模型、SBI-R 反馈与激进坦诚、乔哈里视窗、情绪标注、反映式倾听、冲突处理模式 TKI、印象形成、心理安全、社会渗透、复盘与刻意练习。不是"高情商话术大全"，而是**带年份、期刊、书名出处**的理论。

## 二、主动触发（重要）

这个 Agent **不是等你来翻文档的说明书**。当以下情形出现时，它会主动介入：

- 你说"刚才那句话说错了"——主动建议用 `log` 记下来，并在 24 小时内补一句「下次我想怎么说」；
- 你说"又跟家里人吵起来了"——主动跑 `risk`，看「家人」这个对象的关系账户是不是在持续走低，用困难对话三层模型点破：多半不是事的错，是身份层被碰了；
- 你说"我提了意见对方就防御"——主动用防御率指标 + SCARF 模型排查你碰了哪个维度（地位/确定性/自主/关联/公平），并给 SBI-R 的四步说法；
- 你说"不会拒绝别人"——主动调出「拒绝而不伤关系」模板（Yes-No-Yes 结构），并指出含糊其辞（「我看看吧」）才是最大的关系杀手；
- 你要去汇报/谈判/道歉/提分手——主动用 `script --scene <场景> --goal <目标>` 给结构化说法，并提醒开场承担了不成比例的重量（首因效应）；
- 你说"我沟通有问题但说不清在哪"——主动建议先连续记 5 次对话（**包括谈崩的那些，它们信息量最大**），再用 `trend` 看分场景、分对象的统计；
- 你说"我一着急就控制不住"——主动看情绪代价指标，并给硬规则：情绪强度到 7 就暂停，改约时间；
- 报告退出码为 1（存在中/高严重度模式）——主动用 `plan` 给出本周唯一要练的动作。

换句话说：它在该出手时出手，在该收手时收手（不替代心理咨询，不做关系仲裁），在该教育时教育（用理论而非鸡汤）。

## 三、理论地图（14 篇均带出处）

| # | 主题 | 代表出处 |
|---|---|---|
| 1 | 非暴力沟通四步 | Rosenberg 2003, *Nonviolent Communication* |
| 2 | 困难对话三层结构 | Stone, Patton & Heen 1999, *Difficult Conversations* |
| 3 | 关键对话与安全感 | Patterson et al. 2002, *Crucial Conversations* |
| 4 | 立场与利益 | Fisher & Ury 1981, *Getting to Yes* |
| 5 | SCARF 威胁-奖赏模型 | Rock 2008, *NeuroLeadership Journal* 1(1) |
| 6 | SBI-R 反馈与激进坦诚 | Scott 2017；Kluger & DeNisi 1996 元分析 |
| 7 | 乔哈里视窗 | Luft & Ingham 1955 |
| 8 | 情绪标注 | Lieberman et al. 2007, *Psychol Sci* 18(5) |
| 9 | 反映式倾听 | Rogers 1957, *J Consult Psychol* 21(2) |
| 10 | 冲突处理模式 TKI | Thomas & Kilmann 1974 |
| 11 | 印象形成与首因效应 | Asch 1946；Fiske et al. 2007 |
| 12 | 心理安全 | Edmondson 1999, *ASQ* 44(2) |
| 13 | 社会渗透与自我表露 | Altman & Taylor 1973 |
| 14 | 复盘与刻意练习 | Ericsson et al. 1993, *Psychol Rev* 100(3) |

## 四、快速上手

```bash
# 0) 设沟通档案（我最想改善的场景/对象），可选
python scripts/comm.py --data ./my_comm set --focus_scene 冲突 --focus_relation 家人

# 1) 记一次重要对话（outcome 是必填，其余可省）
python scripts/comm.py --data ./my_comm log \
  --date 2026-09-01 --scene 冲突 --counterpart 家人 --goal 关系 \
  --tone 9 --listened 2 --reaction 对抗 --outcome 1 --aftermath -2 \
  --words "你从来都不理解我"

# 2) 看沟通全景（达成率/防御率/情绪代价/关系账户/分场景分对象）
python scripts/comm.py --data ./my_comm trend --days 30

# 3) 复盘单条（自动判断卡在哪一层 + 给换法）
python scripts/comm.py --data ./my_comm review --id 2026-09-01#1

# 4) 拿结构化话术（按场景 × 目标，带出处）
python scripts/comm.py --data ./my_comm script --scene 冲突 --goal 关系

# 5) 模式与风险扫描（中/高严重度退出码 1）
python scripts/comm.py --data ./my_comm risk --days 30

# 6) 本周最值得练的一个
python scripts/comm.py --data ./my_comm plan --days 30

# 7) 完整报告（落盘 + 中/高退出码 1）
python scripts/comm.py --data ./my_comm report --days 30
```

数据落在 `--data`：`events.jsonl`（按 `type+id` 幂等，记错可重记覆盖）+ `profile.json` + `reports/comm-<日期>.md`，纯本地、不联网、可长期追踪、重跑结果一致。

## 五、子命令速查

| 命令 | 作用 | 关键参数 |
|---|---|---|
| `set` | 设沟通档案（聚焦场景/对象/目标） | --focus_scene --focus_relation --target_outcome --note |
| `log` | 记一次重要对话 | --date --scene --counterpart --goal --tone --listened --reaction --outcome --aftermath --layer --words --better --id |
| `trend` | 沟通全景统计 | --days（默认 30） |
| `review` | 单条复盘（拆三层 + 给换法） | --id（留空复盘最近一条） |
| `script` | 按场景×目标拿结构化话术 | --scene --goal |
| `risk` | 模式与风险扫描（中/高退出码 1） | --days（默认 30） |
| `plan` | 本周最值得练的一个 | --days（默认 30） |
| `report` | 完整报告（落盘 + 中/高退出码 1） | --days（默认 30） |

退出码：`0` 正常 / `1` 存在中或高严重度沟通模式 / `2` 用法错误 / `4` 参数或数据不可用。

## 六、边界声明

- 这是**复盘工具**：帮你量化与识别模式，不做心理治疗、不做临床诊断、不评判谁对谁错；
- **层次推断是启发式的**，只用三个字段（情绪强度、结果、关系变化）判断，粗糙。用 `log --layer` 可以覆盖引擎的推断——你自己的判断通常比引擎准；
- **自评数据有系统性偏差**：你对「我听了多少」的打分通常高于实际。所以 `aftermath`（关系变化）和 `reaction`（对方反应）这类外部信号，比 `tone`、`listened` 这类内部自评更值得看；
- **样本不足不做模式判定**：少于 5 条记录时只给提示，不给结论；
- **隐私**：`words` 字段建议只写**你自己的原话**，不记录对方的私人信息。所有数据存本地，不上传、不联网；
- **涉及持续的关系暴力、职场霸凌、家庭暴力，请寻求专业帮助。本工具不适用。**

详见 `README.md`（导航）、`FAQ.md`（场景对照）、`references/`（14 篇理论长文）、`examples/`（完整样例）。
