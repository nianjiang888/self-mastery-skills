# FAQ：self-learn-agent 常见问题

**Q1：这个 Agent 是清单工具还是真引擎？**
是真引擎。`scripts/learn.py` 是可运行的 Python 程序（纯标准库），六个子命令都会读写 `knowledge.jsonl` / `events.jsonl` 并产出 markdown 实物证据，可逐条复核、可重跑。它不是给你看的建议列表。

**Q2：必须装第三方库吗？**
不需要。引擎只用 Python 标准库（json/os/sys/argparse/datetime/random/hashlib/re），任何装了 Python 3 的环境直接跑。

**Q3：数据存在哪？会丢吗？**
默认在当前目录的 `self_learn_data/`（`--data` 可改）。核心是 `knowledge.jsonl` 与 `events.jsonl` 两个文件，建议定期备份这两个文件即可。删除数据目录会丢失进度，但可重新 `ingest`。

**Q4：概念要填多细？**
填"原子知识点"，即一个可独立回忆的点（如"工作记忆容量有限"），不要填整章标题。越原子，复习与测试越精准。详见 `resources/knowledge-sources.json` 的拆解建议。

**Q5：退出码 1 和 4 分别代表什么？**
`0` 正常；`1` 需关注——存在高风险或薄弱知识点，应优先复习；`4` 系统性警报——数据目录不可读写、配置损坏等，需排查环境。可在脚本/流水线里据此决定是否阻断。

**Q6：间隔复习的"1/2/4/7/15/30/60 天"是怎么来的？**
来自 Leitner 盒（Leitner 1972）的递增间隔，并由 SM-2 难度因子（Wozniak 1987）在通过时放大，取两者较大值。原理见 `references/spacing-effect.md` 与 `resources/spacing-algorithms.json`。

**Q7：为什么 review 有时返回 1 而不是 0？**
当待复习项里存在掌握度<0.4 的薄弱点或遗忘≥2 次的高风险点时，引擎返回 `1` 提醒你"别被流畅骗了，这些点真危险"。这是元认知监控（Koriat 1993）的工程化预警。

**Q8：quiz 和 review 的区别？**
`review` 是"按排程复习并记成绩、推进间隔"；`quiz` 是"额外主动回忆抽测、记录 recall 成绩更新掌握度"。二者都触发测试效应（Karpicke 2008），但 review 偏调度、quiz 偏自测。

**Q9：interleave 每次结果一样吗？**
不一样——它以"日期"为随机种子确定性混排，所以同一天多次运行结果一致、可复核；不同天则自然变化，符合"每天一份新混排"的设计。零基础不宜直接交错，应先 ingest 打底。

**Q10：掌握度（mastery）准确吗？**
是启发式指标，不是绝对测量。它通过复习成绩、回忆成绩、质询动作综合更新，用于排序与风险预警。真正校准要靠 `quiz` 的客观 recall，而非主观感觉（见 `references/metacognitive-monitoring.md`）。

**Q11：能多人共用一个知识库吗？**
`knowledge.jsonl` 是单文件追加式，并发写入不安全。建议每人/每项目独立 `--data` 目录，或用版本控制管理备份文件。

**Q12：和其他 self 系列 Agent 怎么配合？**
本 Agent 负责"把知识吃透留牢"；可配合 self-focus（专注时段）、self-discipline（执行）、self-reflect（复盘）形成"学—练—省"闭环。各 Agent 数据独立，互不直接耦合。
