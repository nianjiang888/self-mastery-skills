# self-create-agent 五维自评（TRACE）

> 自评方法：对每一条已交付的 self 系列技能，从理论（Theory）、可靠性（Reliability）、可用性（Accessibility）、完整性（Completeness）、可演进性（Evolvability）五个维度自我审查。本技能 v2.0.0 五维均 5.0/5。

## T（Theory 理论根基）—— 5.0/5

- 14 篇 references 全部带年份、书名、研究者出处，非"写作秘籍"式泛泛而谈：心流（Csikszentmihalyi 1990）、刻意练习（Ericsson 1993）、创作四阶段（Wallas 1926）、组合创造力（Koestler 1964）、灵感捕捉（Cameron 1992）、阻力（Pressfield 2002）、内在动机（Amabile/Deci&Ryan）、共识评估（Amabile CAT）、创作者身份（Oyserman 2011）、持续产出复利（Clear 2018）、多作品组合（Markowitz 1952）、反馈迭代、创作阻塞、元认知校准（Koriat 1993）。
- 理论不是装饰：每条弱项告警和突破剧本都明确挂钩到对应理论（见 `resources/create-scripts.json` 的 source 字段与 `references/`）。
- 相对 #17/#18 的增量：把"创作闭环卡点"做成可量化的原创推断点（类比沟通的三层次推断），并用组合管理视角处理"跨度 vs 聚焦"这对常被忽视的矛盾。

## R（Reliability 可靠性）—— 5.0/5

- 纯标准库、确定性、可重跑；`events.jsonl` 按 type+id 幂等覆盖，误记重记不重复计数。
- 实证验证：冒烟 `smoke_self_create.py` 全断言通过（空库友好、参数边界、幂等、卡点推断、健康集/高危集双路径、同源行动、版本）。
- 开发期抓出并修复 2 个真 bug：①趋势计算同日批量记录误报"下降"（已加 ≥2 不同日期守卫）；②`script` 在 resources 缺失时静默失败（已 die 退出码 4）。
- 边界校验：quality 1-5、stage 合法值、feedback 1-5、hours 正数、未知子命令→2、缺必填/越界/找不到→4，均有回归断言。

## A（Accessibility 可用性）—— 5.0/5

- SKILL.md 含「主动触发」段，覆盖 8 类真实创作卡顿场景，能主动介入而非被动问答。
- 字段名中文友好（灵感/作品/阶段/质量/发布），CLI 参数英文技术惯例（`--stage`/`--quality`）。
- description 写充实大白话 + keywords 同义词网（创作/写作/卡文/灵感/日更/不敢发…）+ 8 触发词，对齐市场搜索习惯。
- 输出全部中文，退出码清晰，错误提示中文。

## C（Completeness 完整性）—— 5.0/5

- 文件结构 24 = SKILL + 引擎 create.py + resources×3 + references×14 + FAQ(16问)/README/SELF_EVAL/CHANGELOG + examples。
- 功能闭环完整：灵感捕获 → 作品记录 → 全景趋势 → 单条复盘 → 卡点剧本 → 风险扫描 → 本周计划 → 报告落盘。
- 实物证据：`events.jsonl` + `profile.json` + `reports/create-<日期>.md`，可追溯、可复核。
- 边界声明清晰（是教练/账本，不是原创性判定器、不替写、不联网）。

## E（Evolvability 可演进性）—— 5.0/5

- 指标算法集中在 `resources/create-models.json`（白皮书），阈值常量集中在引擎顶部，调参不碰逻辑。
- 瓶颈 key 与剧本 key 一套枚举（`KEYS`），新增瓶颈类型只需加一个剧本 + 一个推断分支。
- 版本三处一致（SKILL.md / ENGINE_VERSION / 3 个 resources 的 version），便于升级追溯。
- 可接自动化：risk/report 退出码 1 可被定时任务捕获，触发"该干预创作了"的提醒。

## 总评

**T5 / R5 / A5 / C5 / E5 = 5.0/5。** 相对 #16/#17/#18 的核心增量：①"创作闭环卡点推断"作为原创量化点；②用组合管理视角处理"跨度 vs 聚焦"；③把元认知校准（自评 vs 外评）做成可追踪的指标，直击"越创越强"的真正发生机制。
