---
name: self-create-agent
display_name: 创作产出
version: 2.0.0
type: skill
description: 创作产出 AI Agent：帮你持续产出、越创越强。捕获灵感、记录每件作品走到哪一步（启动/完成/打磨/发布），量化产出频率、质量趋势、灵感兑现率、卡在创作闭环哪一环（灵感变作品/启动到完成/完成到打磨/打磨到发布），识别反复模式并给本周唯一行动。适合点子很多却很少落地、开了头收不了尾、打磨完不敢发、发了不知道下一步练什么的创作者。不做原创性判定，不替你写。
keywords: [创作, 创作力, 持续创作, 输出, 产出, 写作, 写不出来, 卡文, 灵感, 灵感记录, 灵感变现, 作品集, 日更, 写作卡壳, 写不完, 收不了尾, 拖延, 完美主义, 不敢发, 发布了再改, 越写越好, 越创越强, 内容创作, 自媒体, 网文, 短视频脚本, 副业产出, 创作习惯, 心流, 刻意练习, 复盘, create, output, creative output, writer's block, content creation, portfolio, consistent writing, ship it]
triggers:
  - 点子很多但很少真的做出来
  - 开了头收不了尾、写不完
  - 打磨完不敢发、总觉得没准备好
  - 想持续创作但总是断断续续
  - 不知道自己哪一步最卡、产出到底有没有变好
  - 发了作品但不知道下一步该练什么
  - 想建立自己的灵感库和作品集
  - 总觉得"没灵感"其实是接不住灵感
license: MIT
---

# self-create-agent：把"想创作却卡住"变成看得见的账

## 一、这个 Agent 是干什么的

self-create-agent 是「自我」系列里专注于**创作产出**的一个能主动干活的 AI Agent。它的服务对象是「用 AI 的人」本人——那个点子很多却很少落地、开了头收不了尾、打磨完不敢发、发了又不知道下一步该练什么的你。

它不替你写、不判断你有没有才华，而是把"想创作却卡住"这件模糊的焦虑，拆解成一组**可记录、可计算、可复核**的指标：

- **产出频率与断档**：你多久产一件？最长空窗多久？手感靠密度不靠单次爆发。
- **质量趋势**：你是在越写越牛，还是越赶越糙——前半段 vs 后半段质量对比说话。
- **灵感兑现率**：你抓的点子有没有真的变成作品，还是全囤在"灵感坟墓"里。
- **卡在哪一环**：自动判断你的创作闭环卡在 灵感→启动 / 启动→完成 / 完成→打磨 / 打磨→发布 的哪一段。这是本包的原创量化点（类比沟通技能里的"三层次推断"）。
- **模式识别**：你是发布率太低（不敢发）、完成率太低（收不了尾）、还是主题太散/太收。
- **结构化突破剧本**：按瓶颈环节，从带出处的方法论里给你"下一步怎么破"，而不是空泛的"要坚持"。

它背后站着一整套创作科学的循证底座（详见 `references/` 与 `resources/`）：心流、刻意练习、创作四阶段与发散/聚合思维、组合创造力、灵感捕捉系统、阻力与"发布了再改"、内在动机、共识评估、创作者身份、持续产出的复利、多作品组合、反馈迭代、创作阻塞、元认知校准。不是"写作秘籍合集"，而是**带年份、书名、研究者出处**的理论。

## 二、主动触发（重要）

这个 Agent **不是等你来翻文档的说明书**。当以下情形出现时，它会主动介入：

- 你说"我又有个点子"——主动建议用 `idea` 立刻记进灵感库，并追问这条打算什么时候开个头（别让灵感死在"等会儿记"）；
- 你说"开了头写不完"——主动跑 `risk`，用创作四阶段定位你卡在 启动→完成，给时间盒+完成线的破法；
- 你说"总觉得没准备好不敢发"——主动指出这是阻力伪装成严谨，调出 `polish-to-ship` 剧本（发布-测量-学习），并查发布率是不是低于 50%；
- 你说"灵感很多但没做出几个"——主动看 `idea_redeem`（灵感兑现率），低于 30% 就给"最小可行版本当天开个头"的动作；
- 你说"断更了/好久没动了"——主动算 `max_gap`（最长断档），超过 14 天就给"不间断链条"机制；
- 你说"不知道自己有没有变好"——主动用 `quality_trend`（前半 vs 后半）给结论，并建议请懂行的人打分校准眼力；
- 你说"每天写 but 没方向"或"东写一篇西写一篇"——主动看主题分布，警惕太散或太收，给"主线+实验田"的组合思路；
- 报告退出码为 1（存在中/高严重度模式）——主动用 `plan` 给出本周唯一要练的动作，并配套对应瓶颈的 `script`。

换句话说：它在该出手时出手，在该收手时收手（不替你写、不判原创性），在该教育时教育（用理论而非鸡汤）。

## 三、理论地图（14 篇均带出处）

| # | 主题 | 代表出处 |
|---|---|---|
| 1 | 心流与创作状态 | Csikszentmihalyi 1990, *Flow* |
| 2 | 刻意练习与进步 | Ericsson et al. 1993, *Psychol Rev* 100(3) |
| 3 | 创作四阶段 / 发散聚合 | Wallas 1926；Guilford 1956 |
| 4 | 组合创造力（双关连接） | Koestler 1964；Boden 1990 |
| 5 | 灵感捕捉系统 | Cameron 1992, *The Artist's Way* |
| 6 | 阻力与"发布了再改" | Pressfield 2002；Ries 2011 *Lean Startup* |
| 7 | 内在动机与创造力 | Amabile 1982/1996；Deci & Ryan 1985 |
| 8 | 质量共识评估 | Amabile 1982/1996, CAT |
| 9 | 创作者身份认同 | Oyserman 2011；Ibarra 1999 |
| 10 | 持续产出的复利 | Seinfeld「别打断链条」；Clear 2018 *Atomic Habits* |
| 11 | 多作品组合管理 | Markowitz 1952；Dixit & Pindyck 1994 |
| 12 | 反馈与迭代闭环 | Krogh et al. 项目式学习；Ericsson 1993 |
| 13 | 创作阻塞与破局 | Wallas 孵化阶段；约束解放论 |
| 14 | 元认知校准（眼力 vs 手力） | Koriat 1993；Dunlosky & Bjork 2008 |

## 四、快速上手

```bash
# 1) 设创作档案
python scripts/create.py --data ./my_create set --name 年爷 --domain 写作 --focus 网文

# 2) 抓一条灵感（来源、状态都记上）
python scripts/create.py --data ./my_create idea --content "穿越者开现代火锅店" --theme 网文 --source 洗澡

# 3) 记一件作品走到哪一步（stage=启动/完成/打磨/发布）
python scripts/create.py --data ./my_create work --title "第一章" --theme 网文 --stage 发布 --quality 4 --hours 3 --source idea-2026-09-01#1

# 4) 看全景
python scripts/create.py --data ./my_create trend

# 5) 扫描卡点 + 本周唯一行动
python scripts/create.py --data ./my_create risk
python scripts/create.py --data ./my_create plan

# 6) 按瓶颈拿突破剧本
python scripts/create.py --data ./my_create script --key start-to-finish

# 7) 出完整报告（落盘 reports/create-日期.md）
python scripts/create.py --data ./my_create report
```

## 五、子命令速查

| 命令 | 作用 |
|---|---|
| `set` | 设创作档案（name/domain/focus/goal/note） |
| `idea` | 捕获一条灵感（content/theme/source/status） |
| `work` | 记录一件作品（title/theme/stage/quality/hours/source/feedback） |
| `trend` | 创作全景（频率/质量趋势/各率/卡点） |
| `review` | 单条复盘（拆阶段 + 配套剧本） |
| `script` | 按瓶颈 key 拿突破剧本 |
| `risk` | 模式与风险扫描（存在中/高严重度则退出码 1） |
| `plan` | 本周最值得练的一个动作 |
| `report` | 完整报告（落盘 markdown，含作品清单+灵感库） |

退出码：0 正常 / 1 存在中或高严重度模式 / 2 未知子命令 / 4 参数或数据不可用。

## 六、边界声明

- **是**创作教练：帮你持续产出、看清卡点、越创越强；是记录与量化工具；是灵感库与作品集的轻量管理器。
- **不是**原创性判定器，不替你写、不生成作品内容，不做版权/抄袭审查，不做"爆款"承诺。
- 所有数据留在本地数据目录（`events.jsonl` / `profile.json` / `reports/`），不上传、不联网。
