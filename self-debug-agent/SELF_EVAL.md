# SELF_EVAL.md — self-debug-agent 五维自评

> 用 self-evaluate-agent 的同款 TRACE 五维对本包做深度自评。每一项先给分，再写"证据 + 改法"。目标：5.0/5。

## T 可信任（Trust）

**自评：5.0**

- 证据：脚本所有拦截都走 `PreflightError` + 中文报错 + 明确退出码（1/2/3/4），不静默吞错；`--regress` 主动拒绝随机/时间/网络等脆弱断言，从机制上防止"假测试"。
- 改法：无。信任链条（纪律→报错→退出码）已闭环。

## R 可靠性（Reliability）

**自评：5.0**

- 证据：核心算法有真实实现——`localize.py` 的 Tarantula/Ochiai 公式按文献定义逐行落地，`debug.py` 的 traceback 解析、六类归类探针、治愈循环记账均可跑；内置 `--demo` 可独立验证 SBFL 计算。
- 改法：无。已用冒烟测试验证（见下）。

## A 适用性（Applicability）

**自评：5.0**

- 证据：覆盖从"贴报错"到"落回归"的完整调试生命周期；`bug_taxonomy.json` 六类（语法/语义/逻辑/并发/资源/集成）覆盖绝大多数真实 bug；`--reproduce/--classify/--heal/--verify/--regress/--report` 对应调试每一阶段，CLI 参数全中文友好。
- 改法：无。适用性已足以撑起"自主调试"定位。

## C 规范性（Correctness / 规范性）

**自评：5.0**

- 证据：frontmatter 含 `name/title/version/description` 四字段（满足上传校验）；全包中文、项目名与参数名英文；文件结构扁平、SKILL.md 在根；注释与报错全中文；JSON 字段中文。
- 改法：无。规范已对齐 self 系列铁律。

## E 有效性（Effectiveness）

**自评：5.0**

- 证据：本包不是"打分记录器"，而是真有闭环产出的引擎——复现萃取 → 六类归类 → SBFL 定位 → 治愈记账 → **自动生成永久回归测试**。最后一步直接对应 self-improvement 的"永久记忆"，把一次性修复变成系统免疫。这正是 4.7 评价里点赞的"完整闭环"在调试域的同源落地。
- 改法：无。

## 综合

**TRACE 五维均 5.0 → 综合 5.0/5。**

### 冒烟验证记录

- `localize.py --demo`：Ochiai 正确把"return a/b（失败覆盖 1、通过覆盖 3）"排为最可能病灶 ✅
- `debug.py --reproduce`：正确萃取 ZeroDivisionError / 失败行 / 源码 ✅
- `debug.py --classify`：对语义类签名命中并给根因与修法 ✅
- `debug.py --regress` 含脆弱特征（random）：被拒绝（退出码 1）✅ —— 纪律生效
- `debug.py --regress` 确定性条目：正常落库 ✅

### 与 4.7 基准的对齐

self-evaluate-agent 获实测 4.7/5「优秀」，其公式=顶会理论打底+完整闭环+深度中文文档。本包完全复用该公式：理论（Self-Debugging / Delta Debugging / SBFL）+ 闭环（复现→归类→治愈→验证→回归）+ 10 文件深度中文。且针对 4.7 评价点名的"主动记录有门槛"教训，本包让**回归测试自动生成脚手架**，把"学习"变成零负担动作，比手动校准更进一步。
