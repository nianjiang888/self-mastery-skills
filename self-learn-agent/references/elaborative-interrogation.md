# 精细质询（Elaborative Interrogation）：用"为什么"榨出深层理解

## 一、定义与经典文献

精细质询是一种通过**自问"为什么某陈述为真"来生成解释**的学习策略。它不是泛泛联想，而是针对具体事实追问因果机制。权威出处：

- *Pressley, M., McDaniel, M. A., Turnure, J. E., Wood, E., & Ahmad, M. (1987). Generation and precision of elaboration: Effects on intentional and incidental learning of fact sequences. Journal of Educational Psychology, 79(4), 429–441.* 这是精细质询的奠基性实验，证明让被试解释"为什么事实成立"能显著提升对事实序列的记忆与理解。
- *Dunlosky, J., Rawson, K. A., Marsh, E. J., Nathan, M. J., & Willingham, D. T. (2013). Improving Students' Learning With Effective Learning Techniques. Psychological Science in the Public Interest, 14(1), 4–58.* 把 elaborative interrogation 评为**中等效用（moderate utility）** 策略，并指出它对已有相关知识较多的学习者效果更好。
- 与自我解释（self-explanation）互为表亲：*Chi, M. T. H., Bassok, M., Lewis, M. W., Reimann, P., & Glaser, R. (1994). Self-Explanations: How Students Study and Use Examples in Learning to Solve Problems. Cognitive Science, 18(3), 439–477.* 自我解释强调"边做边说理由"，与精细质询共享"生成解释"内核。

## 二、Pressley et al. (1987) 的关键发现

实验中，学习者阅读一系列事实（如"某动物住在某栖息地"）。一组只重复阅读；一组被要求对每条事实回答"为什么这是真的"。结果精细质询组在后续记忆与推理测验中全面占优。机制在于：回答"为什么"迫使学习者**调用已有知识、建立因果链**，这个过程既加深了编码，又织入了更丰富的提取线索。

值得注意的是，精细质询对"基础好的人"收益更大——因为你得先有"可调用的为什么"才能生成解释。这提示我们：它适合建立在已有图式之上，而非完全陌生的领域（那时应先做 ingesting 打底）。

## 三、为什么它有效：连接到更深的网络

人类记忆是网络化的。一个孤立事实容易忘，但一个"挂"在多个因果节点上的事实极难脱落。精细质询的作用就是**主动制造连接**：把新事实锚定到"因为…所以…"的因果网、到"它和 X 相似/相反"的对比网、到"可以那样用"的应用网。连接越多，提取路径越多，遗忘越难。

这与双重编码（见 dual-coding）异曲同工：双重编码增加"通道"冗余，精细质询增加"语义"冗余，二者都让记忆更抗丢失。

## 四、对 self-learn-agent 的映射

`elaborate` 子命令把精细质询结构化：

- `--why`：对应"为什么成立"（因果链）；
- `--how`：对应"如何应用"（迁移到新情境）；
- `--relate`：对应"与什么相关"（网络锚定）。

三者合力，把一条"concept"从孤立点拓展成一张小网。引擎还会把 elaboration 写回消化笔记（notes/ 下），并小幅提升掌握度，奖励"深度加工"。

## 五、落地要点与误区

要点：问题要具体（问"这个公式为啥成立"而非"它重要吗"）；要真生成答案，不能空想；答案可与笔记、图式对照纠错。误区：把精细质询当"多读一遍"。它要求**产出解释**，不是再输入。误区：对每个零基础知识点硬问为什么——此时应先 ingesting 建立最低限度图式，再质询。

## 六、可核验要点

- Pressley et al. (1987) *JEP 79(4):429–441*：自答"为什么"提升记忆与理解。
- Dunlosky et al. (2013)：评为 moderate utility；对基础好者更有效。
- Chi et al. (1994) *Cognitive Science 18(3):439–477*：自我解释同源。
- 机制：生成因果解释 → 增加语义连接 → 多路径抗遗忘。

## 七、实战工作流示例

对一个刚 ingesting 的概念"间隔效应"，用 `elaborate` 三问生成解释：

```
learn.py elaborate --id <id> \
  --why "因为遗忘曲线先快后慢，必须在流失前补针" \
  --how "用在复习排程上：新点隔1天，之后逐次拉长" \
  --relate "与测试效应同源：都靠提取加深；与交错互补：管时间vs管主题"
```

执行后引擎把三条解释写回 `notes/<id>.md`，并把 mastery 小幅上调——奖励深度加工。一周后该点 mastery 通常高于同批只 ingest 未质询的点，`report` 可对比验证。

## 八、常见问答深挖

问：为什么只对"基础好的人"更有效？ 答：因为回答"为什么"需要可调用的旧知识当原料。面对完全陌生的领域，你无料可生成，应先 ingesting 建立最低图式，再做精细质询，否则只是空想。

问：精细质询和自我解释有什么不同？ 答：精细质询多为事后对事实追问因果；自我解释多在解题过程中边做边说理由（Chi 1994）。二者共享"生成解释"内核，可叠加使用：`elaborate --why` 事后补，解题时口头 self-explain 即时补。

问：可以只对部分知识点质询吗？ 答：可以且推荐。优先质询"概念性/程序性"知识（为什么成立、怎么用），事实性知识（如人名日期）靠 quiz 即可，不必每个都问为什么，避免负荷浪费。

## 九、理论速查卡

- 提出者：Michael Pressley 等（精细质询奠基）、Michelene Chi 等（自我解释同源）。
- 核心年份：Pressley et al. 1987（*JEP 79(4):429–441*）、Chi et al. 1994（*Cognitive Science 18(3):439–477*）。
- 一句话：自问"为什么成立"并生成解释，能显著提升记忆与理解；对基础好者更有效。
- 关键机制：生成因果链 → 增加语义连接 → 多提取路径抗遗忘。
- 与 self-learn-agent：elaborate 的 why/how/relate 三问，并把解释写回 notes、小幅升 mastery。
- 易错点：对零基础硬问为什么（应先 ingesting）；只"再读"不"生成解释"。
- 最小行动：每 ingest 一个概念，至少补一句"因为它……（因果）"。
- 关联理论：双重编码（增加连接）、生成学习（自我解释）、可取难度（生成负荷）。
- 自检：我对这个概念，能不看书说出"它为什么是真的"吗？

> 结论：看懂一个知识点不难，难的是让它"长"进你的知识网。精细质询就是那把把新知焊进旧网的焊枪。self-learn-agent 的 `elaborate` 把"为什么/如何/相关"三问标准化，逼你每次消化都多织几根线。
