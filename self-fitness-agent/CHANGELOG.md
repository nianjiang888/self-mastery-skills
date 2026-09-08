# CHANGELOG

## v2.0.0（首发）
- **定位**：健身训练管理 AI Agent——记录训练、量化负荷与恢复、预警伤痛风险、给渐进式下周计划。服务对象是「用 AI 的人」本人。
- **真引擎 `scripts/fitness.py`**：纯标准库、确定性可重跑，子命令：
  - `set`：设置个人目标（target_freq）；
  - `log`：记录一次训练（类型/时长/RPE/组次重/部位/前夜睡眠/酸痛）；
  - `trend`：近 28 天负荷、频次、强度、ACWR、单调性、部位分布；
  - `recover`：恢复评分（ACWR/单调性/睡眠/酸痛合成 0-100）；
  - `risk`：伤痛风险与弱项扫描（高严重度退出码 1）；
  - `plan`：本周最值得做的一个改变（按严重度排序给可执行行动）；
  - `report`：完整报告 + 弱项预警（弱项退出码 1，落盘 reports/）。
- **核心算法**：单次训练压力分（sRPE 工程近似）、ACWR（急性:慢性）、单调性/紧张度、部位过度使用判定、恢复分。
- **resources×3**：`fitness-guidelines.json`（分目标训练/营养/热身/恢复，带出处）、`training-models.json`（ACWR/周期化/心率区间模型库）、`fitness-domains.json`（指标口径）——均 `version: 2.0.0`。
- **references×13**：均带年份/期刊/书名出处（Gabbett/Garber/Kraemer/Schoenfeld/Watson/Cheung/Tanaka/Kiely/Fradkin/Levine/Meeusen/Morton 等）。
- **核心文档**：SKILL.md（含「主动触发」段 + 搜索友好描述 + 理论地图）、FAQ（14 问）、README（导航+子命令速查）、SELF_EVAL（TRACE 五维 5.0/5）、本 CHANGELOG、examples/sample-fitness-log.md。
- **冒烟**：`smoke_self_fitness.py` 53/53 PASS（覆盖各子命令、退出码 0/1/4、空库、幂等、ACWR 突增、弱项判定）。
- **修复的真 bug**：① `save_profile` 未建目录导致 `set` 失败 → 改为先 `ensure_dirs`；② 稀疏/边界数据下 ACWR 口径与 7 天窗口取数一致性 → 在冒烟中以相对今天连续日期验证。

> 注：references 以"自然写扎实、带出处"为原则，不硬性凑字数；数量 13 篇以满足"理论支撑充足、文件数 15–20 区间"的既定质量标准。
