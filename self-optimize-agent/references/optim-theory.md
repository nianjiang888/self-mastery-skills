# 优化理论根基：从贝叶斯优化到 Agent 自我改进

> 本文件是 self-optimize-agent 的硬学术底座。它要回答一个问题：
> **"自我优化"不是"改改看"，而是把"被评估的分数"当目标函数、对自己做受控实验。**
> 这套思想在机器学习、自动调参、Agent 研究中都有扎实的源头。读懂它们，才不会把优化做成自欺。

---

## 一、贝叶斯优化（Snoek, Larochelle, Adams, NeurIPS 2012）

### 1.1 它解决什么问题

机器学习算法几乎都带"旋钮"：学习率、正则强度、层数、批大小……这些**超参数**极大影响最终表现，但调起来是门"黑艺术"——靠专家经验、靠口口相传的土法则，或靠暴力网格搜索。

Snoek 等人（2012）指出：把超参调优看成对一个**未知黑盒函数**的优化，这个函数把"超参组合"映射到"泛化性能"。每次"评估"这个函数都很贵（要把模型完整训练一遍）。在这种**评估极贵**的场景，贝叶斯优化比网格/随机搜索高效得多。

### 1.2 核心机制

1. **代理模型（surrogate）**：用一个**高斯过程（Gaussian Process, GP）**去近似那个未知函数。GP 的好处是：对任意输入点，它不只给一个预测均值，还给出**不确定性（方差）**——这正是后续"探索-利用"平衡的关键。
2. **采集函数（acquisition function）**：决定"下一个试哪个点"。经典两种：
   - **Expected Improvement（EI）**：选"期望能比当前最好再提升多少"最大的点。它天然兼顾"预测高"（利用）和"不确定"（探索）。
   - **Upper Confidence Bound（UCB）**：显式用 `均值 + κ·标准差` 选点，κ 可调，直接控制探索权重。
3. **循环**：初始化少量点 → 拟合 GP → 优化采集函数选下个点 → 跑真实目标 → 把 (x, y) 并入数据 → 回到拟合。因为每步都用到**所有历史数据**，样本效率极高；很多函数在几十到几百次评估内就能找到好解（网格搜索要上千次）。

### 1.3 关键结论（给本 Agent 的启示）

- 在 CIFAR-10 上，自动调出的三层 CNN 达到 **14.98% 误差**，击败设计该架构的人类专家（18%）。这说明：**自动化的、数据驱动的优化能发现人类直觉遗漏的配置**。
- 作者还做了"成本感知"（Expected Improvement per Second）和"并行幻想（fantasies）"——提醒我们：优化要考虑**每次实验的代价**，别为微小提升耗尽预算。本 Agent 的"实验预算上限"就源于此。

---

## 二、SMBO：序列模型优化（SigOpt/Intel Primer, Algorithm 1）

贝叶斯优化的标准骨架叫 Sequential Model-Based Optimization。伪代码（Algorithm 1）极简却完整：

```
输入：目标 f, 空间 X, 采集函数 S, 代理模型 M, 预算 T
D ← 初始化采样(f, X)            # 撒少量初始点
for i ← |D| to T do
    p(y|x,D) ← FITMODEL(M, D)   # 用历史拟合代理，给出预测分布
    x_i ← argmax_{x∈X} S(x, p)  # 优化采集函数，选下一个点
    y_i ← f(x_i)                # 昂贵的真实评估
    D ← D ∪ (x_i, y_i)          # 把观测并入历史
end for
```

这就是本 Agent `optimize.py` 的循环原型：

- `define` = 确定 f（指标）、X（optim_space 的旋钮）、初始化。
- `run` = 评估 f(x_i)（对基线和候选各打一次分）。
- `compare`/`promote` = 基于历史 D 判断"是否值得把候选晋升为新的基线"。
- `suggest` = 优化采集函数 S，挑下一个 x_i（由 `bayes.py` 用 EI 实现）。

**核心差异只有一处**：贝叶斯优化的 f 是"跑模型几小时"，本 Agent 的 f 是"跑一轮评估/验证样本集"。但两者的数学结构**完全同构**——这正是"自我优化"能立于硬学术的根。

---

## 三、探索 vs 利用（Exploration-Exploitation）

这是所有序贯决策优化的灵魂张力：

- **利用（exploitation）**：去代理模型预测分数高的区域，精修已知的好配置。
- **探索（exploration）**：去模型不确定的区域，可能藏着更好的配置。

纯利用 → 早熟收敛到局部最优（模型在没探索过的地方不准，你却信了它）。
纯探索 → 浪费实验在不太可能好的地方。

采集函数就是编码这种平衡的机制。EI 通过 `Δ·Φ(Δ/σ) + σ·φ(Δ/σ)` 让"预测高"和"不确定"都贡献正收益；UCB 用可调 κ 显式加权不确定性。

本 Agent 的 `bayes.py` 用 EI 做推荐：**在"可能更高"和"还不确定"之间取最大期望提升的点**。这保证我们既不瞎试，也不死守已知。

---

## 四、Agent 自优化综述（arXiv 2503.12434, 2025）

2025 年的综述把 LLM-based Agent 的优化分成两大类，本 Agent 恰好坐在它们的交集上：

### 4.1 经验优化（Experience-based）

从成功/失败轨迹里提炼可复用知识：
- **Optimus-1**：多模态 memory 把探索轨迹转成知识图，辅助规划与提示生成。
- **ExpeL**：自主从训练任务收集知识，推理时召回。
- **AutoManual**：把任务规则组织成"手册"作为提示，并更新系统规则。

→ 对应本 Agent 的 `experiment_log.jsonl`：**每次实验的"谁赢了"都是一条经验，沉淀进可回放的账本**。

### 4.2 反馈优化（Feedback-based）

用环境或自我评估的反馈做反思、纠正、迭代：
- **Reflexion**（Shinn et al.）：环境/任务反馈转成文字纠正，驱动自我反思调整。
- **SAGE**：checker 给当前解法迭代反馈，assistant 生成自我反思再反馈，自我演化。
- **RISE**（见下一节）。

→ 对应本 Agent 的上游：分数来自 self-evaluate（Reflexion 多轮闭环），门禁来自 self-verify。

**综述的核心论断**：反馈优化不修改模型参数，而是用自然语言反馈迭代地引导和优化 Agent 行为——这正是"自我"优化的轻量、可解释形态。

---

## 五、Recursive Introspection（RISE, Qu et al., NeurIPS 2024）

### 5.1 它证明了什么

最强的大模型也不太能"随着更多计算/交互，持续改好自己之前的回答"。RISE 用多轮 MDP 微调，教模型**递归地检测并改正自己上一轮的错误**。实验表明 Llama2/Llama3/Mistral 能用更多轮次自我提升，且在同等推理算力下优于单轮策略，且**不破坏单轮能力**。

### 5.2 给本 Agent 的启示

- **优化是递归的**：晋升后的候选成为新 baseline，下一轮又从它出发——正是 RISE 的"多轮递归修正"精神。
- **不是一次性**："自我"的变好是迭代过程，不是改一版就完。本 Agent 强制 `promote` 之后继续以新 baseline 为起点，正是为此。
- **可测量才可持续**：RISE 用"更多轮是否真的更高分"衡量自我改进——本 Agent 用"显著胜出才晋升"做同样的事，只不过把"轮次"换成"对照实验"。

---

## 六、把理论翻译成本 Agent 的纪律

| 理论要点 | 本 Agent 的落地 |
|---|---|
| 评估极贵 → 聪明地选下一个点 | 设实验预算上限，不无限试；`suggest` 用 EI 选最值试点 |
| 代理模型给"预测+不确定性" | `bayes.py` 核回归输出 μ 与 σ，EI 平衡探索利用 |
| 历史数据指导下一步 | `experiment_log.jsonl` 是所有决策的唯一事实源 |
| 显著才可信（避免局部最优/早熟） | `compare` 用 Welch t + 显著性阈值 + 最小样本，不达标不晋升 |
| 成本感知 | 不为了微小提升耗尽预算，超出上限即停报当前最佳 |
| 反馈当梯度、自然语言当参数 | 上游 self-evaluate/verify 的分数是"梯度"，候选改动是"参数更新" |

---

## 七、常见误解（也是 4.7 评价的提醒）

有人会问："我直接改一版不就行了？"不行，原因在 4.7 评价里也点过——**校准/验证这类事"需要你主动记录"，有使用门槛**。本 Agent 的设计正是把"主动记录"变成**零负担的自动实验账本**：

- 你只需定义实验（--define）、喂对照样本（--run）。
- 要不要晋升、下一个试什么，引擎按数学算，不靠"感觉"。
- 一切可回放、可审计——这就是"自我优化"区别于"自我安慰"的地方。

---

## 八、延伸阅读（论文锚点）

- Snoek, Larochelle, Adams. *Practical Bayesian Optimization of Machine Learning Algorithms*. NeurIPS 2012.
- Shahriari et al. *Taking the Human Out of the Loop: A Review of Bayesian Optimization*. 2015.
- SigOpt/Intel. *Bayesian Optimization Primer*.
- A Survey on the Optimization of LLM-based Agents. arXiv 2503.12434. 2025.
- Qu et al. *Recursive Introspection: Teaching Language Model Agents How to Self-Improve (RISE)*. NeurIPS 2024.
- Ishibashi et al. *Can LLMs Invent Algorithms to Improve Themselves? (Self-Developing)*. arXiv 2024.
