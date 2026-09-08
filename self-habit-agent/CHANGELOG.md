# CHANGELOG · self-habit-agent

## v2.0.0 （2026-09-01）

- 初始发布（self 系列第 10 条）。
- 真引擎 `scripts/habit.py`：5 子命令 `define` / `checkin` / `streak` / `lapse` / `report`。
- 习惯叠加三件套（锚点+新行为+提示线索）→ 自动生成叠加公式。
- 连击算法：连续 +1、同日去重、隔天清零但保留最长连击；当前连击仅在今天/昨天打卡时存活。
- 断签分级：中断(1–6 天, 退出码 1) / 长期未养成(≥7 天, 退出码 4)。
- 养成目标默认 66 天（Lally et al. 2009 中位，区间 18–254），进度条标注区间防焦虑。
- 断签≥7 天给微习惯降级重启建议。
- 实物证据：`.self-habit/habit-log.jsonl` + `habit-report.md`。
- 文件数 9（刻意不套固定模板）：SKILL + 引擎 + resources + 2 references + FAQ + README + SELF_EVAL + CHANGELOG。
- 冒烟 `smoke_self_habit.py` 19/19 PASS。
