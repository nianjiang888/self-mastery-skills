# 完整样例：从零记一次，到出报告

照抄即可跑通。全程约 2 分钟。

## 场景设定

小林，32 岁，产品主管。最近两个月跟家里人连着吵了三次，跟下属提意见对方就防御。
他想知道自己到底卡在哪。

## 1）设档案

```bash
python scripts/comm.py --data ./my_comm set \
  --focus_scene 冲突 --focus_relation 家人 --target_outcome 4 \
  --note "最近跟家里人总吵，想先搞清楚问题在哪"
```

输出：

```
已更新沟通档案：{"focus_scene": "冲突", "focus_relation": "家人", "target_outcome": 4.0, "note": "最近跟家里人总吵，想先搞清楚问题在哪"}
```

## 2）记六次对话

谈崩的三次（信息量最大）：

```bash
python scripts/comm.py --data ./my_comm log --date 2026-08-25 \
  --scene 冲突 --counterpart 家人 --goal 关系 \
  --tone 9 --listened 2 --reaction 对抗 --outcome 1 --aftermath -2 \
  --words "你从来都不理解我"

python scripts/comm.py --data ./my_comm log --date 2026-08-27 \
  --scene 冲突 --counterpart 家人 --goal 关系 \
  --tone 8 --listened 2 --reaction 防御 --outcome 2 --aftermath -1

python scripts/comm.py --data ./my_comm log --date 2026-08-29 \
  --scene 反馈 --counterpart 同事 --goal 达成 \
  --tone 6 --listened 3 --reaction 防御 --outcome 2 --aftermath 0 \
  --words "你这个方案逻辑不对"
```

顺利的三次（对照组，同样重要）：

```bash
python scripts/comm.py --data ./my_comm log --date 2026-08-28 \
  --scene 汇报 --counterpart 上级 --goal 信息 \
  --tone 3 --listened 3 --reaction 合作 --outcome 4 --aftermath 1

python scripts/comm.py --data ./my_comm log --date 2026-08-30 \
  --scene 谈判 --counterpart 客户 --goal 达成 \
  --tone 5 --listened 4 --reaction 中立 --outcome 3 --aftermath 0

python scripts/comm.py --data ./my_comm log --date 2026-08-31 \
  --scene 请求 --counterpart 同事 --goal 达成 \
  --tone 2 --listened 4 --reaction 合作 --outcome 5 --aftermath 1 \
  --better "先说要什么，再给理由，最后留拒绝空间"
```

每条记录后，引擎会立刻告诉你卡在哪一层：

```
已记录 2026-08-25 [冲突/家人] 达成 1 对方对抗 关系-2 → 卡在「身份」层 id=2026-08-25#1
  提示：这一层最难谈。问题不在事情本身，在面子/自我形象。
```

## 3）看全景

```bash
python scripts/comm.py --data ./my_comm trend --days 30
```

输出：

```
近 30 天沟通概览（6 条记录）：
  平均达成 3.00 / 5 | 防御率 50.0% | 对抗率 16.7%
  情绪强度均值 5.17 / 10（高强度占比 33.3%） | 倾听分 3.00 / 5
  关系账户 -0.17（-2 最差 +2 最好）| 身份层冲突占比 33.3%
  情绪代价 -2.25 分（高情绪组达成 − 低情绪组达成）：情绪拖累结果
  分场景达成：冲突 1.50(2次)，谈判 3.00(1次)，反馈 3.00(1次)，汇报 4.00(1次)，请求 5.00(1次)
  分对象关系：家人 -1.50(2次)，客户 +0.00(1次)，上级 +1.00(1次)，同事 +0.50(2次)
```

**读出来的三件事**：
1. 情绪代价 −2.25——他上头时说的话，达成率比平时低 2.25 分。这不是劝告，是他自己的数字。
2. 最弱场景是「冲突」，平均达成 1.50。
3. 跟「家人」的对话后，关系平均 −1.50。这段关系在被消耗。

## 4）复盘单条

```bash
python scripts/comm.py --data ./my_comm review --id 2026-08-25#1
```

输出：

```
复盘 2026-08-25#1  [冲突 × 家人]
  目标：关系 | 结果满意度 1/5 | 对方反应：对抗
  我当时情绪 9/10 | 倾听 2/5 | 事后关系 -2
  原话：你从来都不理解我

  卡在哪一层：身份
    → 这是最硬的一层。对方不是不同意你的事实，而是觉得「我这个人被否定了」。
    → 换法：把「你不对」换成「我的理解是…你看是不是这样」；先肯定对方的出发点，再谈分歧。
  还没写下「下次怎么说」。补一句：
    python scripts/comm.py --data <目录> log --id 2026-08-25#1 ... --better "下次我想这么说：..."
```

## 5）拿话术

```bash
python scripts/comm.py --data ./my_comm script --scene 冲突 --goal 关系
```

输出（节选第一套）：

```
场景「冲突」× 目标「关系」的话术模板（共命中 5 套，取最适的 3 套）：

【非暴力沟通四步（观察 / 感受 / 需要 / 请求）】Rosenberg 2003《Nonviolent Communication》
  1. 说观察：只讲事实，不带评判。「这周的三次会议你都晚了十分钟」而不是「你总是迟到」
  2. 说感受：用情绪词，不用「我觉得你…」这种伪装的指责。
  3. 说需要：说出你真正在意的东西。
  4. 说请求：具体、可执行、可拒绝。
  示例：「这周三次会你都晚了十分钟（观察），我有点着急（感受），因为我需要按计划推进（需要）。下次能不能提前五分钟，来不及就发我一条消息？（请求）」
  避免：把观察和评判混在一起。一旦对方听到「你总是」「你从来」，四步就全废了。
```

注意最后那句「避免」——正好命中他说的「你从来都不理解我」。

## 6）扫描模式

```bash
python scripts/comm.py --data ./my_comm risk --days 30
```

输出：

```
沟通风险与模式扫描（近 30 天，6 条）：
  平均达成 3.00 | 防御率 50.0% | 关系账户 -0.17 | 倾听 3.00
  [高] 关系账户平均 -0.17（负），对话在持续消耗关系
  [中] 情绪代价 -2.25 分：情绪上头时达成率明显更低
  [中] 整体防御率 50.0%（≥40%），对方经常进入防御状态
  [中] 最弱场景是「冲突」：2 次平均达成仅 1.50
  [中] 和「家人」的对话后关系平均 -1.50（负），这段关系在被消耗
  [低] 话术沉淀率 16.7%（<30%），复盘了但没留下下次怎么说
  优先行动：接下来一周只做一件事：任何对话结束后加一句关系修复（先认可对方这个人，再谈事）
```

退出码为 `1`（存在中/高严重度模式），agent 看到会主动介入。

## 7）本周只练一个

```bash
python scripts/comm.py --data ./my_comm plan --days 30
```

输出：

```
本周最值得练的一个：
  [高] 关系账户平均 -0.17（负），对话在持续消耗关系
  → 行动：接下来一周只做一件事：任何对话结束后加一句关系修复（先认可对方这个人，再谈事）。
  （另有 5 项次要模式，跑 risk 看全部）
  配套：跑 script --scene 冲突 --goal 关系 拿结构化说法
```

**只练这一个动作。** 同时改三个，你永远不会知道哪个起作用。

## 8）出报告

```bash
python scripts/comm.py --data ./my_comm report --days 30
```

落盘到 `reports/comm-<日期>.md`，含全景指标、模式与行动、以及逐条记录（包括你写下的「下次怎么说」）。

## 落盘的数据

```
my_comm/
├── events.jsonl                  # 按 type+id 幂等，记错可重记覆盖
├── profile.json                  # 沟通档案
└── reports/
    └── comm-2026-09-01.md        # 完整报告
```

`events.jsonl` 每行一条：

```json
{"type": "comm", "id": "2026-08-25#1", "date": "2026-08-25", "scene": "冲突", "counterpart": "家人", "goal": "关系", "tone": 9.0, "listened": 2.0, "reaction": "对抗", "outcome": 1.0, "aftermath": -2.0, "layer": "", "words": "你从来都不理解我", "better": "", "ts": "2026-09-01 16:20:11"}
```

注意 `"layer": ""` 是空的——层次由引擎在读取时推断，不写死在记录里。这样以后调整推断规则，历史数据会自动跟着更新。
