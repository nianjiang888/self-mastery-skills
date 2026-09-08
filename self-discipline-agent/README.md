# self-discipline-agent 导航

AI 自律承诺装置引擎：登记承诺 → 到期打卡履约 → 自动违约检测 → 问责报告暴露最易破类型。

## 文件结构

```
self-discipline-agent/
├── SKILL.md                      # 总说明、理论根基、命令、主动触发、使用边界
├── scripts/
│   └── discipline.py             # 真引擎：commit/checkin/streak/audit/report 五子命令
├── resources/
│   └── commitment-prompts.json   # 承诺装置提问库（if-then / 装置类型 / 问责话术）
├── references/
│   ├── discipline-theory.md      # 理论串讲：承诺装置/预承诺/实施意图/自我损耗(争议标注)
│   └── accountability-method.md  # 问责机制与违约判定算法
├── FAQ.md                        # 常见问题
├── README.md                     # 本文件
├── SELF_EVAL.md                  # 五维自评（TRACE 5.0/5）
└── CHANGELOG.md                  # 版本记录
```

## 快速开始

```bash
python scripts/discipline.py commit --content "本周戒烟" --deadline 2099-01-01 --stake "违约发红包200" --partner "老婆"
python scripts/discipline.py checkin --id c1
python scripts/discipline.py audit
python scripts/discipline.py report
```

## 命令一览

| 子命令 | 作用 | 关键产物 |
|---|---|---|
| `commit` | 登记承诺（后果/监督人/类别） | `discipline-log.jsonl` |
| `checkin` | 履约打卡 | 同上 |
| `streak` | 连续履约统计 | 终端输出 |
| `audit` | 违约检测 + 问责报告 | `audit-report.md` |
| `report` | 周期问责报告 | `discipline-report.md` |

退出码：`0` 正常 · `1` 需关注 · `4` 系统性失守警报。

## 相关

- `self-habit-agent/`：长线习惯养成（日日做），本引擎管单次承诺问责，二者互补。
- 冒烟测试：`../_tools/smoke_self_discipline.py`（13 用例，全 PASS）。
