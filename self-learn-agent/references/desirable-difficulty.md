# 可取难度（Desirable Difficulties）：越"费劲"的提取，记得越牢

## 一、理论源流与权威文献

"可取难度"由 Bjork 夫妇提出，指一类**当下让学习更困难、长期却提升记忆与迁移**的条件。它挑战直觉：顺畅≠学会，磕绊≠无效。核心文献：

- *Bjork, R. A., & Bjork, E. L. (1992). A New Theory of Disuse: forgetting as a Function of Retrievability and Storage Strength. In A. F. Healy, S. M. Kosslyn, & R. M. Shiffrin (Eds.), From Learning Processes to Cognitive Processes: Essays in Honor of William K. Estes. Erlbaum.* 提出"新闲置理论"，区分存储强度与提取强度。
- *Bjork, E. L., & Bjork, R. A. (2011). Making Things Hard on Yourself, But in a Good Way: Creating Desirable Difficulties to Enhance Learning. In M. A. Gernsbacher, R. W. Pew, L. M. Hough, & J. R. Pomerantz (Eds.), Psychology and the Real World. Worth.* 面向大众的综述，列举可取难度家族：间隔、交错、测试、减馈等。
- 与测试效应（Karpicke & Roediger 2008）、间隔效应（Cepeda 2006）共同构成"困难有益"证据链。

## 二、存储强度 vs 提取强度

Bjork 的关键区分：一条记忆有"存储强度"（信息多牢）和"提取强度"（此刻多容易想出）。反复阅读把**提取强度**短暂拉高（所以当下流畅），却几乎不增加**存储强度**（所以睡醒就忘）。而间隔、测试、交错这些"困难"操作，虽然当下提取强度低（费劲），却在持续累积存储强度——这才是长期记忆的真正引擎。

一句话：**当下容易的练习强化的是"错觉"，当下困难的练习强化的是"记忆"。**

## 三、可取难度家族

Bjork 列举的典型可取难度：

1. **间隔（spacing）**：拉长复习间隔，让每次提取更费劲；
2. **交错（interleaving）**：混排主题，增加辨别负荷；
3. **测试（retrieval）**：用提取代替重读；
4. **减馈（reduced feedback delay）**：不立即给答案，先让自己挣扎；
5. **变情境（context variation）**：在不同环境/表述下学习，增强泛化。

这些恰好是 self-learn-agent 六大子命令的理论母集：`review`=间隔+测试，`interleave`=交错，`quiz`=测试，`elaborate`=深度加工（亦增负荷）。

## 四、为什么它和"流畅性错觉"一体两面

前面 metacognitive-monitoring 提到：人用"流畅度"代理"掌握度"，而可取难度恰恰制造"不流畅"。所以真正高效的学习者要**对抗直觉**——当练习很顺时警惕（可能只在刷提取强度），当练习很磕绊时安心（正在建存储强度）。本引擎的 `report` 用客观 recall 成绩而非你的体感来报掌握度，正是帮你绕开这套直觉陷阱。

## 五、落地边界（难度要"可取"而非"不可取"）

边界极重要：难度必须落在"可成功提取"的区间。如果间隔长到全忘光、交错乱到无从辨别、测试难到完全卡死，那就从"可取"变成"无效"。Bjork 强调"可取"二字——是**刚好够不着、踮脚够得着**的难度。工程上，`review` 的间隔按 Leitner 渐进拉长、`quiz` 优先抽低掌握度项，都是在维持这个"踮脚区间"。

## 六、可核验要点

- Bjork & Bjork (1992) "新闲置理论"：存储强度 vs 提取强度。
- Bjork & Bjork (2011)：可取难度家族（间隔/交错/测试/减馈/变情境）。
- 规律：当下流畅→错觉；当下困难→长记。
- 边界：难度须"可取"（可成功提取），非无限难。

## 七、实战工作流示例

把"可取难度"刻意嵌进每周节奏：

```
# 1. 合上书才回忆（quiz 制造提取难度）
learn.py quiz --id <id> --recall 0.6
# 2. 隔几天才复习（review 间隔制造时间难度）
learn.py review --id <id> --grade 4
# 3. 混着练才辨得清（interleave 制造辨别难度）
learn.py interleave --tags 方法 --count 6
```

三者合力，每次练习都"刚好够不着、踮脚够得着"。若某次 recall 跌到 0.2 以下（太难），说明难度越过"可取"边界，应缩短间隔或先补 ingesting——保持难度在可取区间，而非无限难。

## 八、常见问答深挖

问：可取难度和"虐待自己"的边界在哪？ 答：在"能否成功提取"。Bjork 强调 desirable（可取）——是踮脚够得着的难，不是完全够不着的难。当测试全卡死、间隔长到全忘光，难度就从"可取"滑向"无效"，需回调。

问：为什么当下流畅反而危险？ 答：流畅提升的是"提取强度"（暂时好想），不增"存储强度"（长期牢度）。重读最流畅却最易忘；测试最磕绊却最牢。所以别用"顺不顺"衡量学习，用"几天后还能不能提取"衡量。

问：self-learn-agent 哪些设计在制造可取难度？ 答：`quiz` 的合书回忆、`review` 的间隔拉长、`interleave` 的主题混排、以及 `report` 用客观成绩对抗流畅错觉——几乎每个子命令都在有意制造"有益的困难"。

## 十一、理论速查卡

- 提出者：Robert A. Bjork 与 Elizabeth L. Bjork（加州大学洛杉矶分校）。
- 核心年份：1992（新闲置理论）、2011（*Psychology and the Real World* 综述）。
- 一句话：当下费劲但能成功的提取，长期记忆最强；流畅≠学会。
- 两个强度：存储强度（长期牢度）vs 提取强度（当下易想）；重读只拉提取、不增存储。
- 可取难度家族：间隔、交错、测试、减馈、变情境。
- 与 self-learn-agent：quiz 合书回忆、review 间隔拉长、interleave 主题混排，全是可取难度。
- 易错点：难度越过"可成功提取"边界就变无效，需回调（recall 长期<0.2 即警报）。
- 最小行动：下次练习若很顺，警惕——可能只在刷提取强度；刻意制造一点磕绊。
- 关联理论：测试效应（Karpicke 2008）、间隔效应（Cepeda 2006）、元认知监控（Koriat 1993）。
- 自检：我今天的学习有多少是"可取难度"，有多少只是"虚假流畅"？

> 结论：学习的反直觉真理是——别追求轻松。self-learn-agent 故意让你"合上书才回忆""混着练才辨得清""隔几天才复习"，这些磕绊不是 bug，而是 Bjork 说的"可取难度"：当下越费劲，记忆越长寿。
