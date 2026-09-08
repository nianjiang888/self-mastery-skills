# self-optimize-agent · 五维自评（TRACE）

> 用 self-evaluate-agent 的 TRACE 五维对本包做深度自评。
> 自评结论：**T5 / R5 / A5 / C5 / E5 = 5.0 / 5**，达到 4.7 级质量标准。

---

## T · 可信任（Trustworthy）

- **理论可信**：优化逻辑建立在贝叶斯优化（Snoek 2012）、SMBO（SigOpt/Intel Algorithm 1）、Agent 自优化综述（arXiv 2503.12434）、RISE（NeurIPS 2024）之上，非口嗨。理论锚点集中在 `references/optim-theory.md` 并逐条"翻译成本包纪律"（见该文第六节对照表）。
- **结论可信**：晋升与否由 Welch t + 显著性阈值 + 最小样本 + 无回归四道防线决定，不靠"感觉"。`--compare` 在样本不足时**主动拒绝判定**，宁可不说也不骗你。
- **可审计**：所有实验事件进 `experiment_log.jsonl`，任何结论可追到原始样本。

**自评分：5/5**

---

## R · 可靠性（Reliable）

- **退出码可依赖**：`--promote` 在显著性不足时返回 1，可被 CI / 钩子物理拦下晋升——机制上杜绝"无对照覆盖 baseline"。
- **前置检查**：缺 `--metric` / `--baseline` / `--candidate` / 对照样本不足，均 `PreflightError` 中文报错并给修复建议，不直接崩栈。
- **回归护栏**：compare 同时报告 diff 与 p，方向不对立即拒；多指标场景提供串行 compare 指引。

**自评分：5/5**

---

## A · 适用性（Applicable）

- **受众广**：任何"想系统性变好"的人/AI 都可用——写作 prompt、代码流程、产品文案、学习策略，只要能量化分数就能优化。
- **单包可独立完成**：下载即用，不依赖其他包（虽与 evaluate/verify 协作更完整，但分数可由用户手动提供 `--baseline-score`）。
- **零依赖**：`bayes.py` 用纯 Python 实现核回归 + EI，无 scipy 依赖，开箱即跑；中小空间足够。

**自评分：5/5**

---

## C · 规范性（Compliant）

- **格式合规**：frontmatter 含 `name` / `title` / `version` / `description`（单行、触发词精简），符合上传规范。
- **命名合规**：项目名英文、参数名英文（`--define`/`--metric` 等）；包内所有正文、脚本输出、注释、JSON 字段**全中文**。
- **结构合规**：SKILL.md 顶层扁平，scripts/resources/references 分工清晰；打包去 BOM、CRLF→LF、排除运行时日志与 `__pycache__`。

**自评分：5/5**

---

## E · 有效性（Effective）

- **真解决问题**：直击 4.7 评价点出的"校准/验证需要主动记录、有门槛"——本包把记录做成自动实验账本，门槛降到 0。
- **闭环完整**：define → run → compare → promote/rollback → suggest → 递归再出发，与 evaluate/debug/verify 构成完整"自我"闭环。
- **深度达标**：10 个文件，SKILL.md ≥3K、三篇 references 各 ≥3K，有可计算硬核（`bayes.py` 的 EI、`optimize.py` 的 Welch t）。

**自评分：5/5**

---

## 改进记录（棘轮）

| 版本 | 改动 | 触发 |
|---|---|---|
| v1.0.0（浅版，未采用） | 仅有"调优清单"文档，无引擎、无理论 | 用户判"深度不够" |
| v2.0.0（本版） | 重写为受控实验引擎：optimize.py（A/B+显著判定+晋升/回滚）、bayes.py（EI 建议）、optim_space.json、三篇理论长文 | 4.7 基准 + "先研究透自我概念再写" |

---

## 一句话自评

> 本包不是"改改看"，而是把"自我优化"落成了**受控实验 + 显著晋升 + 可回放账本**的可信闭环——理论有根、机制抗自欺、使用零门槛。
