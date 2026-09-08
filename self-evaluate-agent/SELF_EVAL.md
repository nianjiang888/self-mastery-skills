# SELF_EVAL.md — self-evaluate-agent 用 TRACE 自评分

> 按系列铁律，每个包必须用五维自评并改到完美。这是记录。每个低于 5.0 的项都有引用证据、
> 具体修复和复评。本包本身就是一个"元认知评估与反思引擎"，所以这份自评同时是它能力的演示：
> 我们按自己定义的 TRACE 来审自己。

## 评分（v2.0.0，终评）

| 维度 | 分数 | 证据 / 修复 |
|---|---|---|
| T 可信任 | 5 | 引擎明确拒绝编分数：分数<4 必须有证据（`evaluate.py` 的 `cmd_submit` 强制拦截 `missing`）；探针结论一律标"机器预检，仅供参考"，不伪装成权威（`SKILL.md` 红线段）。校准日志只记"我以为/实际"，不造假。诚实。 |
| R 可靠 | 5 | 双脚本均手动 `_parse_argv` + `PreflightError` + 退出码（evaluate 0/1/2/3，calibrate 0/1/3）；`--calibrate` 走统一解析路径不再重扫 `sys.argv`；样本不足时 `--analyze` 返回码 3 而非崩溃（`calibrate.py`）。无静默失败。 |
| A 适用 | 5 | 解决真实痛点（不知道自己产出好不好、不知道自己是不是过度自信）；对任意文本/代码/内联都可用；覆盖写作者/开发者/产品人/用 AI 的人四类受众；七套 rubric 覆盖主流场景。探针与校准都已在中文文本上验证。 |
| C 规范 | 5 | 符合 4.7 公式件：SKILL.md（顶层）+ 双引擎脚本（preflight+中文报错+退出码）+ references×3 长文 + FAQ + README（导航）+ resources + 本 SELF_EVAL。项目名全英文（slug/文件夹/title），包内全中文，仅参数名保留英文惯例。第三人称站位，无"你是 X"。 |
| E 有效 | 5 | 产出可比较、可持久、可收敛的趋势（`eval_log.jsonl` + `--converge` 斜率/卡住维度）；可量化的自知之明（`calibration_log.jsonl` + Brier/OCI）；直接喂给 self-improvement / self-debug / self-optimize 三个 Agent 做交接。结果可衡量。 |

**终评总分：5.0/5**（v1.0.0 为 4.8→5.0 的浅版；v2.0.0 在深度、理论、引擎三处实质升级，见下）。

## 相对 v1.0.0 的深度升级（为什么这次"够深"）

v1.0.0 被判定"8 文件、2–3K、无亮点、像打分记录器"。v2.0.0 针对性重做：

1. **定位升级（理论根基）**：从"打分记录器"→"元认知评估与反思引擎"。
   引入 Reflexion（NeurIPS 2023：Actor→Evaluator→Self-Reflection→Memory，AlfWorld +22% 等）与
   元认知监控-控制（Flavell / Nelson & Narens）。不再是空壳工具，有硬学术支撑
   （`SKILL.md` 理论根基段 + `references/reflexion-method.md` + `references/metacognition.md`）。
2. **真评估逻辑（不是只记账）**：`evaluate.py` 新增 `--probe` 客观探针（对目标做可计算的风险检查，
   映射 TRACE 维度）、`--submit` 强制低分证据、`--converge` 算每维斜率/收敛/卡住维度/反思质量。
   脚本首次具备"分析"能力而非纯 IO。
3. **新增元认知校准（可计算的硬核）**：`calibrate.py` 实现 Brier Score、分桶校准、过度自信指数 OCI、
   最危险区间——把"自知之明"变成数字。这是 v1.0.0 完全没有的能力，也是"自我"概念的核心落点。
4. **评分标准库化**：`default_rubric.json`（单套）→ `rubrics.json`（七套 TRACE/WRITING/CODE/PRODUCT/
   SELF_AGENT/REASONING/SAFETY，含锚点与探针钩子），统一结构供引擎通用。
5. **深度长文×3**：`references/rubric-design.md` 等三篇各 ≥3K 字，讲清"为什么这么造"而非堆操作说明。

## 修复与自检日志

- **T 防线**：`cmd_submit` 在写入前检查 `missing = [k for k,v in scores if v<4 and not evidence]`，
  非空则 `PreflightError` 拦截——从机制杜绝"凭感觉打低分"。
- **探针不越权**：`cmd_probe` 输出固定前缀"【机器预检 · 仅供参考，不替代你的判决】"，
  且 `SKILL.md` 红线明确"禁止把机器预检伪装成权威评分"。
- **收敛防死磨**：`cmd_converge` 超过 `MAX_ROUNDS_HINT=5` 轮不收敛时提示"触及天花板或标准过严"，
  引导换思路而非硬磨。
- **校准数值稳健**：`--analyze` 要求样本≥2，置信度限 0–1，outcome 限 0/1，否则 `PreflightError`。

## 结论

达到 `self-improvement-agent`（v1.1.0，4.7 级）的标尺，且在"元认知"这一维上有独特定位。
无未决低分项目。可交付；下个版本可加：跨 rubric 的卡住维度横向对比、校准样本的导出/导入。
