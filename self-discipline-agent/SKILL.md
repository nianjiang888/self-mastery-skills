---
name: self-discipline-agent
display_name: 自律承诺装置
version: 2.0.0
description: AI 自律承诺装置引擎。登记承诺（后果/监督人/类别）+ 到期打卡履约 + 自动违约检测 + 问责报告暴露最易破类型，把靠意志硬扛变成可核查机制。与 self-habit（养成就不丢）互补——本引擎管「单次承诺的问责」。
license: MIT
---

# self-discipline-agent · 自律承诺装置引擎

把「做/不做某事」从靠意志硬扛，变成**可核查的机制**：登记承诺 → 到期前打卡履约 → 系统自动检测违约 → 问责报告暴露你**最易破的承诺类型**。核心思想：别依赖会耗尽的意志，改用承诺装置（押金 / 监督人 / 环境改造）。

## 与 self-habit-agent 的区别（重要）

两者都管「自律」，职责不重叠：

- **self-habit-agent**：养成长线习惯（习惯叠加 + 每日打卡 + streak），关注「养成就不丢」。
- **self-discipline-agent**：管单次承诺的问责（有期限、有后果、有监督人），关注「这条承诺到底履约没」。

一句话：habit 管「日日做」，discipline 管「这条承诺算数不算数」。可单独用，也可配合——先 discipline 守住关键承诺，再 habit 把好事变日常。

## 理论根基

| 理论 | 提出者 | 落地位置 |
|---|---|---|
| 承诺装置（助推） | Thaler & Sunstein 2008 | `commit` 强制写后果/监督人 |
| 预承诺 | Schelling 1960 | `--deadline` + 打卡 + 违约判定 |
| 实施意图 if-then | Gollwitzer 1999 | `resources/` 预案模板 |
| 自我损耗（含争议标注） | Baumeister 1998 | 不依赖意志，改外部装置 |
| 习惯回路 | Duhigg 2012 | 按类别暴露最易破回路 |
| 透明助推 | Sunstein 2014 | 后果/监督人由用户自定 |

详见 `references/discipline-theory.md`（理论串讲）与 `references/accountability-method.md`（问责算法）。

## 主动触发（本引擎会自己干活）

满足以下情形时**主动**启动，而非等用户问：

- 用户说「我要戒 X / 我决定每天做 Y / 这次一定要…」→ 主动建议 `commit` 并提醒加 `--stake` / `--partner`。
- 用户反复破同类承诺 → 主动跑 `audit`，点出最易破类型并建议升级装置。
- 周期到了（如周末）→ 主动 `report` 看履约率趋势。
- 用户只说「我要自律」却无具体承诺 → 主动用 if-then 模板帮其落成可核查承诺。

主动时遵循：先 `commit` 沉淀 → 视情况 `audit` 看违约 → 用提问库引导换更强装置，不替用户下决心。

## 命令说明（scripts/discipline.py）

```
discipline --store <目录> <子命令>

  commit   登记承诺：--content 内容 [--deadline YYYY-MM-DD] [--stake 后果] [--partner 监督人] [--category 类别]
  checkin  履约打卡：--id 承诺id
  streak   连续履约统计（当前连击 / 最长连击）
  audit    违约检测：期限已过且无打卡=违约 → 问责报告（按类别暴露最易破类型）
  report   周期问责报告（履约率 / 各类别表现）
```

退出码：`0` 正常 · `1` 需关注（有违约非系统）· `4` 系统性失守警报（某类 ≥2 条全违约或履约率<30%）。

## 实物证据（4.8 基准：留可重跑文件）

- `discipline-log.jsonl`：commit / checkin 事件流，纯数据，可任意重跑分析。
- `audit-report.md` / `discipline-report.md`：各命令生成的产物，可复核。

## 使用示例

```
# 1. 登记一条带装置的关键承诺
python scripts/discipline.py commit --content "本周戒烟" --deadline 2099-01-01 --stake "违约发红包200" --partner "老婆"
# 2. 到期前打卡履约
python scripts/discipline.py checkin --id c1
# 3. 看违约与最易破类型
python scripts/discipline.py audit
# 4. 周末看趋势
python scripts/discipline.py report
```

## 使用边界（诚实）

- 打卡是「自报」行为，引擎不验证你**真的**做了；重要承诺请用 `--partner` 让监督人交叉验证。
- 类别识别靠关键词，生僻表达可能归「未分类」，用 `--category` 补即可。
- 履约率随样本增多才可信，一两条记录下的百分比意义有限。
- 自我损耗理论存在复制争议，本引擎因此不把「靠意志」当主策略，已诚实标注。
- 所有数据留在你指定的 `--store`，不外传、不联网。
