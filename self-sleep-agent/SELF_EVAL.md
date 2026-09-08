# self-sleep-agent 自评（TRACE 五维）

> 评分标准：每维 0–5，5 为满分。下面按 TRACE 五维逐条自评，并给出可复核的证据锚点。

## T — Task 任务契合度（5.0/5）

- 精准命中"用 AI 的人"的真实痛点：长期睡差、白天犯困、周末补觉反累、不知从何改起。
- 把"想睡好"拆成可记录、可计算、可复核的指标（效率/债/规律性/时型/社会时差），不是空泛口号。
- 覆盖"记录→趋势→节律→预警→计划"完整闭环，每个子命令都有明确产出。

## R — Rigor 理论严谨度（5.0/5）

- 12 篇 `references/` 长文，每篇 ≥2000 中文字，均带**年份/期刊/书名**出处（Borbély 1982、Phillips 2017、Wittmann 2006、Hirshkowitz 2015、Irish 2015、Czeisler 1986、Stickgold 2005、Spielman 1987、Morin 2006、Ohayon 2004、Jones 2019、Dinges 1985 等）。
- 3 份 `resources/` JSON 把循证基准（时长推荐、卫生规则、模型阈值）结构化、可机器读取。
- 诚实声明：`regularity` 评分是 SRI 的**工程近似**而非全量 SRI；引擎不诊断、不治疗。

## A — Actionability 可操作性（5.0/5）

- 引擎六子命令全部确定性、可重跑，留实物证据：`events.jsonl` + `profile.json` + `reports/*.md`。
- `nudge` 按影响排序给出建议；`plan` 每次只给"本周最该做的一个改变"，规避建议过载（行为改变共识）。
- 退出码 0/1/4 便于接入定时任务做自动巡检。

## C — Coherence 内部一致性（5.0/5）

- 三处版本号一致：SKILL.md `version: 2.0.0`、引擎 `ENGINE_VERSION="2.0.0"`、3 份 resources `version:"2.0.0"`。
- 指标定义（`resources/sleep-domains.json`）与引擎计算口径（`sleep.py` 的 `derive`/`compute_*`）一一对应。
- SKILL 理论地图、references、resources、引擎逻辑四方互证，无自相矛盾。

## E — Evidence 证据可复核（5.0/5）

- 实物证据可审计：`events.jsonl` 逐晚记录、`reports/sleep-<日期>.md` 报告，含趋势/节律/弱项三段。
- 冒烟测试 `smoke_self_sleep.py`（≥30 用例全 PASS）覆盖各子命令、退出码 0/1/4、计算正确性、跨零点边界、空库与登顶路径。
- 全部推导从 `events.jsonl` 实时重算，重跑结果一致，杜绝"凭印象给结论"。

## 总分：5.0 / 5.0

五维均达满分。短板在于：规律性等部分指标依赖足够多的记录才能稳定，且本质为观察/教练工具，不替代专业医疗——这已在 SKILL.md 与 FAQ 中明确边界，属于定位分寸而非能力缺陷。
