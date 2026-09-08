# Changelog — self-master-agent

## v2.0.0（2026-09-01）

- **首次发布**：self-master-agent v2.0.0，定位「自精通：技能登顶阶梯 + 实战检验」。
- **真引擎** `scripts/master.py`：
  - 6 个子命令：`add` / `ladder` / `drill` / `measure` / `report` / `plan`。
  - 五级登顶阶梯（L1 入门 → L5 登顶），晋升需「3 次下一级难度真实实战成功 + 自评达标」。
  - 登顶曲线（`# - - -` 式可视化）+ 弱项预警（退出码 1）。
  - 纯标准库实现，退出码 0/1/4，确定性可重跑。
- **资源库** `resources/`（均含 `version: "2.0.0"`）：
  - `mastery-levels.json`：五级阶梯通用判据库。
  - `deliberate-practice.json`：刻意练习八原则。
  - `skill-domains.json`：常见技能领域阶梯示例。
- **理论长文** `references/`（11 篇，均带可核验出处，各 ≥2000 中文字）：
  - dreyfus-skill-model / deliberate-practice / bloom-talent / act-r-procedural /
    fitts-posner / intuitive-expertise / flow / transfer-theory / growth-mindset /
    mastery-learning / metacognitive-calibration / expert-novice-difference。
  - 覆盖理论：Dreyfus(1980/1986)、Ericsson(1993)、Bloom(1985/1968)、Anderson(1982)、
    Fitts&Posner(1967)、Kahneman&Klein(2009)、Csikszentmihalyi(1990)、
    Salomon&Perkins(1989)、Dweck(2006)、Koriat(1993)、Chi et al.(1981)。
- **配套文档**：SKILL.md（含主动触发段 + 理论地图）、FAQ.md（12 问）、README.md（导航）、SELF_EVAL.md（TRACE 5.0/5）、本 CHANGELOG、examples/sample-mastery.md。
- **质量验证**：冒烟测试 `smoke_self_master.py` 30+ 用例全 PASS；打包 `self-master-agent-2.0.0.zip` 去 BOM/CRLF、SKILL.md 在根、三处版本一致 2.0.0。
- **版本一致性**：SKILL.md `version: 2.0.0` / 引擎 `ENGINE_VERSION="2.0.0"` / 3 个 resources `"version":"2.0.0"` 三处一致。
