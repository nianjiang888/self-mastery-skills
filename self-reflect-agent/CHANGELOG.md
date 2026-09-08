# self-reflect-agent 更新记录

## v2.0.0（2026-09-01）

- 初始发布。定位：日三省——洞察日志 + 模式识别，看见思维惯性与盲点。
- 真引擎 `scripts/reflect.py` 六子命令：
  - `log`：记录反省，自动抽标签（中文词库 + 拉丁词 + 显式）、自动识别情绪。
  - `pattern`：跨时间惯性识别（同标签跨 ≥N 天），破坏性惯性退出 1。
  - `claim`：登记自称价值/待改行为，去重。
  - `blindspot`：言行对照，系统性背离退出 4（双环警报）。
  - `aar`：美国陆军四问复盘模板。
  - `report`：周期趋势报告。
- 实物证据：`.self-reflect/reflect-log.jsonl`、`claims.json` 及四份 markdown 产物，可重跑。
- 理论根基：Schön 反思实践 / Argyris 单双环 / Gibbs / Brookfield 四透镜 / AAR / Dweck 成长型 / Flavell 元认知。
- 与 self-evaluate-agent 明确分工：evaluate 评「物」，reflect 省「己」。
- 交付质量：冒烟测试 15/15 PASS；版本号三处一致（SKILL.md / 引擎 EVENT_VERSION / 资源 version）。
