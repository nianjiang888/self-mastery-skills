# self-fitness-agent 导航

> 把"想动起来"变成可追踪、可坚持、不受伤的爬坡。记录每次训练 → 量化负荷与恢复 → 预警伤痛 → 给渐进计划。

## 30 秒上手

```bash
# 设目标（可选）
python scripts/fitness.py --data ./my_fit set --target_freq 4

# 记一次训练
python scripts/fitness.py --data ./my_fit log \
  --date 2026-09-01 --type_sub strength --duration 50 --rpe 7 \
  --sets 4 --reps 8 --weight 60 --parts 胸,三头 --sleep_prev 7 --sore 3

# 看趋势 / 风险 / 恢复 / 计划 / 报告
python scripts/fitness.py --data ./my_fit trend --days 28
python scripts/fitness.py --data ./my_fit risk  --days 28
python scripts/fitness.py --data ./my_fit recover
python scripts/fitness.py --data ./my_fit plan
python scripts/fitness.py --data ./my_fit report
```

数据落在 `--data`：`events.jsonl`（按 date 幂等覆盖）+ `profile.json` + `reports/fitness-<日期>.md`。纯本地、可长期追踪、重跑一致。

## 文件导航

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 技能定义、主动触发、理论地图、快速上手 |
| `scripts/fitness.py` | 真引擎（6 子命令 + set，纯标准库、确定性） |
| `resources/fitness-guidelines.json` | 分目标训练/营养/热身推荐，带出处 |
| `resources/training-models.json` | ACWR/单调性/周期化/心率区间模型库 |
| `resources/fitness-domains.json` | 指标定义与计算口径 |
| `references/*.md` | 13 篇方法论长文，均带年份/期刊出处 |
| `FAQ.md` | 14 个常见问题 |
| `SELF_EVAL.md` | TRACE 五维自评 |
| `CHANGELOG.md` | 版本记录 |
| `examples/sample-fitness-log.md` | 完整两周记录与输出样例 |

## 子命令速查

| 命令 | 作用 | 关键参数 | 退出码 |
|---|---|---|---|
| `set` | 设个人目标 | --target_freq | 0 |
| `log` | 记一次训练 | --date --type_sub --duration --rpe --sets --reps --weight --parts --sleep_prev --sore | 0 |
| `trend` | 负荷/频次/强度趋势 | --days（默认 28） | 0 |
| `recover` | 恢复评分（0-100） | --days（默认 14） | 0 |
| `risk` | 伤痛风险扫描 | --days（默认 28） | 高严重度→1，否则 0 |
| `plan` | 下周最该改的一个 | --days（默认 28） | 0 |
| `report` | 完整报告 | --days（默认 28） | 有弱项→1，否则 0 |

## 退出码

- `0` 正常
- `1` 需关注（弱项 / 高风险）
- `2` 未知子命令
- `4` 参数错误 / 引擎异常

## 边界声明

- 前哨工具，不做医疗诊断；伤痛持续/关节锐痛/长期疲劳请走正规运动医学。
- 训练压力分为工程近似，**看重趋势与比值（ACWR、单调性）**，绝对值不对外承诺。
- 与 `self-sleep-agent` 互补：睡眠是恢复的母舰，两个 Agent 的数据可互相印证。
