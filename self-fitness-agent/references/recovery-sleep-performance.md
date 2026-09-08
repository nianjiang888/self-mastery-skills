# 恢复与睡眠：训练只是刺激，睡眠才是兑现

## 一、核心结论
练得再科学，没有恢复就等于零增长，甚至负增长。**睡眠是恢复的母舰**：生长激素在深睡期脉冲式释放、肌肉蛋白合成在睡眠中加速、神经系统在睡眠中"重演"动作巩固神经适应。Watson 等研究直接把睡眠时长与运动表现、受伤风险挂钩——睡不够的人，训练反应更差、受伤更多。这也正是 self 系列把 fitness 和 sleep 做成两个互相呼应的 Agent 的原因。

## 二、睡眠如何影响适应
- **激素**：深睡期生长激素分泌，驱动组织修复；
- **合成**：睡眠中肌肉蛋白合成率上升；
- **神经**：动作模式在睡眠中巩固，第二天动作更"自动"；
- **认知**：反应速度、决策、疼痛耐受都依赖睡眠。

## 三、量化衔接
self-fitness-agent 允许在 `log` 里填"前夜睡眠评分"和"酸痛"。当这些偏低时，引擎的 `recover` 会下调恢复分并提示"先睡好再加压"。这把 sleep Agent 的输出（你的睡眠质量趋势）直接变成 fitness Agent 的输入信号。

## 四、实战推演
你这周加了量（ACWR 1.2，安全），但连续三天前夜睡眠只有 5 分。`recover` 给出恢复分 60 以下 → 正确做法是这周保留量但加 1–2 个恢复日，并把睡眠优先级提到训练之前。等到睡眠回到 7+ 分，再加量才安全。

## 五、速查卡
- 训练日目标 7–9 小时睡眠；
- 大重量日尽量安排在前夜睡好的日子；
- 睡眠连续 <6 小时，宁可降量也别硬冲。

## 六、深度问答
**Q：补觉能抵消熬夜吗？** 部分能补，但昼夜节律和社会时差会打乱，不能长期替代规律睡眠（见 self-sleep-agent）。
**Q：午睡有用吗？** 20–30 分钟小睡可缓解睡眠惯性、提升下午表现，但别超过 1 小时以免夜里难入睡。

## 七、出处
- Watson AM. Sleep and athletic performance. *Sleep Med Clin*. 2017;12(4):563-573. (See also Watson NF, et al. Sleep duration and risk of injury in college athletes. *Sleep*. 2017;40(1):zsx019.)
- Strength and conditioning consensus on sleep (National Sleep Foundation / NCAA guidance, 2010s).
- Walker MP. *Why We Sleep*. Scribner; 2017. (科普延伸)
