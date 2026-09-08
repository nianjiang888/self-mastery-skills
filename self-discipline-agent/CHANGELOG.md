# self-discipline-agent 更新记录

## v2.0.0（2026-09-01）

- 初始发布。定位：自律承诺装置引擎——把靠意志硬扛变成可核查机制。
- 真引擎 `scripts/discipline.py` 五子命令：
  - `commit`：登记承诺（内容/期限/后果/监督人/类别，类别自动识别）。
  - `checkin`：到期前履约打卡。
  - `streak`：连续履约统计。
  - `audit`：违约检测（期限已过无打卡=违约），按类别暴露最易破类型，问责报告。
  - `report`：周期问责报告（履约率/各类别表现）。
- 实物证据：`.self-discipline/discipline-log.jsonl` + `audit-report.md` / `discipline-report.md`，可重跑。
- 理论根基：承诺装置(Thaler&Sunstein) / 预承诺(Schelling) / 实施意图(Gollwitzer) / 自我损耗(Baumeister, 含复制争议诚实标注) / 习惯回路(Duhigg) / 透明助推(Sunstein)。
- 退出码：0 正常 / 1 需关注 / 4 系统性失守警报（同类≥2条全违约或履约率<30%）。
- 冒烟测试 `smoke_self_discipline.py` 13/13 PASS；修复单条违约误判为系统性失守的逻辑 bug。
- 版本号三处一致（SKILL.md / 引擎 EVENT_VERSION / 资源 version）。
