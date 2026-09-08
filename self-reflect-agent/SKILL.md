---
name: self-reflect-agent
display_name: 每日三省反思
version: 2.0.0
description: AI 日三省引擎。记录反省日志、跨时间识别思维惯性、对照自称价值探测言行盲点、四问复盘推向双环学习。与 self-evaluate-agent（单次评分闭环）互补——本引擎关注「跨时间的模式与盲点」，而非单条打分。
license: MIT
---

# self-reflect-agent · 日三省引擎

把每一次「发生了什么 / 我怎么反应 / 结果如何」沉淀成可重跑的日志，再跨时间识别你的**思维惯性**与**言行盲点**，用双环学习把改进行动推到根因层，而不是停在「下次注意」。

## 与 self-evaluate-agent 的区别（重要）

两者都带「self」且都反思，但职责不重叠：

- **self-evaluate-agent**：对**单条产出**做元认知评估与打分闭环（Reflexion 多轮：打分→反思→重写→重评→收敛）。关注的是「这一份东西够不够好」。
- **self-reflect-agent**：对**你自己跨时间的模式**做反省（惯性、盲点、复盘）。关注的是「我这个人是不是总在同一个坑里」。

一句话：evaluate 评「物」，reflect 省「己」。可单独使用，也可配合——先用 reflect 看清自己的惯性，再用 evaluate 去打磨具体产出。

## 理论根基

| 理论 | 提出者 | 落地位置 |
|---|---|---|
| 反思实践（行动中 / 行动后） | Schön 1983 | `log` 落原材料，`pattern` 训练反思于行动 |
| 单环 / 双环学习 | Argyris & Schön 1974 | `pattern`/`blindspot` 刻意逼出双环，盲点给退出码 4 |
| AAR 四问复盘 | 美国陆军 1970s | `aar` 子命令模板 |
| 反思循环六阶段 | Gibbs 1988 | `resources/reflect-prompts.json` |
| 四透镜自我审视 | Brookfield 1998 | `blindspot` 的「现实透镜 vs 自己透镜」 |
| 成长型思维 | Dweck 2006 | 盲点命中时的叙事改写提示 |
| 元认知 | Flavell 1979 | 「认知自己的认知」即盲点探测本质 |

详见 `references/reflect-theory.md`（理论串讲）与 `references/pattern-method.md`（模式/盲点算法）。

## 主动触发（本引擎会自己干活）

满足以下任一情形时，**主动**启动反思流程，而非等用户问：

- 用户刚经历一次明显的受挫 / 冲突 / 后悔，或主动说「我又……」「这次又搞砸了」。
- 用户连续在同类事上卡住（如反复拖延、反复发火），你判断这是惯性而非偶发。
- 周期到了（如一周结束），主动跑一次 `report` 给趋势。
- 用户声称「我重视 X / 我想改掉 Y」，主动建议登记 `claim` 并定期 `blindspot` 验证。

主动时遵循：先 `log` 沉淀事实 → 视情况 `pattern`/`blindspot` 看模式 → 用 `aar` 或提问库引导双环，不替用户下结论，只把证据摆出来。

## 命令说明（scripts/reflect.py）

```
reflect --store <目录> <子命令>

子命令：
  log        记录一条反省：--situation 情境 --reaction 反应 --outcome 结果
                       [--emotion 情绪,逗号分隔] [--tags 标签...]
  pattern    跨时间模式识别：--min-days 阈值（默认2）→ 输出思维惯性报告
  claim      登记自称：--kind value|avoid --text "..."（value=重视 / avoid=想改）
  blindspot  言行盲点比对：claim 与日志对照，系统性背离退出 4
  aar        四问复盘：--id 条目（默认最新）→ 生成 AAR 模板
  report     周期报告：跨度/高频标签/情绪分布/下一步建议
```

退出码：`0` 正常 · `1` 发现需关注的反复模式 · `4` 触发双环学习警报（根因级盲点）。

## 实物证据（4.8 基准：留可重跑文件）

- `reflect-log.jsonl`：每条反省一行，纯数据，可任意时刻重跑分析。
- `claims.json`：自称价值/待改行为登记。
- `pattern-report.md` / `blindspot-report.md` / `aar-<id>.md` / `reflect-report.md`：各命令生成的产物，均为可复核的 markdown。

## 使用示例

```
# 1. 沉淀今天的受挫
reflect log --situation "项目延期" --reaction "我对同事发火了" --outcome "关系更僵"
# 2. 登记你自称重视的，再查言行 gap
reflect claim --kind value --text "情绪管理"
reflect blindspot        # 若日志里情绪管理实践缺失 → 退出 4，提示双环
# 3. 对最新一条做四问复盘
reflect aar
# 4. 周末看趋势
reflect pattern --min-days 2 && reflect report
```

## 使用边界（诚实）

- 情绪识别靠词表，自由文本不完美；重要反省请用 `--emotion` 显式标注。
- 盲点判定基于字符串命中，用词不同义可能漏报——这是「不臆测」的代价。
- 本引擎给证据与提示，**不替你做人生决定**；双环的前提改写需要你自己的诚实。
- 不收集任何外部数据，所有产物留在你指定的 `--store` 目录。
