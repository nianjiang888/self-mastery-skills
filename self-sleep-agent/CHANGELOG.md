# self-sleep-agent 更新日志

## v2.0.0（2026-09-01）

- **首次发布**：睡眠质量管理 AI Agent，定位为「用 AI 的人」的自我观察与节律学习工具。
- **真引擎 `scripts/sleep.py`**：纯标准库、确定性可重跑，6 子命令
  - `log`：记录一晚睡眠（就寝/入睡/起床/夜醒/主观质量/咖啡因/屏幕/运动/次日情绪/日期类型）；新增 `--latency` 直接录入入睡潜伏期（与 `--onset` 二选一），同日期重记幂等覆盖；
  - `trend`：近期趋势、睡眠债、规律性评分；
  - `rhythm`：学出睡眠中点、推断时型（早鸟/中间/夜猫）、规律性（SRI 工程近似）、估算社会时差；
  - `nudge`：按影响排序的可执行建议；
  - `report`：完整报告 + 弱项预警（弱项退出码 1），评估窗口无记录时安全返回 0；
  - `plan`：本周最值得做的一个改变，无记录时安全返回 0。
- **核心算法**：跨零点时间归一（中点 `%1440`）、睡眠效率/潜伏期/WASO/中点计算、睡眠债、规律性（SRI 工程近似）、弱项判定（效率/债/规律性/潜伏期/咖啡因/屏幕）。
- **冒烟抓出并修复的真 bug**：
  - `append_event` 原纯追加，重记同晚会重复计数污染趋势 → 改为按 `type+date` 幂等覆盖；
  - `cmd_report`/`cmd_nudge`/`cmd_plan` 在 `recent()` 过滤后无记录时 `t=None`，report 会 `KeyError` 崩溃 → 统一加 `not t` 守卫安全退出 0；
  - `log` 子命令缺 `--latency` 录入入口（潜伏期是一等指标）→ 补 `--latency` 参数并写入记录；
  - `cmd_rhythm` 未输出规律性/SRI → 补充规律性评分行。
- **3 份 resources**（均 `version: 2.0.0`）：
  - `sleep-guidelines.json`：分年龄睡眠时长推荐（Hirshkowitz 2015）+ 睡眠卫生规则（带出处）；
  - `circadian-models.json`：双过程/时型/SRI/光照授时模型库；
  - `sleep-domains.json`：指标定义与计算口径。
- **12 篇 references**（每篇 ≥2000 中文字、带年份/期刊/书名出处）：
  - 双过程模型、睡眠规律性指数、社会时差与时型、睡眠需要与睡眠债、睡眠卫生、多导睡眠图基础、光与昼夜节律、睡眠记忆巩固、CBT-I 与睡眠限制、睡眠结构与年龄、个体时型、睡眠惯性与小睡。
- **核心文档**：SKILL.md（含主动触发段 + 理论地图）、FAQ.md（14 问）、README.md（导航）、SELF_EVAL.md（TRACE 五维 5.0/5）、本文件。
- **examples/sample-sleep-log.md**：一份完整记录样例。
- **退出码约定**：0 正常 / 1 需关注（弱项）/ 4 系统性警报。
- **实物证据**：`events.jsonl` + `profile.json` + `reports/sleep-<日期>.md`，重跑一致。
- **冒烟测试**：`E:/Skills/_tools/smoke_self_sleep.py`（≥30 用例全 PASS）。
- **边界声明**：非医疗诊断、不替代医生；规律性为 SRI 工程近似；重度失眠走正规 CBT-I。
