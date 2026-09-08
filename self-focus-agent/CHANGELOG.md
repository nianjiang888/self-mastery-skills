# CHANGELOG · self-focus-agent

## v2.0.0 （2026-09-01）

初始发布（self 系列第 11 条）。

- **真引擎 `scripts/focus.py`**：5 子命令 `plan` / `log` / `interrupt` / `measure` / `report`；确定性、可重跑、留实物证据。
- **退出码 0/1/4**：打断过多或时长不足→1；长期日均专注不足→4。
- **资源 `resources/focus-baselines.json`**：阈值 + 干扰来源归一词典（含 version 字段）。
- **理论扎实**：`references/focus-theory.md`（8 条理论，均带可核验出处与争议标注）+ `references/focus-method.md`（防干扰方法论，把理论变机制）。
- **冒烟 17/17 PASS**：`E:/Skills/_tools/smoke_self_focus.py`，覆盖各退出码路径与来源归一、jsonl 累积。
- **诚实边界**：不引用无出处的网络百分比；基线为启发式非医学标准；深度工作有特权属性。
