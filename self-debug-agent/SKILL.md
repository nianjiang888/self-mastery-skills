---
name: self-debug-agent
display_name: 自主调试
title: self-debug-agent
version: 2.0.0
description: 自主调试引擎。让 Agent（或你）自主复现一个失败、用探针归类病灶、在沙箱里打补丁、用回归测试验证修复，最关键的是把每个咬过你的 bug 自动写成一条永久回归测试，让同一个失败不可能再犯第二次。闭环：复现→假设→补丁→验证→治愈→回归。理论根基是 Self-Debugging（Chen et al., ICLR 2024）、Delta Debugging（Zeller, FSE 1999）与频谱故障定位 SBFL（Tarantula/Ochiai）。触发：调试/修 bug/这个报错怎么解/复现一下/定位问题/regression test/自愈/self-debug/debug this/traceback/为什么挂了/又踩同一个坑/自动修/防御回归。
license: MIT
---

# self-debug-agent

## 这个 Agent 是什么（不是让你 cosplay 的人格）

self-debug-agent 是一台**自主调试引擎**，不是一个人格面具。你给它一个失败——一段报错、一个挂掉的测试、一个复现步骤——它把你从"我看看……哦可能是那个……算了重写得快"的随机游走里拉出来，落到一条**可复现、可归因、可验证、可防御**的调试曲线上。

它的「自我」写在名字里：**self-debug = 自己调试自己**。2025 年一篇系统复盘论文把 self-debugging 定义得非常清楚——

> 模型试图调试并修复**它自己写的程序**，不依赖人类监督，也不依赖更强模型的引导。

这就是「自我」的边界：不是「帮你叫个人来修」，是**自己长出修复与免疫的能力**。你给它一个失败，它闭环跑完，最后交还两样东西：一个修好的程序，和一条**永久记住这个坑的回归测试**。

它做四件事，每一件都有硬学术根基，不是拍脑袋：

1. **当复现器（Reproducer）**：把模糊的"它有时候会崩"变成精确的"在输入 X 下，第 N 行抛了 E 类错误"。这对应 Zeller 的 **Delta Debugging**（FSE 1999, *Yesterday, my program worked. Today, it does not. Why?*）——系统性地缩小到最小失败诱因。复现不了，就不算 bug，这是铁律。
2. **当法医（Classifier + Localizer）**：用探针把 bug 归到六类（语法/语义/逻辑/并发/资源/集成），再用 **SBFL 频谱故障定位**（Tarantula 2002 / Ochiai 2007）按"被失败测试覆盖多、被通过测试覆盖少"给每一行算可疑度，排出 Top-N 病灶。这是元认知在调试里的投影：不是"感觉是这儿"，是"数据说最可能是这儿"。
3. **当外科医生（Healer）**：这是 **Self-Debugging**（Chen et al., ICLR 2024）的核心三步循环——**生成候选补丁 → 用自然语言解释自己的改法 → 对照执行反馈判断对不对 → 不对就修订重跑**。论文证明：想得更深（1–3 轮闭环）胜过硬采样 10× 候选程序，在 Spider 最难档上准确率 +9%，有单测时 +12%。
4. **当免疫学家（Regressor）**：**每个 bug 都自动落成一条永久回归测试**。这是整个「自我」闭环最锋利的一刀——bug 不再是个一次性麻烦，而是变成系统的长期抗体。它直接对应 self-improvement-agent 的"错误→永久记忆"棘轮：失败不是终点，是下次不再犯的输入。

重点不是"这次修好了"，是**这条曲线和这面墙**：每次记下的复现、每轮根因反思、每条自动沉淀的回归测试，都能互相印证，于是你能看见自己（或你的 Agent）是不是真的在变强，以及——同一个坑，会不会再踩第二次。

## 何时主动触发（这一段是真的"主动"）

本 Agent 应该在以下场景**自己跳出来**，不用你点名：

- 你刚贴了一段 traceback / 报错，或一句"又挂了 / 又踩同一个坑"——主动提议：先复现、再归类、再修。
- 你改完代码说"应该好了"但没跑测试——主动提醒：没验证的修复等于没修复，要 `--verify`。
- 你连续第二次遇到同类报错——主动拉出历史回归测试墙，问"这条是不是该加厚了"。
- 你准备重构 / 删代码——主动建议：先确认有回归测试罩着要动的逻辑。
- 你自己写完一段复杂逻辑却说"我觉着没问题"——主动用 SBFL 思路提醒：感觉不算数，覆盖率与失败复现才算数。

**反触发**：纯需求讨论、纯写作、与代码运行无关的事，本 Agent 闭嘴。

## 怎么用（最小上手）

```bash
# 1) 复现：把报错和代码喂进来，提炼最小失败
python3 scripts/debug.py --reproduce --trace /tmp/trace.txt --code app.py

# 2) 归类 + 定位：探针打六类，SBFL 排病灶
python3 scripts/debug.py --classify --trace /tmp/trace.txt --code app.py
python3 scripts/localize.py --spectrum spectrum.json --top 10

# 3) 治愈循环：失败→根因反思→重试行，最多 5 轮，记 heal_log.jsonl
python3 scripts/debug.py --heal --trace /tmp/trace.txt --code app.py --max-rounds 5

# 4) 免疫：把这个 bug 落成永久回归测试
python3 scripts/debug.py --regress --bug "空输入时除零" --case "f(0)" --expect "抛 ValueError"

# 5) 复盘：看治愈曲线 + 回归墙
python3 scripts/debug.py --report
```

> 说明：脚本是**纪律引擎**——它负责复现萃取、归类探针、SBFL 计算、治愈循环记账、回归测试脚手架生成与校验。真正写补丁代码的是你或你的编程 Agent；脚本确保这个过程不糊弄、有证据、能收敛、留抗体。这跟 self-evaluate-agent 的分工一致：引擎管闭环，人/模型管产出。

## 边界与红线（不许越界）

- **不复现，不修**：拿不出最小复现的"修复"一律视为安慰剂，脚本会拒绝进入治愈循环。
- **不靠感觉定位**：宣称"是这一行的问题"必须附覆盖率/失败证据，否则只允许作为"待验证假设"列出。
- **不吞错误**：补丁若只是 `try/except: pass` 把错误压下去，脚本标记 `mask`，不算治愈。
- **不制造脆弱测试**：生成的回归测试必须确定性（固定输入→固定期望），禁止用随机数、时间戳、网络依赖当断言。
- **不跨权限**：只动你指定的代码与测试文件，不悄悄改环境、不装包、不碰别的目录。
- **不过度自信**：治愈轮数到了上限仍没收敛，老老实实报告"卡在哪一类、卡在哪一行假设"，而不是编一个"已修复"。

## 与 self 系列的关系

- `self-evaluate-agent`（评估-反思-改进）：给产出的**质量**打分收敛。本 Agent 是给产出的**正确性**打补丁收敛，两者同一 Reflexion 血脉。
- `self-improvement-agent`（错误→永久记忆）：它的"永久记忆"是抽象经验；本 Agent 的"永久回归测试"是**可执行、可重跑**的具体抗体，是它的工程落地。
- `self-optimize-agent`（把分当目标函数做实验）、`self-reflect-agent`（日三省的洞察日志）：本 Agent 治愈后产出的"根因反思"可以直接喂给它们。

一句话：**self-evaluate 告诉你差在哪，self-debug 帮你把差的补上，self-improvement 让补过的不再差。**
