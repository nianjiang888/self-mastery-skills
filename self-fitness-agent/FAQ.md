# self-fitness-agent 常见问题（FAQ）

**1. 我是完全新手，从哪开始？**
先用 `set --target_freq 3` 设目标，然后每周用 `log` 记 3 次全身训练（推/拉/蹲/核心各一两个动作）。记满 2–3 周再让 Agent 跑 `trend` / `plan`，数据太少时它只会提示"先积累"。

**2. 每次都要记那么多项吗？**
不用。最低限度是 `--date --type_sub --duration --rpe`；`--sets --reps --weight --parts` 对力量训练建议补，`--sleep_prev --sore` 补了才能用恢复评估。少填不影响记录，只是分析浅一点。

**3. ACWR 是什么？为什么它报警？**
急性:慢性负荷比 = 近 7 天负荷 ÷ 近 4 周平均周负荷。它在 0.8–1.3 最安全；>1.5 说明你最近猛加量，软组织损伤风险高，Agent 会让你降量加恢复日。详见 `references/training-load-injury-acwr.md`。

**4. 为什么我加量了 Agent 反而让我减量？**
因为加太快（ACWR 突破 1.5）比加得慢更伤。它要的是"可持续的渐进"，不是"狠一次"。这也是 `references/progressive-overload.md` 的核心。

**5. 报告退出码 1 是出错了吗？**
不是。退出码 1 表示"存在弱项/风险"，是 Agent 在提醒你关注，属于正常业务信号，可被脚本用来触发后续动作。

**6. 我酸痛好几天，是不是练伤了？**
延迟性酸痛（DOMS）24–72 小时达峰、几天自愈，是正常适应；但关节锐痛、某个点剧痛、力量断崖下跌是损伤信号，要停。Agent 把"酸痛均值 >6"列为恢复不足预警。详见 `references/doms-recovery.md`。

**7. 恢复分怎么算的？**
由 ACWR、单调性、前夜睡眠评分、酸痛均值合成 0–100 分。睡眠差或酸痛重会显著拉低分数并提示加恢复日。

**8. 我想增肌该练几次？**
每肌群每周 10–20 组是起点，频率高低差异不大、总量才重要。新手从全身 3 次起步最稳。详见 `references/hypertrophy-mechanisms.md` 与 `training-frequency.md`。

**9. 减脂期还要力量训练吗？**
要。减脂期保肌靠力量训练 + 足够蛋白质，否则掉的多是肌肉不是脂肪。详见 `references/protein-nutrition.md`。

**10. 心率区间有必要记吗？**
有氧训练记 `--zone 1–5` 能让 Agent 看强度分布是否失衡（全堆 Z5 会预警）。没设备用"说话测试"近似也行。详见 `references/heart-rate-zones.md`。

**11. 训练前一定要热身吗？**
建议 5–10 分钟专项动态热身，能降低损伤、提升表现；训练后做静态拉伸。详见 `references/warmup-injury-prevention.md`。

**12. 我每天坐办公室，训练还有用吗？**
有用，但久坐的代价训练抵消不了。把日常 NEAT（多走、多站、多起身）也计入全局，恢复日散步比瘫坐好。详见 `references/sedentary-neat.md`。

**13. 怎么判断自己是不是过度训练？**
持续 2 周以上表现下滑、静息心率升高、睡眠情绪变差、易感染——先减量 1 周，不回血要警惕 OTS，走正规运动医学。Agent 的 `recover`/`risk` 只做前哨预警。详见 `references/overtraining-syndrome.md`。

**14. 数据存在哪？安全吗？**
全在本地 `--data` 目录的 `events.jsonl` + `profile.json` + `reports/`，不上传、不联网，可随时备份或删除。重记同一天同类型会自动覆盖，不会重复计数。
