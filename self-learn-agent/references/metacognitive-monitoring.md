# 元认知监控（Metacognitive Monitoring）：校准"我真的会了吗"

## 一、概念与权威文献

元认知监控指学习者对自己"知道什么、不知道什么"的觉察与校准能力，是"学会学习"的核心。其中最重要的一环是**知晓感（Feeling of Knowing, FOK）**——你对"某信息能否被提取"的主观判断。关键文献：

- *Hart, J. T. (1965). Memory and the Feeling-of-Knowing Experience. Journal of Educational Psychology, 56(4), 208–216.* 首次系统研究 FOK：人能在一定程度上预判"我能不能想起来"，但这种预判常出错。
- *Koriat, A. (1993). How Do We Know That We Know? The Accessibility Model of the Feeling of Knowing. Psychological Review, 100(4), 609–639.* 提出"可达性模型"：FOK 判断依赖的是"提取线索的容易程度"，而非真实记忆强度——这正是错觉的根源。
- *Koriat, A., Goldsmith, M., & Pansky, A. (2002). Toward a Psychology of Memory Accuracy. Annual Review of Psychology, 53, 549–577.* 研究练习后"欠自信效应"等校准现象。
- *Dunlosky, J., & Bjork, R. A. (2008). The Labor-in-Vain Effect: Illusions of Competence. In M. A. Gernsbacher & J. P. Byrne (Eds.), Psychology of Learning and Motivation, 49, 85–110.* 命名"能力错觉（illusion of competence）"：流畅的重读让人误以为会了。

## 二、Koriat (1993) 可达性模型：错觉从哪来

Koriat 的关键洞见：当你判断"我能不能想起 X"，大脑并不是去查"记忆仓库里 X 有多牢"，而是看"此刻有多少线索蹦出来"。线索多→误以为记得牢；线索少→误以为忘了。问题在于，**流畅性（线索蹦出的容易度）≠ 真实保持强度**。重读一遍材料后，线索瞬间变多、提取变顺，于是你产生强烈的"我会了"错觉——但那只是短暂流畅，睡一觉就现原形。

这解释了为什么"反复阅读"是效率陷阱：它制造流畅，却几乎不增加真实保持。真正能校准判断的是**提取测试**——测试时线索不会白送，你要么真想出来（真会），要么卡住（真不会），反馈是诚实的。

## 三、能力错觉与教育后果

Dunlosky & Bjork (2008) 的"白费力气效应（labor-in-vain）"指出：学生常把时间砸在"看起来有用实则无效"的活动上（重读、划重点、看视频不做题），因为这些活动带来流畅感，被误读为学习进展。结果考试一揭底，才发现自己只是"熟悉了页面"，并非"掌握了内容"。

破除错觉的唯一可靠手段是**用提取测试代替重读**——而这正是 `quiz` 与 `review` 在做的事。测试把"主观 FOK"替换为"客观 recall 成绩"，让掌握度从猜测变成测量。

## 四、对 self-learn-agent 的映射

本引擎把元认知监控嵌进两条路径：

1. **客观化判断**：`quiz` 的 `--recall` 与 `review` 的 `grade` 用真实提取成绩驱动 `mastery`，而非让你"感觉会了"。`report` 据此输出"薄弱/高风险"清单，把模糊的 FOK 变成可读的表格。
2. **风险预警**：`spacing-algorithms.json` 的 `risk_rule` 把 mastery<0.4 判薄弱、<0.3 或遗忘≥2 次判高风险，并以退出码 1（EXIT_ATTENTION）提醒你"别被流畅骗了，这些点真危险"。

## 五、落地要点

要点：定期用测试代替"看一遍"来自检；把"我熟悉"和"我能提取"区分开；用 `report` 的薄弱清单对齐你的主观感受与客观数据。误区：相信"看懂视频=学会"；相信"划了重点=记住"；用流畅度当掌握度代理。

## 六、可核验要点

- Hart (1965) *JEP 56(4):208–216*：FOK 可研究、常出错。
- Koriat (1993) *Psychological Review 100(4):609–639*：可达性模型——FOK 看线索易度而非真实强度。
- Dunlosky & Bjork (2008)：能力错觉 / labor-in-vain 效应。
- 解法：用提取测试校准 FOK，流畅≠掌握。

## 七、实战工作流示例

每周用 `report` 做一次"主观 vs 客观"对账：

```
learn.py report
# 输出：薄弱(<40%) N 项、高风险 M 项，并列出清单
```

把清单和你"自以为会了"的清单对比。若你以为会、引擎标薄弱，那就是 Koriat 说的 FOK 错觉——立刻对这些点做 `quiz` 主动回忆，用客观 recall 成绩覆盖错觉。长期坚持，你的主观判断会越来越准（校准提升）。

## 八、常见问答深挖

问：FOK 错觉能完全消除吗？ 答：不能，它是大脑默认启发式，但可以用"测试替代重读"大幅削弱。关键动作是：任何"我感觉会了"的断言，都先用一次 `quiz` 验证，让客观成绩说话。

问：为什么重读制造错觉、测试破除错觉？ 答：重读让提取线索瞬间变多、当下流畅，误导 FOK 判"记得牢"；测试不送线索，要么真想出（真会）要么卡住（真不会），反馈诚实，所以能校准。

问：report 的"高风险"判定依据什么？ 答：依据 `spacing-algorithms.json` 的 `risk_rule`：mastery<0.3 或 forgotten_count>=2 判高风险，并以退出码 1 提醒。这是把元认知预警工程化，不用你凭感觉焦虑。

## 九、理论速查卡

- 提出者：Lynne Reder（Hart 1965 奠基 FOK）、Asher Koriat（1993 可达性模型）、Bjork 夫妇（能力错觉）。
- 核心年份：Hart 1965、Koriat 1993（*Psychological Review 100(4):609–639*）、Dunlosky & Bjork 2008。
- 一句话：人对"自己会不会"的判断常错；流畅感≠掌握度，需用提取测试校准。
- 关键机制：可达性模型——FOK 看线索易度而非真实强度，故产生错觉。
- 与 self-learn-agent：quiz 的 recall 与 review 的 grade 用客观成绩驱动 mastery；report 输出薄弱/高风险清单。
- 易错点：把重读后的流畅当学会；用"熟悉页面"误判"掌握内容"。
- 最小行动：任何"我感觉会了"的断言，先用一次 quiz 验证，让客观成绩说话。
- 关联理论：可取难度（Bjork，流畅错觉同源）、测试效应（Karpicke 2008）。
- 自检：我的主观"会了"清单，和 report 的客观清单，重合度有多高？

> 结论：学习最大的敌人不是记不住，是"以为自己记住了"。元认知监控要做的，就是把虚幻的流畅感替换成诚实的提取成绩。self-learn-agent 的 `report` 与 `quiz` 就是你的校准仪——它冷酷地告诉你哪些点其实还不会。
