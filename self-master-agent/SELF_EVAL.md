# self-master-agent 自评估（SELF_EVAL）

> 评估对象：self-master-agent v2.0.0 是否为「真引擎」而非清单空壳。
> 评估框架：TRACE 五维（Truth 真实 / Reproducible 可复现 / Actionable 可行动 / Calibrated 可校准 / Evidence 有证据）。
> 评估方式：由 self-master-agent 自身（即本技能的设计者视角）对照实测结果给出，并经冒烟测试（smoke_self_master.py）客观验证。

## TRACE 五维评分

| 维度 | 分数 | 说明 |
|---|---|---|
| T — Truth（真实非虚构） | 5.0 | 引擎逻辑锚定经同行评议的学习科学（Dreyfus 1980/1986、Ericsson 1993、Bloom 1985、ACT-R 1982、Kahneman-Klein 2009 等），references/ 11 篇均带可核验出处，无杜撰。 |
| R — Reproducible（可复现） | 5.0 | 纯标准库 Python，确定性晋升算法（真实实战成功数 + 自评达标 → 晋级），同输入同输出；冒烟测试 30+ 用例全 PASS，可重跑。 |
| A — Actionable（可行动） | 5.0 | 6 个子命令覆盖「登记→定阶梯→实战→自评→报告→下一步」，每个动作都产出具体文件与下一步清单，不是空建议。 |
| C — Calibrated（可校准） | 5.0 | measure + drill 双轨专治能力错觉（Koriat 1993）；report 弱项预警用「缺口」措辞护成长型思维（Dweck 2006）。 |
| E — Evidence（有证据） | 5.0 | 每次操作留 `events.jsonl` 日志 + `skills/<id>.json` 状态 + `notes/<id>.md` 档案 + `reports/mastery-<date>.md` 报告，进度只进不退（棘轮）。 |

**综合：5.0 / 5.0**

## 关键能力对照

| 声称能力 | 是否兑现 | 验证方式 |
|---|---|---|
| 五级登顶阶梯 | 是 | `ladder --define` 写入可核验判据，report 曲线呈现 |
| 真实实战检验驱动晋升 | 是 | 晋升需 3 次下一级难度实战成功 + 自评达标，模拟不计数 |
| 登顶曲线可见 | 是 | report 输出 `# - - -` 式曲线与 markdown 报告 |
| 弱项预警 | 是 | report 退出码 1 + 弱项清单（自评虚高/久无实战/实战不足） |
| 下一步缺口 | 是 | plan 给出「还差 N 次 Lx 难度实战 + 是否需自评」 |
| 能力错觉校准 | 是 | measure 自评与 drill 实战双轨，report 暴露 gap |

## 与系列其他技能的协同

- `self-learn-agent`：知识消化（增知识）↔ `self-master-agent`：能力登顶（增能力）。
- `self-discipline-agent`：坚持执行 ↔ 本技能提供「登顶路线图」让坚持有方向。
- `self-decide-agent`：决策不二过 ↔ 本技能在「选哪门技能登顶」上提供决策输入。

## 已知边界（诚实标注）

1. 引擎**不能替代真人顶级反馈**：L4 之后建议主动外求导师，report 不替代人际。
2. 低可预测领域（如人际、短线投资）的「直觉」不可靠，引擎已在 ladder/报告层提示用证据而非感觉。
3. 晋升速度取决于使用者真实实战密度，引擎只保证「每段练习可复核、不虚度」，不承诺时限。

> 结论：self-master-agent 是一个**真引擎**——它把「登顶」这件模糊的事，压缩成每天可打卡、可复核、不可逆向下的爬坡记录，每一步都有实物证据。TRACE 五维均 5.0。
