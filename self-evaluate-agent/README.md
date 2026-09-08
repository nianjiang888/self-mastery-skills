# self-evaluate-agent · 说明

> 元认知评估与反思引擎（Reflexion 多轮闭环 + 元认知校准）。
> 属于 `self-*` 系列（20 个 Agent，名称全英文，品质同一标尺）：把任意产出送进
> "打分→反思→重写→重评→收敛"，并量化"你以为你知道"和"实际对不对"的差距。

## 文件导航

| 文件 | 是什么 |
|---|---|
| `SKILL.md` | Agent 规范：定位、理论根基、主动触发、怎么用、边界、红线 |
| `scripts/evaluate.py` | 评估与反思引擎：机器预检 / 多轮提交 / 收敛分析 / 趋势 / 评分标准管理（preflight + 中文报错 + 退出码） |
| `scripts/calibrate.py` | 元认知校准：Brier Score / 分桶校准 / 过度自信指数 OCI（你的"自知之明账本"） |
| `resources/rubrics.json` | 七套评分标准：TRACE(默认) / WRITING / CODE / PRODUCT / SELF_AGENT / REASONING / SAFETY，含锚点与探针钩子 |
| `references/reflexion-method.md` | 深度长文：Reflexion 框架（NeurIPS 2023）+ 本包如何跑一轮 |
| `references/metacognition.md` | 深度长文：元认知理论（Flavell/Nelson&Narens）+ Brier/OCI 校准 |
| `references/rubric-design.md` | 深度长文：评分标准设计学（维度≤6 / 可测 / 锚点 / 加权 / 校准反模式） |
| `FAQ.md` | 场景→应对 映射 + 元认知问答 |
| `SELF_EVAL.md` | 本包用 TRACE 五维深度自评的记录（证明它达标） |
| `eval_log.jsonl` | 你的质量日记（首次 `--submit` 时生成） |
| `calibration_log.jsonl` | 你的自知之明账本（首次 `--record` 时生成） |

## 快速上手：跑一轮 Reflexion

```bash
# 0) 机器客观预检（盲点提示，不替代判决）
python scripts/evaluate.py --probe 草稿.md

# 1) 第 1 轮：打分 + 证据 + 反思 + 改进
python scripts/evaluate.py --submit 草稿.md \
  --scores "T:4,R:3,A:5,C:4,E:3" \
  --evidence "R:3-第2段未处理空输入;C:4-缺错误提示;E:3-未说明适用场景" \
  --reflection "根因：先写主流程，边界和失败路径留到最后就忘了" \
  --fix "下一轮先写空输入与异常分支" --round 1

# 2) 改写后第 2 轮
python scripts/evaluate.py --submit 草稿.md --scores "T:5,R:5,A:5,C:5,E:4" \
  --evidence "R:5-已加空输入分支;C:5-统一错误格式" --reflection "边界已补" --fix "" --round 2

# 3) 收敛报告与趋势
python scripts/evaluate.py --converge
python scripts/evaluate.py --report
```

## 快速上手：元认知校准

```bash
python scripts/calibrate.py --record "这段代码无越界" 0.9 0
python scripts/calibrate.py --record "函数返回非空" 0.7 1
python scripts/calibrate.py --analyze --bins 10
```

## evaluate.py 命令

| 命令 | 作用 |
|---|---|
| `--probe <文件\|文本> [--rubric 名]` | 机器客观预检，标风险点（仅供参考） |
| `--submit <文件\|文本> --scores "维:分,..." [--evidence "维:出处;..."] [--reflection 文] [--fix 文] [--round N] [--rubric 名]` | 提交一轮评估 |
| `--converge [--rubric 名]` | 收敛分析：斜率 / 收敛检测 / 卡住维度 / 反思质量 |
| `--report [--dim T]` | 评分趋势（总览或单维度） |
| `--init-rubric <名称>` / `--calibrate <好> <差>` / `--show-rubric [名称]` | 评分标准管理 |

## calibrate.py 命令

| 命令 | 作用 |
|---|---|
| `--record "<主张>" <置信度0-1> <实际对错0/1>` | 记一条"我以为 / 实际" |
| `--analyze [--bins 10]` | Brier / 分桶校准 / OCI / 最危险区间 |
| `--history` | 历史校准样本 |

## 退出码

`evaluate.py`：`0` 正常 · `1` 参数非法 / 目标为空 / 低分缺证据 · `2` 评分标准缺失或非法 · `3` 还没有日志 / 意外错误
`calibrate.py`：`0` 正常 · `1` 参数非法 · `3` 样本不足 / 意外错误
