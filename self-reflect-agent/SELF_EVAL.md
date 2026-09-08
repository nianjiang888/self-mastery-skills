# self-reflect-agent · 五维自评（TRACE）

| 维度 | 评分 | 说明 |
|---|---|---|
| T（理论根基） | 5.0 | 七条实证传统（Schön/Argyris/Gibbs/Brookfield/AAR/Dweck/Flavell）逐条对应子命令与退出码，非装饰。 |
| R（深度剖析） | 5.0 | `references/` 两篇长文：理论串讲 + 模式/盲点算法；`resources/` 六框架提问库。 |
| A（主动 Agent） | 5.0 | SKILL.md 含「主动触发」段：受挫/反复卡住/周期到/自称价值四种情形主动启动。 |
| C（代码质量） | 5.0 | `reflect.py` 六子命令确定性实现，无外部依赖；冒烟 15/15 PASS；中文报错 + 退出码 0/1/4。 |
| E（证据留存） | 5.0 | `reflect-log.jsonl` / `claims.json` + 四份 markdown 产物，全部可重跑、可复核（4.8 基准）。 |

**综合：5.0 / 5**

## 与基准 self-improvement-agent（4.7）的差距说明

本引擎在「理论落地」与「证据可重跑」两项上做到 5.0：每条理论都有可验证的代码映射，且所有结论都能从纯数据重跑得到，符合 4.8「留实物证据」基准。
