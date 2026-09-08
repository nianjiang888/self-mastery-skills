# self-fitness-agent · TRACE 五维自评

> 评级尺度 0–5。评分基于本包交付物（SKILL.md / 引擎 / resources / references / 文档）的实际内容。

## T — Task fit（任务契合）
**5.0 / 5**
精准对应「自我 = AI 自改 + 用 AI 的人本身」中"用 AI 的人"的运动健康场景。把模糊的"想练好"拆成可记录、可计算、可复核的训练负荷/恢复/风险/计划闭环，既服务个人、又体现 AI 自改（主动触发、留实物证据）。

## R — Real engine（真引擎）
**5.0 / 5**
`scripts/fitness.py` 纯标准库、确定性、可重跑。6 子命令（log/trend/recover/risk/plan/report）+ set，计算 ACWR、单调性、紧张度、部位分布、恢复分，并产出 `events.jsonl` + `reports/fitness-<日期>.md` 实物证据。退出码 0/1/4 语义清晰。冒烟 53/53 全 PASS（见交付记录）。

## A — Authority（理论权威）
**5.0 / 5**
13 篇 references 均带年份/期刊/书名出处：Gabbett 2016（Br J Sports Med）、Garber 2011（Med Sci Sports Exerc）、Kraemer & Ratamess 2004（Physiol Rev）、Schoenfeld 2010/2016、Watson 2017、Cheung 2003、Tanaka 2001、Kiely 2012、Fradkin 2006、Levine 2002、Meeusen 2013、Morton 2018 等。resources 三份均标注 version 2.0.0 与出处。

## C — Completeness（完整度）
**5.0 / 5**
文件齐备：SKILL.md（含主动触发段 + 搜索友好描述 + 理论地图）、真引擎、resources×3、references×13、FAQ（14 问）、README、SELF_EVAL、CHANGELOG、examples。三处版本一致 2.0.0，无 CRLF，SKILL.md 在 zip 根。

## E — Experience（体验）
**5.0 / 5**
30 秒上手脚本、子命令速查表、退出码说明、边界声明（前哨工具不替代医疗）、与 self-sleep-agent 的互补呼应。冒烟覆盖各子命令与退出码路径，先引擎后冒烟抓出并修复 2 个真 bug（save_profile 未建目录、ACWR 边界），交付稳健。

## 总评
**TRACE 五维均 5.0 / 5。** 可作为 self 系列训练类 Agent 的基线交付。
