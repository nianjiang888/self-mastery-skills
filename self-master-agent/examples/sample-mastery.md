# 样例：一轮「Python 性能优化」登顶记录

> 本样例展示 self-master-agent 在真实使用下的产物形态。数据目录 `./demo_master`。

## 1. 登记技能（add）

```
python scripts/master.py --data ./demo_master add \
    --name "Python 性能优化" --goal "把慢接口提速10倍" --target 5 --level 1
```
产出：`skills/#1.json`（目标 L5，当前 L1）。

## 2. 定义登顶阶梯（ladder）

```
python scripts/master.py --data ./demo_master ladder --id "#1" \
    --define "L1:能读懂火焰图;L2:能定位一类瓶颈;L3:能稳定提速2倍;L4:能设计缓存策略;L5:能定义团队性能规范"
```

## 3. 真实实战（drill，带证据）

```
python scripts/master.py --data ./demo_master drill --id "#1" \
    --task "优化导出脚本" --difficulty 2 --result success --confidence 4 --evidence "export_v2.py"
python scripts/master.py --data ./demo_master drill --id "#1" \
    --task "定位 N+1 查询" --difficulty 2 --result success --confidence 4 --evidence "query_fix.py"
python scripts/master.py --data ./demo_master drill --id "#1" \
    --task "缓存热点路径" --difficulty 2 --result success --confidence 5 --evidence "cache_layer.py"
```

## 4. 自评校准（measure）

```
python scripts/master.py --data ./demo_master measure --id "#1" --score 2 --note "能定位一类瓶颈了"
```
→ 因已有 3 次 L2 实战成功 + 自评≥2，**自动晋升至 L2 胜任**。

## 5. 报告与下一步（report / plan）

```
python scripts/master.py --data ./demo_master report
python scripts/master.py --data ./demo_master plan --id "#1"
```

`report` 产出（节选）：

```
| 技能 | 当前层 | 掌握度 | 目标 | 状态 |
|---|---|---|---|---|
| #1 Python 性能优化 | L2 胜任 | 41.7% | L5 | 爬坡中 |

## 登顶曲线
- #1 Python 性能优化 `## ---`

## 弱项预警（需关注）
- #1 Python 性能优化：下一级实战成功仅 0/3 次
```

`plan` 产出（节选）：

```
下一步冲刺 L3 熟练 的缺口：
  - 还需 3 次『L3 难度』实战成功（真实场景，非模拟）
  - 自评已达标 ✓
  - L3 判据：能稳定提速2倍
```

## 6. 实物证据清单（棘轮，只进不退）

- `events.jsonl`：add / ladder_set / drill×3 / measure / promote / report 全事件。
- `skills/#1.json`：阶梯、实战、自评、当前层、晋升时间戳。
- `notes/#1.md`：技能档案（阶梯 + 实战表 + 自评表 + 掌握度）。
- `reports/mastery-<date>.md`：掌握度报告 + 登顶曲线 + 弱项预警。

> 可见产出：每一次真实实战都被记录、被校准、被推着向上爬；`report` 的登顶曲线让「十年登顶」的长期复利，变成每周可观测的进度条。
