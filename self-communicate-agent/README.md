# self-communicate-agent 使用说明

沟通表达复盘 AI Agent。**记一次 30 秒，每月花 5 分钟看模式。**

## 30 秒上手

```bash
# 1) 记一次重要对话（outcome 必填，其余可省）
python scripts/comm.py --data ./my_comm log --scene 冲突 --counterpart 家人 \
  --outcome 1 --reaction 对抗 --tone 9 --aftermath -2

# 2) 看全景
python scripts/comm.py --data ./my_comm trend --days 30

# 3) 本周只练一个
python scripts/comm.py --data ./my_comm plan --days 30
```

要求：Python 3.8+，**零第三方依赖**（纯标准库）。

## 建议的使用节奏

| 阶段 | 做什么 | 为什么 |
|---|---|---|
| 前两周 | 只 `log`，重要对话后 24 小时内记 | 拖过三天，记忆已经被加工过了 |
| 第 5 条之后 | 跑 `trend` 和 `risk`，看模式 | 少于 5 条记录引擎不做模式判定 |
| 每次复盘 | 至少写一句 `--better` | 复盘的核心产出不是反思，是一句「下次我想怎么说」 |
| 每月 | `report` 出完整报告 | 看分场景、分对象的长期走向 |

**优先复盘谈崩的那些。** 成功的对话信息量小——你不知道是哪个动作起了作用。失败的对话能精确定位问题。

## 文件导航

| 文件 | 内容 |
|---|---|
| `SKILL.md` | 主文档：能力、主动触发、理论地图、命令速查、边界 |
| `scripts/comm.py` | 引擎（纯标准库，确定性、可重跑） |
| `resources/communication-scripts.json` | 10 套结构化话术模板，每套带出处（供 `script` 检索） |
| `resources/communication-models.json` | 各指标算法定义、阈值与文献出处 |
| `resources/communication-domains.json` | 字段口径、弱项规则、退出码、边界声明 |
| `references/*.md` | 14 篇方法论长文，每篇带年份+期刊/书名出处 |
| `examples/sample-comm-log.md` | 端到端完整样例（照抄即可跑通） |
| `FAQ.md` | 常见场景对照与误用提醒 |
| `SELF_EVAL.md` | 自评（TRACE 五维） |
| `CHANGELOG.md` | 版本记录 |

## 子命令速查

| 命令 | 作用 | 关键参数 |
|---|---|---|
| `set` | 设沟通档案 | --focus_scene --focus_relation --target_outcome --note |
| `log` | 记一次重要对话 | --date --scene --counterpart --goal --tone --listened --reaction --outcome --aftermath --layer --words --better --id |
| `trend` | 沟通全景统计 | --days（默认 30） |
| `review` | 单条复盘（拆三层） | --id（留空复盘最近一条） |
| `script` | 按场景×目标拿话术 | --scene --goal |
| `risk` | 模式与风险扫描 | --days（默认 30） |
| `plan` | 本周最值得练的一个 | --days（默认 30） |
| `report` | 完整报告（落盘） | --days（默认 30） |

`--data` 是**顶层参数**，必须放在子命令之前：

```bash
python scripts/comm.py --data ./my_comm trend --days 30   # 对
python scripts/comm.py trend --days 30 --data ./my_comm   # 错
```

## 字段与量表

| 字段 | 取值 | 说明 |
|---|---|---|
| `scene` | 谈判/汇报/请求/反馈/冲突/日常/亲密 | 对话情境 |
| `counterpart` | 上级/客户/同事/家人/朋友/陌生人 | 对象类型 |
| `goal` | 达成/关系/信息/情绪 | **这次对话你想要什么。目标设错是常见的隐性失败** |
| `tone` | 1–10（≥7 为高强度） | 你开口时的情绪强度 |
| `listened` | 1–5 | 你觉得自己听进去多少（主观自评） |
| `reaction` | 合作/中立/防御/对抗 | 对方反应。防御=自我保护，对抗=反击 |
| `outcome` | 1–5（**必填**） | 结果满意度 |
| `aftermath` | -2…+2 | 事后这段关系的变化 |
| `layer` | 事实/情绪/身份（留空由引擎推断） | 卡在哪一层 |

## 关键指标口径

| 指标 | 算法 | 怎么看 |
|---|---|---|
| 平均达成 | outcome 的均值 | 1–5，越高越好 |
| 防御率 | （防御+对抗）÷ 总数 | ≥40% 触发中风险；根因通常是安全感丢失，不是内容不对 |
| 对抗率 | 对抗 ÷ 总数 | ≥20% 触发**高**风险——对方已从自保转为反击 |
| 情绪代价 | 高情绪组平均达成 − 低情绪组平均达成 | **负值=情绪拖累结果**，本引擎最有诊断价值的指标 |
| 关系账户 | aftermath 均值 | 负值 = 你在持续透支这段关系 |
| 身份层占比 | 推断为身份层的条数占比 | ≥40% 触发高风险；说明问题不是技巧，是说话方式在威胁对方的自我形象 |
| 倾听分 | listened 均值 | <2.5 说明说得多听得少 |
| 话术沉淀率 | 填了「下次怎么说」的占比 | <30% 说明复盘了但没留下替代说法 |

**层次推断规则**（优先级 身份 > 情绪 > 事实）：
- `aftermath <= -1 且 outcome <= 2` → 身份层（关系倒退，通常意味着伤到了人）
- `tone >= 7` → 情绪层（你在上头状态开的口）
- 其余 → 事实层

## 退出码

| 码 | 含义 | 谁在用 |
|---|---|---|
| `0` | 正常，或仅有低严重度提醒 | — |
| `1` | 存在中或高严重度沟通模式 | agent 看到 1 就该主动介入 |
| `2` | 用法错误（未知子命令、选项取值非法） | — |
| `4` | 参数或数据不可用（缺 outcome、数值越界、找不到 id、话术库缺失） | — |

## 边界声明

- **复盘工具**，不是心理治疗、不是关系仲裁、不做临床诊断。
- **自评数据有偏差**：`aftermath` 和 `reaction` 这类外部信号，比 `tone`、`listened` 这类内部自评更可信。
- **小于 5 条记录不做模式判定**，只给提示。
- **隐私**：`words` 字段建议只写你自己的原话，不记录对方的私人信息。数据存本地，不联网、不上传。
- **涉及持续的关系暴力、职场霸凌、家庭暴力，请寻求专业帮助。本工具不适用。**
