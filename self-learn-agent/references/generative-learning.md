# 生成式学习（Generative Learning）：用自己的脑把知识"造"出来

## 一、理论源流与权威文献

生成式学习主张：真正的学习不是把信息"灌"进脑子，而是学习者主动**生成（generate）** 新的表征与意义。代表学者 Richard Mayer 从多媒体学习切入，提出：

- *Mayer, R. E. (2009). Multimedia Learning (2nd ed.). Cambridge University Press.* 提出认知理论 CTML（Cognitive Theory of Multimedia Learning）：人有两个独立但连通的信息加工通道（言语、表象），学习发生在"选择—组织—整合"三个认知过程中。
- *Fiorella, L., & Mayer, R. E. (2015). Learning as a Generative Activity: Eight Learning Strategies that Promote Understanding. Cambridge University Press.* 这是生成式学习的集大成之作，系统提出**八种生成策略**：summarizing（总结）、mapping（画概念图）、drawing（画图）、imagining（想象）、self-testing（自测）、self-explaining（自我解释）、teaching（教别人）、enacting（具身演练）。

## 二、SOI 模型：Select-Organize-Integrate

Mayer 的 SOI 模型解释了"生成"发生在哪：学习者在输入中**选择（Selecting）** 相关信息，在 working memory 中**组织（Organizing）** 成结构，再与已有知识**整合（Integrating）** 进长时记忆。被动阅读只完成"选择"，而生成策略强制走完"组织—整合"，所以学得深。这直接呼应认知负荷理论（见 cognitive-load-theory）：生成活动把外在负荷转化为关联负荷（对图式建构有用的负荷）。

## 三、八策略如何对应 self-learn-agent

Fiorella & Mayer（2015）的八策略几乎可以一对一映射成本引擎的动作：

1. **summarizing（总结）** → `ingest` 的 note 字段，强制用自己的话压缩；
2. **mapping（画概念图）** → 复习时把多知识点用 `interleave` 串成网；
3. **drawing（画图）** → 配合双重编码（见 dual-coding）记图示；
4. **imagining（想象）** → elaborate 的"如何应用"逼出心智模拟；
5. **self-testing（自测）** → `quiz` 主动回忆；
6. **self-explaining（自我解释）** → `elaborate` 的"为什么"；
7. **teaching（教别人）** → 费曼技巧（见 learning-strategies 资源）；
8. **enacting（具身）** → 程序性知识在真实任务里跑一遍。

也就是说，self-learn-agent 不是随机堆功能，而是把 Fiorella & Mayer 的八策略翻译成可执行的 CLI 子命令。

## 四、为什么"生成"比"消费"牢

生成活动迫使学习者从"接收者"变成"制造者"。当你要总结，必须决定什么重要；当你要画图，必须理清关系；当你要教别人，必须补全逻辑漏洞。每一步都在"重组"信息，而重组正是记忆固化的关键（Bjork 的提取即编码）。研究显示，生成策略在"迁移测验"（用旧知识解决新问题）上的增益尤为明显——这正是交错练习与生成学习共同追求的目标。

## 五、落地误区

误区一：生成=抄笔记。抄写是消费，不是生成；真正的生成要"输出新东西"（自己的话、图、讲解）。误区二：生成越多越好。生成也要消耗认知资源，需在负荷承受范围内（呼应 CLT）。误区三：只生成不理解。生成后要有反馈闭环，`report` 与笔记复盘就是这个闭环。

## 六、可核验要点

- Mayer (2009) *Multimedia Learning*：CTML 双通道 + SOI 三过程。
- Fiorella & Mayer (2015) *Learning as a Generative Activity*：八策略清单。
- 八策略：summarizing / mapping / drawing / imagining / self-testing / self-explaining / teaching / enacting。
- 生成把被动输入转为"选择—组织—整合"，深度编码抗遗忘。

## 七、实战工作流示例

以读完一章《认知心理学》为例，用本引擎走完生成式八策略：

```
# 1. summarizing：用自己的话录概念
learn.py ingest --source "《认知心理学》" --title "第3章" \
  --concept "工作记忆容量有限" --note "一次只能保持约4±1个组块，超限就需组块化"

# 5. self-testing：合上书自测
learn.py quiz --id <id> --recall 0.7

# 6. self-explaining：为什么
learn.py elaborate --id <id> --why "因为容量有限，所以必须压缩信息"

# 2/3. mapping+drawing：复习时画概念图、配双编码
learn.py interleave --tags 认知
```

每步都在"输出新东西"，而非被动消费。一周后 `report` 会显示该概念 mastery 明显高于只做过 ingest 的条目——这就是生成效应的可复核证据。

## 八、常见问答深挖

问：生成越多越好吗？ 答：否。生成也消耗认知资源（见 CLT），应在负荷承受范围内；过量生成会变成外在负荷，反而挤掉关联负荷。建议每个知识点做 1–2 种生成动作即可，不必八策略全上。

问：生成和测试有什么区别？ 答：测试（quiz）是"提取已有"，生成（summarizing/drawing）是"建构新表征"，二者互补：生成建网络，测试固网络。self-learn-agent 同时提供，正是为此。

问：看别人的思维导图算生成吗？ 答：不算，那是消费。只有你自己画、自己总结才触发 SOI 的"组织—整合"。可以借鉴别人结构，但落笔必须是自己的。

## 九、理论速查卡

- 提出者：Richard Mayer（加州大学圣塔芭芭拉分校）与 Logan Fiorella。
- 核心年份：Mayer 2009（*Multimedia Learning*）、Fiorella & Mayer 2015（*Learning as a Generative Activity*）。
- 一句话：学习是主动"生成"新表征，不是被动"接收"信息；生成活动走完选择—组织—整合。
- 八策略：总结、画概念图、画图、想象、自测、自我解释、教别人、具身演练。
- 与 self-learn-agent：ingest=总结、quiz=自测、elaborate=自我解释/教别人、interleave=画网，八策略全覆盖。
- 易错点：把抄笔记当生成；生成过量变外在负荷（见认知负荷）。
- 最小行动：读一节后，合书用一句话总结，再画一张两节点之间的关系图。
- 关联理论：双重编码（画图即双通道）、测试效应（自测）、精细质询（解释）。
- 自检：我今天的学习，有几步是"输出新东西"而非"再看一遍"？

> 结论：读书最大的陷阱是"以为看懂就是学会"。生成式学习告诉我们，必须让脑子"造"点什么出来。self-learn-agent 的每个子命令都在逼你生成——总结、自测、解释、交错，都是把别人的知识改造成你自己的私有库。
