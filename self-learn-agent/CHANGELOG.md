# CHANGELOG：self-learn-agent

## 2.0.0（当前版本）

- 重构为真引擎：新增 `scripts/learn.py`，六子命令 `ingest`/`review`/`quiz`/`elaborate`/`interleave`/`report`，纯标准库、确定性可重跑。
- 间隔调度采用 Leitner 盒（1/2/4/7/15/30/60 天）叠加 SM-2 难度因子（Wozniak 1987）。
- 实物证据体系：`knowledge.jsonl`（知识点库）、`events.jsonl`（追加式日志）、`notes/<id>.md`（消化笔记）、`reports/mastery-<date>.md`（掌握度报表）。
- 退出码约定：0 正常 / 1 需关注（高风险或薄弱点）/ 4 系统性警报。
- 资源库三件套：`learning-strategies.json`、`spacing-algorithms.json`、`knowledge-sources.json`，均含 `version: "2.0.0"`。
- 理论长文 11 篇，覆盖 12+ 条带出处理论（年份/期刊/书名可核验）。
- 配套文档：SKILL.md（含主动触发段与理论地图）、FAQ.md、README.md、SELF_EVAL.md（TRACE 5.0/5）、examples/sample-knowledge-log.md。

## 版本一致性

- SKILL.md frontmatter `version: 2.0.0`
- `scripts/learn.py` 常量 `EVENT_VERSION = "2.0.0"`
- 三个 resources 的 `"version": "2.0.0"`

三处版本号保持一致。
