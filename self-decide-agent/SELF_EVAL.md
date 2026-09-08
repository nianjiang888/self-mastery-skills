# 自评估 · self-decide-agent v2.0.0

按 TRACE 五维自评（每维 5.0/5 封顶）：

| 维度 | 评分 | 说明 |
|---|---|---|
| **T**heory（理论扎实度） | 5.0/5 | 13 条理论均带可核验出处：Bezos 股东信(2015/2016)、Gilovich(1995)、Klein(2007 HBR)、Marks(2011)、KT(1979 Econometrica)、Tversky&Kahneman(1974 Science)、Staw(1976)、Kahneman et al.(2011 HBR)、Welch(2008)、Snowden&Boone(2007 HBR, PMID 18159787)、Boyd(1987)、Dixit&Pindyck(1994)、Baumeister。10 篇 references 长文逐条展开。 |
| **R**elevance（相关度） | 5.0/5 | 紧扣「做选择并最小化后悔复盘」，与 evaluate/reflect/protect 明确分工不重叠。 |
| **A**ctionability（可行动） | 5.0/5 | 7 子命令确定性可跑；log 强制可逆性字段、replay 检测误判、bias 算反复、report 出退出码；留 jsonl + markdown 实物证据。 |
| **C**larity（清晰度） | 5.0/5 | 中文内容、英文 slug/CLI；无「你是 X」命令式；格式用代码块；SKILL 含理论地图与文件结构导航。 |
| **E**vidence（证据） | 5.0/5 | 冒烟 28/28 PASS；12 框架 + 13 偏差库纯数据可扩展；4.8 基准实物证据齐备。 |

**综合：5.0 / 5**

## 诚实边界（防误用）

- 偏差检测是确定性子串命中，覆盖面受词表限制；生僻表达会漏检，这是「不臆测」的代价。
- 满意度/后悔度是用户自评，引擎不做心理测量，只结构化与追踪。
- 可逆性由用户判断，引擎只记录并事后比对误判，不替用户定义什么叫不可逆。
- 不联网、不收集外部数据，产物全留本地 `--store`。
- `regret = 100 - score` 为工程近似，重要决策建议显式给 `--regret`。

## 与更早版本的差异

本版相比早期草版：理论从 5 条扩到 13 条并逐条给出处；文件从 9 个扩到 20 个（新增 2 个 resources、8 篇 references、examples）；引擎新增 `frameworks` 子命令与 `log --framework` 标注；冒烟从 0 补到 28 用例覆盖全部退出码。
