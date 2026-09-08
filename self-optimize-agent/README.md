# self-optimize-agent · 自述与导航

> 受控自我实验优化引擎。把评估分数当目标函数，跑 A/B，显著胜出才晋升 baseline。
> 项目名（self-optimize-agent）为英文品牌标识；以下所有说明与脚本输出**全中文**。

---

## 一、文件导航

```
self-optimize-agent/
├── SKILL.md                 # 引擎定义：自我优化本质、理论根基、主动触发、边界红线
├── scripts/
│   ├── optimize.py          # 受控实验引擎：define/run/compare/promote/rollback/report
│   └── bayes.py             # 贝叶斯式建议器：核回归代理 + Expected Improvement 推荐下个候选
├── resources/
│   └── optim_space.json     # 优化空间：可调旋钮、范围、方向、约束
├── references/
│   ├── optim-theory.md      # 理论：贝叶斯优化(Snoek2012)/SMBO/RISE/综述
│   ├── experiment-method.md # 方法：受控A/B、显著性、回归护栏、预算停止
│   └── promotion-culture.md # 文化：晋升门槛、实验账本、抗自欺、递归改进
├── FAQ.md                   # 场景与概念问答
├── README.md                # 本文件
└── SELF_EVAL.md             # 用 TRACE 五维对本包做深度自评
```

---

## 二、三句话理解它

1. **自我** = 不假外求地对自己做受控实验（评估分当目标函数）。
2. **纪律** = 对照不可动、显著才晋升、全量入账本（对抗自欺与回归）。
3. **闭环** = 评估(score) → 优化(experiment) → 固化(promote) ，与同系列构成完整自我进化。

---

## 三、最小上手

```bash
cd self-optimize-agent

# 1) 定义实验：优化 eval_total（越大越好），基线 v1、候选 v2
python3 scripts/optimize.py --define \
  --metric eval_total --direction higher \
  --baseline v1 --candidate v2

# 2) 对同一批 8 个样本各打基线/候选分，喂 8 对
python3 scripts/optimize.py --run \
  --baseline-score 4.1 --candidate-score 4.6 --n 8

# 3) 比较是否显著胜出（样本不足/未达标会明确拒绝）
python3 scripts/optimize.py --compare

# 4) 胜出则晋升 baseline（写 promotion 事件）
python3 scripts/optimize.py --promote

# 5) 基于历史建议下一个候选（贝叶斯式 EI）
python3 scripts/bayes.py --suggest --space resources/optim_space.json

# 账本摘要
python3 scripts/optimize.py --report
```

---

## 四、退出码（可被 CI / 钩子拦截）

| 命令 | 退出码 0 | 退出码 1 | 退出码 2 |
|---|---|---|---|
| `--compare` | 显著胜出 | 样本不足 / 方向不对 / 未显著 | — |
| `--promote` | 已晋升 | 显著性不足（拒绝，baseline 不动） | 用法错误 |
| `--run`/`--define` | 成功 | 前置检查未过 | — |

> 设计意图：`--promote` 在"不通过"时返回 1，可被流水线物理拦下——把"要人记得做验证"变成"机器自动守门"。

---

## 五、与同系列协作

| 包 | 角色 | 与本包关系 |
|---|---|---|
| self-evaluate-agent | 打分 + 反思 | 提供优化目标函数（分数） |
| self-debug-agent | 修明确 bug | 优化前的下限保障 |
| self-verify-agent | 交付门禁 | 优化结果须过门禁才准入 |
| **self-optimize-agent** | **受控实验晋升** | **拿分数做实验，让好累积** |

四者同宗：评估 → 调试 → 验证 → 优化，构成完整的"自我"闭环。

---

## 六、理论学习顺序建议

1. 先读 `SKILL.md` 第二节（理论根基）建立直觉。
2. 再读 `references/optim-theory.md` 看硬学术源头（贝叶斯优化 / SMBO / RISE）。
3. 做实验前读 `references/experiment-method.md`（显著性、护栏）。
4. 想理解"为什么不能省门槛"读 `references/promotion-culture.md`。
