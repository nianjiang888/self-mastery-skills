# self-decide-agent 使用指南

> 决策日志与回放评分引擎。把「做决定」从口号变成可复盘的数据闭环。

## 文件结构

```text
self-decide-agent/
├── SKILL.md                          # 总说明、主动触发、理论地图
├── scripts/decide.py                 # 真引擎（7 子命令）
├── resources/
│   ├── biases.json                   # 偏差库（13 条，含 version 2.0.0）
│   ├── decision-frameworks.json      # 框架库（12 个，含 version 2.0.0）
│   └── decision-prompts.json         # 三阶段自问清单（含 version 2.0.0）
├── references/                       # 10 篇理论长文（均带出处）
│   ├── decide-theory.md              # 总论 + System 1/2 + 闭环
│   ├── reversible-framework.md       # 单向门/双向门
│   ├── pre-mortem-method.md          # 事前验尸
│   ├── second-order-thinking.md      # 二阶思考
│   ├── decision-biases-catalog.md   # 13 偏差详解
│   ├── regret-minimization.md        # 后悔最小化 + 时序错位
│   ├── cynefin-ooda.md               # Cynefin + OODA
│   ├── 10-10-10-method.md            # 10-10-10 三时窗
│   ├── external-view-planning-fallacy.md  # 外部视角/计划谬误
│   └── real-options-flexibility.md   # 实物期权/灵活性
├── examples/
│   └── sample-decision-log.md        # 可重跑示例轨迹
├── FAQ.md  SELF_EVAL.md  CHANGELOG.md
```

## 快速上手

```bash
# 0) 先看看有哪些框架可用
python scripts/decide.py frameworks
python scripts/decide.py frameworks --id pre_mortem

# 1) 事前：假设已经失败，逼出盲点
python scripts/decide.py premortem --context "是否接受A公司offer" --reversibility irreversible

# 2) 当下：锁定决策（含偏差预检 + 框架标注）
python scripts/decide.py log --context "投资怕亏本" \
    --options "持有;卖出" --chosen "持有" --expected "保住本金" \
    --reversibility reversible --framework loss_aversion
#   → 检测到「损失厌恶」偏差

# 3) 事后：回放打分（可纠正可逆性误判）
python scripts/decide.py replay --id d1 --actual "其实还能反悔" \
    --score 60 --regret 30 --reversibility reversible
#   → 原 irreversible 被纠正，标记「可逆性误判」

# 4) 模式：识别反复偏差
python scripts/decide.py bias        # 反复偏差 → 退出 1

# 5) 报告：聚合误判率 + 常犯偏差 + 后悔最小化
python scripts/decide.py report      # 重大不可逆误判≥2 → 退出 4
```

## 退出码

| 码 | 触发条件 |
|---|---|
| `0` | 无重大不可逆误判、误判率 < 0.5、无反复偏差 |
| `1` | 存在 1 次重大不可逆误判，或误判率 ≥ 0.5，或存在反复偏差 |
| `4` | 重大不可逆误判 ≥ 2 次（不可逆决策多次严重误判） |

## 实物证据（4.8 基准：留可重跑文件）

- `decision-log.jsonl`：每条决策一行纯数据，任意时刻重跑 `bias`/`report` 结论一致。
- `replay-<id>.md` / `bias-report.md` / `decision-report.md` / `premortem-<slug>.md`：各命令生成的可复核 markdown。

## 版本

- 包版本：`2.0.0`
- 三处版本一致：`SKILL.md` frontmatter / 引擎 `EVENT_VERSION` / `resources/*.json` 的 `version` 字段
- 3 处 resources 均含 `version: "2.0.0"`
