# self-create-agent 使用导航

> 创作产出 AI Agent：帮你持续产出、越创越强。把"想创作却卡住"变成可记录、可计算、可复核的指标。

## 30 秒上手

```bash
python scripts/create.py --data ./my_create set --name 年爷 --domain 写作 --focus 网文
python scripts/create.py --data ./my_create idea --content "穿越者开现代火锅店" --theme 网文 --source 洗澡
python scripts/create.py --data ./my_create work --title "第一章" --theme 网文 --stage 发布 --quality 4 --hours 3
python scripts/create.py --data ./my_create trend
python scripts/create.py --data ./my_create risk
```

## 节奏建议

| 频率 | 动作 |
|---|---|
| 灵感一来 | `idea` 立刻记，别靠脑子记 |
| 完成一件作品 | `work` 记 stage/quality |
| 每周一次 | `trend` 看全景，`risk` 扫卡点 |
| 卡住时 | `plan` 拿本周唯一动作 + `script --key <瓶颈>` 拿剧本 |
| 每月一次 | `report` 出完整复盘报告 |

## 文件导航

| 文件 | 用途 |
|---|---|
| `SKILL.md` | 总说明、主动触发、理论地图 |
| `scripts/create.py` | 真引擎（8 子命令，纯标准库，确定性） |
| `resources/create-domains.json` | 字段 schema / 弱项规则 / 退出码 / 边界 |
| `resources/create-models.json` | 指标算法定义与阈值白皮书 |
| `resources/create-scripts.json` | 8 套瓶颈突破剧本（带出处） |
| `references/*.md` | 14 篇方法论长文（均带出处） |
| `FAQ.md` | 16 个常见问题 |
| `SELF_EVAL.md` | 五维自评（TRACE 5.0/5） |
| `CHANGELOG.md` | 版本与开发记录 |
| `examples/sample-create-log.md` | 端到端跑通示例 |

## 子命令速查

| 命令 | 必填 | 可选 |
|---|---|---|
| `set` | — | --name --domain --focus --goal --note |
| `idea` | --content | --theme --source --status(灵感/已启动/已转化) --date --id |
| `work` | --title --quality | --theme --stage(启动/完成/打磨/发布) --hours --source --feedback --date --id |
| `trend` / `risk` / `plan` / `report` | — | --days(默认30) |
| `review` | — | --id（留空复盘最近一件作品） |
| `script` | --key | — |

## 字段与量表

- **quality（质量）**：1=很糙 2=一般 3=还行 4=满意 5=很满意（自评，配合 feedback 校准）
- **stage（阶段）**：启动(开了头) < 完成(初稿) < 打磨(精修) < 发布(对外)
- **idea status（灵感状态）**：灵感 < 已启动 < 已转化(变成作品)
- **feedback（外部反馈）**：1-5，懂行人的独立评分

## 核心指标定义

| 指标 | 含义 |
|---|---|
| avg_quality | 窗口内作品质量均值 |
| quality_trend | 前半段 vs 后半段质量：上升/平稳/下降 |
| finish_rate | stage≥完成 占比（收尾能力） |
| polish_rate | stage≥打磨 占比 |
| ship_rate | stage==发布 占比（隐性天花板） |
| idea_redeem | 灵感转化为作品的比例（流动 vs 囤积） |
| freq_week | 每周产出件数（手感靠密度） |
| max_gap | 最长无产出天数（>14 高危） |
| distinct_themes / max_theme_share | 跨度与聚焦平衡 |
| bottleneck | 创作闭环卡点（本包原创量化点） |

## 退出码

| 码 | 含义 |
|---|---|
| 0 | 正常（无中/高严重度模式） |
| 1 | 存在中或高严重度模式（risk/report 触发） |
| 2 | 未知子命令 |
| 4 | 参数或数据不可用（缺必填/越界/找不到记录） |

## 边界

- 是创作教练与量化工具，不是原创性判定器，不替你写、不生成作品内容。
- 数据全部留本地（`events.jsonl` / `profile.json` / `reports/`），不上传、不联网。
