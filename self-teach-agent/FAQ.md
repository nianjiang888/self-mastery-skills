# 常见问题（FAQ）

**Q：self-teach 和 self-evaluate / self-optimize 有什么区别？**
A：三个是"自我"血脉的不同环。evaluate 是**给产出打分反思**（质量视角）；optimize 是**把分数当目标函数做受控实验**（改进视角）；teach 是**把外部知识内化成本领**（学习视角）。简单说：evaluate 看"好不好"，optimize 看"能不能更好"，teach 看"我学会了没"。teach 的晋升门禁和 verify 一样严格——不达标物理拦下。

**Q：脚本真的能"教"我吗？**
A：不能，也不该。self-teach 不替你理解，它管的是**闭环与证据**：把材料拆成单元、检查你有没有补全四要素、按难度排学习计划、算复习日程、在覆盖达标时才允许"晋升为本领"。真正的思考是你（或 Agent）做的。它拒绝"喂一段就声称学会了"。

**Q：为什么 promote 会失败？**
A：这是设计，不是 bug。promote 要求**覆盖 100%**（每个单元都有 concept/definition/why/example）且（若提供评分）**回忆评分全 ≥4**。任何一项不达标都返回非零退出码，可被 CI / 工作流拦下。这继承了 STaR "只留对的" 精神，杜绝 Self-Instruct 式的虚假掌握。

**Q：没有评分文件（--grades）也能 promote 吗？**
A：能，但只卡"四要素覆盖"。建议补一份 `单元名→评分(0-5)` 的 json 传给 `--grades`，让门禁同时卡"能回忆"，更接近真实掌握。

**Q：curriculum.py 报"先修环"是什么？**
A：你的大纲里 A 先修 B、B 又先修 A（或更长回路），无法排出合法顺序。检查 `resources/sources.json` 之外你自己写的大纲，打破环即可。

**Q：retention.py 的 SM-2 参数能改吗？**
A：能，全在 `resources/retention_schedule.json`：初始易度、最小易度、首两次间隔、评分阈值。若你某领域忘得特别快，把间隔序列整体砍半即可。

**Q：学完的东西怎么真正变成能力？**
A：teach 管"不忘"，但复杂技能最终要在 self-optimize / self-debug 的**真实使用**里固化。建议 promote 后，把本领同步进 self-improvement-agent 的永久记忆，或抽成独立技能——这就是"教自己"到"长成本领"的最后一跃。

**Q：材料是别人的版权内容，能摄入吗？**
A：摄入仅限个人内化使用；不要把未授权内容当作自己"产出"再分发。self-teach 是学习引擎，不是洗稿工具。
