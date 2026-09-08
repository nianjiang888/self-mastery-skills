# self-reflect-agent 导航

AI 日三省引擎：记录反省 → 跨时间识别思维惯性 → 对照自称价值探测言行盲点 → 四问复盘推向双环学习。

## 文件结构

```
self-reflect-agent/
├── SKILL.md                      # 总说明、理论根基、命令、主动触发、使用边界
├── scripts/
│   └── reflect.py                # 真引擎：log/pattern/claim/blindspot/aar/report 六子命令
├── resources/
│   └── reflect-prompts.json      # 六框架反思提问库（Schön/Argyris/Gibbs/Brookfield/AAR/Dweck）
├── references/
│   ├── reflect-theory.md         # 理论串讲：七条研究传统如何落成代码
│   └── pattern-method.md         # 模式识别与盲点探测的方法论与算法
├── FAQ.md                        # 常见问题
├── README.md                     # 本文件
├── SELF_EVAL.md                  # 五维自评（TRACE 5.0/5）
└── CHANGELOG.md                  # 版本记录
```

## 快速开始

```bash
# 记录今天的受挫
python scripts/reflect.py log --situation "项目延期" --reaction "我对同事发火" --outcome "关系僵"

# 登记自称、查言行 gap
python scripts/reflect.py claim --kind value --text "情绪管理"
python scripts/reflect.py blindspot

# 复盘与周趋势
python scripts/reflect.py aar
python scripts/reflect.py pattern --min-days 2
python scripts/reflect.py report
```

## 命令一览

| 子命令 | 作用 | 关键产物 |
|---|---|---|
| `log` | 记录一条反省 | `reflect-log.jsonl` |
| `pattern` | 跨时间惯性识别 | `pattern-report.md` |
| `claim` | 登记自称价值/待改 | `claims.json` |
| `blindspot` | 言行盲点比对 | `blindspot-report.md` |
| `aar` | 四问复盘模板 | `aar-<id>.md` |
| `report` | 周期趋势报告 | `reflect-report.md` |

退出码：`0` 正常 · `1` 需关注模式 · `4` 双环警报。

## 相关

- `self-evaluate-agent/`：单条产出评分闭环（评「物」），本引擎评「己」，二者互补。
- 冒烟测试：`../_tools/smoke_self_reflect.py`（15 用例，全 PASS）。
