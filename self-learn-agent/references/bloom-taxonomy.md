# Bloom 教育目标分类学：把"学会"拆成可操作的层级

## 一、理论源流与权威出处

Bloom 教育目标分类学由美国教育心理学家 Benjamin Bloom 领衔的委员会于 1956 年首次发表，原始文献为 *Bloom, B. S. (Ed.). (1956). Taxonomy of Educational Objectives: The Classification of Educational Goals. Handbook I: Cognitive Domain. New York: Longmans, Green.* 这份文献把教育的"认知目标"从低到高排成六个层级：知识（Knowledge）、理解（Comprehension）、应用（Application）、分析（Analysis）、综合（Synthesis）、评价（Evaluation）。它长期是课程设计、测验命题与学习评估的底层框架。

2001 年，以 Lorin Anderson 与 David Krathwohl 为首的小组发布了修订版，文献为 *Anderson, L. W., & Krathwohl, D. R. (Eds.). (2001). A Taxonomy for Learning, Teaching, and Assessing: A Revision of Bloom's Taxonomy of Educational Objectives. New York: Longman.* 修订版做了两处关键改动：第一，把名词改成动词，强调"要做的事"——记忆（remember）、理解（understand）、应用（apply）、分析（analyze）、评价（evaluate）、创造（create）；第二，引入"知识维度"与"认知过程维度"的二维矩阵，知识维度分为事实性（factual）、概念性（conceptual）、程序性（procedural）、元认知（metacognitive）四类。这一修订让分类学从"考什么"转向"怎么学"，与 self-learn-agent 的消化逻辑高度契合。

## 二、为什么它对"知识消化"是地基

大多数人读书的瓶颈不在"读得少"，而在"停在第一层"。他们记住了术语（事实性知识），却没走到理解（能用自己的话解释）、应用（能换情景使用）、分析（能拆结构）、评价（能判断优劣）、创造（能组合出新东西）。Anderson 与 Krathwohl 的二维模型点破要害：同一事实，可以只"记住"，也可以上升到"创造"——这取决于你施加的认知过程深度。

self-learn-agent 的 `ingest` 子命令要求填写"concept（原子概念）"与"note（我的消化）"，正是强迫学习从"记忆"跨到"理解"；而 `elaborate` 子命令的"为什么/如何/与什么相关"三问，恰好覆盖了分析→评价的链路；`interleave` 与 `quiz` 则把知识推进到"应用"层。换句话说，本引擎的六个子命令，几乎是一张 Bloom 修订版认知过程维度的操作化地图。

## 三、二维矩阵如何指导复习排序

修订版最有用的地方是"知识维度 × 认知过程维度"的矩阵。事实性知识靠重复就能记牢，但概念性与程序性知识必须在"应用—分析—创造"层反复打磨才真正内化。这意味着：

1. 事实性知识（如定义、公式、人名）适合短间隔、高频的 `quiz` 主动回忆；
2. 概念性知识（如"什么是认知负荷"）适合 `elaborate` 精细质询，逼出"为什么"；
3. 程序性知识（如"如何做间隔复习调度"）适合 `interleave` 交错练习，在不同情境里迁移；
4. 元认知知识（"我哪里容易错"）适合 `report` 的掌握度反查，校准自我判断。

## 四、常见误用与纠正

误用一：把"读完一章"当成"学会"。读完只停在记忆层，没有理解与应用，遗忘曲线会很快把信息抹掉。纠正：每读完一节，至少做一次 `elaborate` 或一次 `quiz`。误用二：只做低层练习。反复抄写概念等于重复记忆层，无法抵达分析/创造。纠正：用 Bloom 的"动词"自检——你能"解释"吗？能"使用"吗？能"判断"吗？能"设计"吗？误用三：忽视知识维度。把程序性知识当事实背，结果是"看得懂做不出"。纠正：程序性知识必须配合实操（交错练习、真实任务）。

## 五、与后续理论的衔接

Bloom 提供了"学什么深度"的框架，但没解决"怎么记得牢"。后续理论正好补足：Ebbinghaus 与间隔重复解决"遗忘"，Karpicke 的测试效应解决"提取"，Fiorella & Mayer 的生成学习解决"意义建构"，Sweller 的认知负荷解决"效率"。本包把 Bloom 作为顶层坐标系，其余理论作为底层引擎，构成完整的"消化—固化—迁移"闭环。

## 六、可核验要点（来自原始文献）

- 1956 原始版六层级：Knowledge / Comprehension / Application / Analysis / Synthesis / Evaluation。
- 2001 修订版六动词：remember / understand / apply / analyze / evaluate / create。
- 二维模型：知识维度（factual / conceptual / procedural / metacognitive）× 认知过程维度。
- 权威文献：Bloom (1956) *Taxonomy of Educational Objectives, Handbook I*；Anderson & Krathwohl (2001) *A Taxonomy for Learning, Teaching, and Assessing*。

## 七、实践落地：用 self-learn-agent 走完六层

把任意一章书按 Bloom 六动词拆成任务链，逐层调用子命令：

1. **remember（记忆）**：`ingest` 录入原子概念与原文定义，建立事实底。
2. **understand（理解）**：在 `ingest` 的 note 里用自己的话重述，不抄原文。
3. **apply（应用）**：`interleave` 把该概念与易混概念混排，逼自己辨别并套用。
4. **analyze（分析）**：`elaborate --how` 拆解其结构、前提、边界条件。
5. **evaluate（评价）**：`elaborate --relate` 对比同类理论的优劣与适用场景。
6. **create（创造）**：用 `quiz` 自测后，尝试把该概念组合进自己的项目/文章。

每完成一层，`report` 会反映掌握度变化；若某层卡住（mastery 不升），说明该层认知过程没真正发生，需回到对应子命令补做。

## 八、与其他理论的协同网络

- Bloom 定"深度标尺"，认知负荷理论（CLT）定"每层该投多少资源"——低层可批量，高层需慢工。
- Bloom 的"应用/分析"直接对应交错练习的"辨别"，因为辨别是应用的前提。
- Bloom 的"理解"对应精细质询的"为什么"，二者都在生成因果链。
- Bloom 的"创造"对应生成式学习的 teaching/enacting，都是输出型深加工。

## 九、常见错误自查表

- [ ] 我是否把"读完"等同于"学会"？（应至少做一次 quiz/elaborate）
- [ ] 我的 note 是自己的话还是抄原文？（抄写 = 记忆层，无效）
- [ ] 我是否只练了低层、从不敢应用？（用 interleave 逼自己辨别）
- [ ] 我是否定期用 report 核对各概念的深度分布？（避免全员停在记忆层）

## 十、常见问答深挖

问：Bloom 与"布鲁姆"是不是同一个人？ 答：是，Benjamin Bloom 的中文译名常作"布鲁姆"，1956 年分类学即出自其委员会，不必困惑于译名差异。

问：修订版把 Synthesis 换成 Create，仅仅是换词吗？ 答：不是。原版的 Synthesis（综合）偏"拼合已有要素"，修订版的 Create（创造）更强调"产出新颖、原创的成果"，并把"创造"放在认知过程的最高层，凸显其在深度学习中的顶点位置。这一定位让"创造"从可有可无变成必须训练的能力。

问：能不能跳过低层直接练"创造"？ 答：不行。创造建立在事实性、概念性知识之上；没有底层的"记住—理解—应用"，高层的"分析—评价—创造"就是空中楼阁。self-learn-agent 的 `ingest` 先打事实底，再逐层往上走，正是遵循这个依赖顺序。

问：二维矩阵怎么用最省力？ 答：先给每个知识点标"知识维度"（事实/概念/程序/元认知），再决定"认知过程"该走到哪层。事实性知识走到 apply 即可，程序性知识必须走到 create 才算真会——这直接决定了你该用 `quiz`、`elaborate` 还是 `interleave`。

> 结论：Bloom 分类学不是记忆术，而是"学习深度的标尺"。self-learn-agent 的每个子命令都对应一档认知过程，用它来校准自己停在了哪一层，是抗遗忘的第一道防线。
