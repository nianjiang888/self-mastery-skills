# CHANGELOG · self-decide-agent

## v2.0.0 （2026-09-01，深度版）

深度重构，相比早期草版：

- **理论加量**：5 条 → 13 条，逐条带可核验出处（Bezos 股东信 / Gilovich 1995 / Klein 2007 HBR / Marks 2011 / KT 1979 Econometrica / Tversky&Kahneman 1974 / Staw 1976 / Kahneman et al. 2011 HBR / Welch 2008 / Snowden&Boone 2007 HBR / Boyd 1987 / Dixit&Pindyck 1994 / Baumeister）。
- **文件加量**：9 个 → 20 个。
  - 新增 `resources/decision-frameworks.json`（12 框架库）、`resources/decision-prompts.json`（三阶段自问）。
  - 新增 `references/` 从 2 篇 → 10 篇（每篇对应一个框架/理论长文，含出处）。
  - 新增 `examples/sample-decision-log.md`。
- **引擎增强**：`scripts/decide.py` 由 6 子命令增至 7，新增 `frameworks` 子命令（列出/查看 12 框架），`log` 支持 `--framework` 标注所用框架。
- **冒烟补齐**：`smoke_self_decide.py` 28 用例全 PASS，覆盖 7 子命令、各退出码、偏差识别、jsonl 累积。
- 三处版本一致：`SKILL.md` / 引擎 `EVENT_VERSION` / `resources/*.json` 的 `version` 均为 `2.0.0`。

## 理论出处速查

| 理论 | 出处 |
|---|---|
| 单向门/双向门 | Bezos, 亚马逊 2015/2016 股东信 |
| 后悔最小化 | Bezos 1994（Gilovich & Medvec 1995 根基） |
| 事前验尸 | Klein, HBR 85(9):18-19, 2007 |
| 二阶思考 | Marks, 《The Most Important Thing》, 2011（溯 Bastiat 1850） |
| 损失厌恶 | Kahneman & Tversky, Econometrica 47(2):263-291, 1979 |
| 锚定效应 | Tversky & Kahneman, Science, 1974 |
| 沉没成本 | Staw, OBHDP 16(1):27-44, 1976 |
| 外部视角 | Kahneman, Lovallo & Sibony, HBR, 2011 |
| 10-10-10 | Welch, 《10-10-10》, 2008 |
| Cynefin | Snowden & Boone, HBR, PMID 18159787, 2007 |
| OODA | Boyd, 1987 |
| 实物期权 | Dixit & Pindyck, 《Investment Under Uncertainty》, 1994 |
| 决策疲劳 | Baumeister 等（ego depletion） |
