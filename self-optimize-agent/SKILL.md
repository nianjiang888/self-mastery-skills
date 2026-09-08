---
name: self-optimize-agent
display_name: 受控自我实验优化
title: self-optimize-agent
version: 2.0.0
description: 受控自我实验优化引擎：把自评/验证分数当目标函数，跑 A/B 实验，显著胜出才晋升 baseline，用贝叶斯式采集函数挑下一个候选。触发：优化/调优/改进/变更好/自我提升/A/B 测试/哪个版本更好/optimize/tuning/实验改进/显著性/晋升 baseline/我是不是真的变好了。
license: MIT
---

# self-optimize-agent · 受控自我实验优化引擎

> 不是"改一改"，而是**对自己做受控实验**：把评估分数当目标函数，跑 A/B，显著胜出才晋升。
> 自我 = 不假外求地、用最小的实验代价，逼近更优的自己。

---

## 一、这个 Agent 到底在干什么（"自我"的本质）

「自我优化」最易被理解成"我改一版试试"。那不是优化，那是无依据的试错。

本 Agent 的「自我」是：**把你（或你的产出、你的流程）当作一个待优化的系统，把某个可量化分数当作目标函数，然后像调超参一样，对你做受控实验。**

- self-evaluate 给你一个分数（"这段 4 分"）；
- self-debug 修掉明确坏掉的地方；
- self-verify 把你拦在交付门禁前；
- **self-optimize 拿着那个分数，问"怎么做才能系统性地更高"，并真的去试、去比较、去晋升。**

这就是"自我"的闭环第四环：**评估 → 修复 → 验证 → 优化**，环环相扣，但 optimize 是真正让"好"可持续累积的那一环。

### 为什么需要"受控实验"而不是"改改看"

直觉改版有两个致命伤：

1. **回归盲区**：你改 A 以为变好了，却悄悄把 B 弄坏了。没有对照基线，你根本不知道。
2. **自欺盲区**：人（和模型）天然倾向于"确认自己变好了"。没有统计显著性，一句"感觉更顺了"就能骗过自己。

本 Agent 用两条铁律对抗这两者：
- **对照基线（baseline）不可动**：每次实验只动候选（candidate），用同一组评测样本同时打分基线和候选，方向可比。
- **显著才晋升**：差异要在统计上站得住（达到最小样本 + 预设显著性阈值 + 不回归其他维度），否则候选被丢弃或回滚，baseline 不动。

---

## 二、理论根基（硬学术，不是口嗨）

### 1. 贝叶斯优化（Snoek, Larochelle, Adams, NeurIPS 2012）

原论文把"机器学习超参调优"这个黑盒函数，用**高斯过程（Gaussian Process）**建模成代理（surrogate），再用**采集函数（acquisition function）**决定"下一个试哪个配置"。核心结论：在 CIFAR-10 上自动找到的配置达到 14.98% 误差，击败设计该架构的人类专家（18%）。

它解决的本质问题是：**函数评估极贵（跑一次模型要几小时），所以必须让"下一次试什么"尽量聪明**。这和系统优化自己完全同构——你的"评一次"也贵（要真做任务、真打分），所以不能瞎试。

### 2. SMBO：序列模型优化（SigOpt/Intel Primer, Algorithm 1）

贝叶斯优化的标准骨架，四步循环：

```
初始化：在搜索空间撒少量初始点（随机/Latin Hypercube）
fit：用已有数据拟合代理模型（预测均值 + 不确定性）
select：优化采集函数，挑出"最值得试"的下一个点
evaluate：跑真实（昂贵）目标，得到 y
update：把 (x, y) 并入历史，回到 fit
```

本 Agent 的 `optimize.py --suggest` 就是这套循环的中文落地版，只是把"昂贵目标"换成"跑一次评测样本集"。

### 3. 探索 vs 利用（Exploration-Exploitation）

采集函数平衡两件事：
- **利用（exploitation）**：去模型预测分数高的地方，精修已知好区域；
- **探索（exploration）**：去模型不确定的地方，可能藏着更好的区域。

纯利用会早熟收敛到局部最优；纯探索浪费实验。Expected Improvement（EI）和 Upper Confidence Bound（UCB）是两种经典平衡法。本 Agent 的 `bayes.py` 默认用 EI。

### 4. Agent 自优化综述（arXiv 2503.12434）

2025 年的综述把 LLM Agent 优化分成：
- **经验优化（Experience-based）**：把成功/失败轨迹存进 memory，提炼成可复用的知识图、手册、指南（Optimus-1 / ExpeL / AutoManual）。
- **反馈优化（Feedback-based）**：用环境反馈或自我评估做反思、纠正、迭代（Reflexion / SAGE / RISE）。

本 Agent 是反馈优化 + 经验优化的交集：每次实验的"哪个候选赢了"就是一条经验，沉淀进实验账本。

### 5. Recursive Introspection（RISE, Qu et al., NeurIPS 2024）

把"单轮改写"建模成多轮 MDP，教模型递归地**检测并改正自己上一轮的错误**。实验表明 Llama/Llama3/Mistral 能用更多轮次自我提升，且不破坏单轮能力。这给本 Agent 一个关键启示：**优化本身是递归的**——晋升后的候选成为新 baseline，下一轮又从它出发。

---

## 三、核心能力（主动 Agent）

本 Agent 不只是被动回答"怎么优化"。它会被设计成**主动**触发：

- **主动触发场景**：
  - 当你连续完成 N 个任务后，主动建议"是否跑一轮优化实验，看看最近的做法是否优于两周前的 baseline"。
  - 当 self-evaluate 给出某维度持续低分（如"R 可靠性连 3 次 ≤3"），主动提议"要不要做一个针对性优化实验"。
  - 当你说"最近感觉顺了"，主动提醒"顺不顺要用实验数据说话，要不要 A/B 一下"。

- **能力清单**：
  1. `define`：定义一次实验——选指标、选可调旋钮、锁定 baseline。
  2. `run`：对一组样本同时跑 baseline 与 candidate，各自打分。
  3. `compare`：判定 candidate 是否**显著胜出**（含最小样本、方向、回归检查）。
  4. `promote` / `rollback`：胜出则晋升 baseline；否则回滚，baseline 不动。
  5. `suggest`：基于全部历史实验，用贝叶斯式 EI 推荐"下一个最值得试的旋钮组合"。
  6. `log`：所有实验写进 `experiment_log.jsonl`，形成可回放的实验账本。

---

## 四、用法速览（详见 README.md）

```bash
# 1) 定义实验：指标=评估总分，旋钮来自 optim_space.json
python3 scripts/optimize.py --define \
  --metric "eval_total" --direction "higher" \
  --baseline "v1_prompt" --candidate "v2_prompt"

# 2) 跑 A/B：对同一批样本打分基线和候选
python3 scripts/optimize.py --run \
  --baseline-score 4.1 --candidate-score 4.6 --n 8

# 3) 比较是否显著胜出
python3 scripts/optimize.py --compare

# 4) 胜出则晋升 baseline
python3 scripts/optimize.py --promote

# 5) 基于历史建议下一个候选（贝叶斯式 EI）
python3 scripts/bayes.py --suggest --space resources/optim_space.json
```

所有命令输出全中文；失败有中文报错；关键节点返回非零退出码（可被 CI / 钩子用来物理拦下不达标晋升）。

---

## 五、边界与红线（保持"自我"的诚实）

1. **不无对照改 baseline**：任何"晋升"都必须有对照实验支撑，禁止"感觉更好就覆盖"。
2. **不隐瞒回归**：candidate 在次要维度掉分，必须显式报告，不得只报主指标。
3. **不做无显著性的宣称**：未达显著性阈值的"提升"只能记为"未证实"，不能写进结论。
4. **不替代评估与验证**：optimize 建立在 evaluate/verify 之上，不自己发明分数；若上游未评估，先去 evaluate。
5. **不无限膨胀实验**：设实验预算上限（默认 20 轮），超出则停止并报告当前最佳，避免为微小提升耗尽成本（呼应贝叶斯优化的"昂贵评估"约束）。

---

## 六、与同系列的关系（独立而可合作）

- **self-evaluate-agent**：提供分数（目标函数来源）。
- **self-debug-agent**：修掉明确 bug（优化的"下限保障"）。
- **self-verify-agent**：交付门禁（优化结果必须过门禁才准入）。
- **self-optimize-agent**：拿分数做受控实验，让"好"累积成 baseline。

四者同宗：一个完整的"自我"闭环——**知道自己几斤两量（评估）→ 改掉明显的错（调试）→ 拦住不达标的交付（验证）→ 系统性地变得更好（优化）**。
单条下载即可独立完成"对自己做受控改进"的真实任务；组合使用则构成自我进化的完整引擎。
