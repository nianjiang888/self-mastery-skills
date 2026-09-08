# self-decide-agent 理论总论

self-decide-agent 不靠「你该想清楚再决定」这种空话驱动。它把 13 条经实证的研究传统，落成可重跑的代码逻辑：每一条理论都对应一个子命令、一种退出码、一份可复核的产物。本文说明每条理论落在引擎的哪个位置，为什么「外部脚手架」比「靠自觉」可靠，以及它们如何串成一条从「事前」到「事后」的决策改进闭环。

## 一、为什么需要外部脚手架（System 1 / System 2，Kahneman）

Daniel Kahneman 在《思考，快与慢》里把思维分为两套系统：**System 1** 快、直觉、自动化，但也最容易被偏差劫持；**System 2** 慢、费力、可控，却天然懒惰——能不调用就不调用。

决策质量的最大敌人不是「不懂方法」，而是「方法懂了却总在关键时刻用不上」。疲劳、情绪、时间压力会让 System 2 的「电池」耗尽，于是人退回 System 1 的自动默认。本引擎的全部子命令，本质上都是在**强制调用 System 2**：

- `log` 强制把可逆性从「下意识判定」变成「必须显式填写的字段」，打断 System 1 的自动默认。
- `premortem` 强制想象失败路径，对抗 System 1 的「计划谬误」式乐观。
- `replay` 的事后比对，把 System 1 当时写的「记忆」与 System 2 当时锁定的「记录」并排，防止记忆自我美化。

而决策疲劳（Baumeister）恰恰描述 System 2 的资源会被耗尽——这正是为什么反复偏差要用外部清单替代意志力。引擎不改造大脑，只是把 System 2 的审查**外置成可重跑的文件**。

## 二、13 条理论地图

| # | 理论 | 提出者 / 出处 | 落点 | 专文 |
|---|---|---|---|---|
| 1 | 单向门 / 双向门 | Bezos，2015/2016 股东信 | `log` 强制标可逆性 | reversible-framework.md |
| 2 | 后悔最小化 | Bezos 1994（Gilovich 根基） | `replay` 后悔度 | regret-minimization.md |
| 3 | 事前验尸 | Klein 2007（HBR） | `premortem` | pre-mortem-method.md |
| 4 | 二阶思考 | Marks 2011（溯 Bastiat 1850） | `premortem` 第三步 | second-order-thinking.md |
| 5 | 损失厌恶 | KT 1979（Econometrica） | 偏差库 | decision-biases-catalog.md |
| 6 | 锚定效应 | Tversky & Kahneman 1974 | 偏差库 | decision-biases-catalog.md |
| 7 | 沉没成本 | Staw 1976 | 偏差库 | decision-biases-catalog.md |
| 8 | 外部视角 | Kahneman et al. 2011（HBR） | 框架库 | external-view-planning-fallacy.md |
| 9 | 10-10-10 | Welch 2008 | 框架库 | 10-10-10-method.md |
| 10 | Cynefin | Snowden & Boone 2007（HBR） | 框架库 | cynefin-ooda.md |
| 11 | OODA 循环 | Boyd 1987 | 框架库 | cynefin-ooda.md |
| 12 | 实物期权 | Dixit & Pindyck 1994 | 框架库 | real-options-flexibility.md |
| 13 | 决策疲劳 | Baumeister 等 | `bias` 提示 | （见本篇第四节） |

## 三、从事前到事后的闭环

```text
frameworks（先挑框架）
   → premortem（事前：假设失败 + 二阶 + 可逆性校验）
   → log（落决策：选项/预期/可逆性 + 偏差预检 + 框架标注）
   → [时间流逝，真实结果发生]
   → replay（事后：实际结果 + 满意度 + 后悔度 + 纠正可逆性误判）
   → bias（跨决策：识别反复偏差）
   → report（聚合：误判率 + 常犯偏差 + 后悔最小化，退出码 0/1/4）
```

理论不是装饰。每一条都对应一个子命令、一种退出码、一份可重跑的产物——这就是「帮用户做决定，并事后最小化后悔地复盘」从格言变成机制的方式。

## 四、决策疲劳：System 2 的电池

Roy Baumeister 的「自我损耗（ego depletion）」研究与后续关于「决策疲劳」的实证（如法官假释率在一天内随疲劳下降的经典研究）揭示：人的决策质量不是恒定资源，而是会随当天累计的抉择次数**递减**。

这条理论直接解释了为什么「反复偏差」常在疲劳时段集中出现。引擎的 `bias` 报告末尾给出决策疲劳提示：反复偏差往往出现在精力低位，建议把重要决定挪到精力充沛时，并固化成「决策前检查清单」——用外部清单替代被损耗的意志力。这也是 `report` 退出码 1（发现反复偏差）的一个潜在根因解读。

## 五、后悔的时序错位：为什么「不做」更痛（Gilovich & Medvec）

Tom Gilovich 与 Victoria Medvec 在 1995 年的经典研究《The Experience of Regret》揭示了一个反直觉的规律：**短期内人们更后悔「做了的蠢事」（行动性后悔），但长期来看，最刺痛的是「没做的事」（不作为后悔）**。

这个时序错位，正是 Bezos 后悔最小化框架的心理学根基：当你站在 80 岁的视角回看，多半不会为「试过没成」而后悔，却会为「本来可以却没动」夜不能寐。引擎在 `premortem` 第五步、在 `replay` 的后悔度量化、`report` 的后悔最小化建议里，反复落点这一发现——它解释了对抗「后悔厌恶（regret aversion）」偏差的必要性：因怕后悔而拖延/保守，长期反而累积更大的后悔。

## 六、诚实边界

- 偏差检测是**确定性子串命中**，覆盖面取决于 `resources/biases.json` 的词表；生僻表达会漏检，这是「不臆测」的代价。
- 后悔度/满意度是用户自评输入，引擎不做心理测量；它只是把自评结构化、可追踪。
- 可逆性分类由用户判断，引擎只负责记录与事后比对误判，不替用户定义什么叫不可逆。
- 不联网、不收集任何外部数据，所有产物留在用户指定的 `--store` 目录。
