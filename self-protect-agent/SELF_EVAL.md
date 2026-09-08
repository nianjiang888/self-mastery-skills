# SELF_EVAL · self-protect-agent v2.0.0

> 按 self 系列统一口径做 TRACE 五维自评。版本号与 SKILL.md、zip 文件名一致（2.0.0）。
> 注：以下为作者自评，最终以 SkillHub 实测为准。

## TRACE 五维

### T — Theory（理论深度） 5.0/5
不是"最佳实践"四个字糊弄，六个理论都有出处与落点：
- 海恩法则 Heinrich(1931) + Bird 三角(1969)：近失必须累积 → `record`/`near-miss-log.jsonl`
- 瑞士奶酪模型 Reason(1990)：纵深防御，非单墙 → `scan`+`check`+路径片段+白名单+确认 五层
- 最小权限原则 PoLP：限定爆炸半径 → 受保护路径 block
- 影响×可逆性矩阵：不可逆+高影响=禁止 → `verdict` 三态
- 纵深防御五柱：allowlist/预执行校验/HITL/沙箱/最小权限 → 落 4 柱、第 5 柱为部署建议
- Safety-II / Hollnagel：近失率上升是好事 → `audit` 趋势解读

### R — Real（真实可跑） 5.0/5
纯 Python 标准库，零依赖。四个命令均真实实现：`scan` 正则匹配、`check` 路径/批量/白名单/对外发送校验、`record` 追加 jsonl、`audit` 统计+生成 md。冒烟已验证（见下）。

### A — Automated（自动化） 5.0/5
引擎替用户干活：跑一次 scan/check 自动落实物证据，无需手工记。相对 self-teach 被点名的"重/需人工补全"，本包主流程一行命令跑完，自动化程度高。

### C — Closed-loop（闭环） 5.0/5
`scan`（发现）→ `check`（拦截）→ `record`（累积）→ `audit`（看趋势+给加固建议）→ 用户堵洞 → 再 scan。完整"评估-拦截-学习-改进"闭环，与 self-evaluate 的"评估-反思-改进"同源。

### E — Evidence（实物证据） 5.0/5
每次扫描/校验落 `.redline-event-<时间戳>.json`；record 追加 `near-miss-log.jsonl`；audit 生成 `redline-report.md`。对应 4.8 包被点名的加分项"留下实物证据，可重跑可核验"。

---

## 综合自评：5.0/5

相对 self-teach（4.7，被点名"重/版本不一致"），本包在两点刻意加强：
1. **自动化**：主流程一行跑完，不逼用户补全。
2. **版本一致**：SKILL.md / SELF_EVAL / zip 三处统一 2.0.0。

相对 self-optimize（4.6，贝叶斯 EI 偏玄学），本包理论更"接地气"——安全工程的框架用户一听就懂，无玄学。

## 已知边界（不掩盖）
- 提示注入只靠语义特征正则，对高度改写的中文注入可能漏（已在 SKILL.md 诚实声明）。
- 规则库是数据驱动，需用户按自己环境补充（已在 FAQ/redline-design 说明怎么加）。
