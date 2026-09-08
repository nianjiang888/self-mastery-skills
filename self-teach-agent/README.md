# self-teach-agent 使用说明

自我教学与知识内化引擎。把任意外部材料（文章/论文/书/对话/代码库）走完
**摄入 → 排课(由易到难) → 自测 → 间隔复现 → 晋升** 闭环，不达标不晋升。

## 文件导航（12 个文件，结构随内容走）

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 引擎定义与理论根基 |
| `scripts/teach.py` | 主编排：摄入→结构化→自测覆盖→晋升/回滚/汇报 |
| `scripts/curriculum.py` | 先修图拓扑排序 + 由易到难路径（可计算硬核 1） |
| `scripts/retention.py` | SM-2 间隔重复 + 遗忘曲线读数（可计算硬核 2） |
| `resources/sources.json` | 知识源类型与摄入适配器 |
| `resources/retention_schedule.json` | SM-2 间隔参数 |
| `references/teach-theory.md` | Self-Instruct / STaR / Curriculum / 遗忘曲线 深解 |
| `references/ingest-method.md` | 把原始材料变成自己的知识 |
| `references/spaced-retention.md` | 间隔重复与测试效应实践 |
| `FAQ.md` | 常见疑问 |
| `README.md` | 本文件 |
| `SELF_EVAL.md` | 本包 TRACE 五维自评到 5.0 |

## 快速上手

```bash
cd self-teach-agent

# 1) 摄入一篇材料，拆成知识单元脚手架
python3 scripts/teach.py --ingest --topic "注意力机制" --material article.md

# 2) 为每个单元补全 definition/why/example（用你的笔记工具）
#    完成后检查覆盖
python3 scripts/teach.py --quiz

# 3) 若还做了回忆评分，传 --grades grades.json 一起卡
python3 scripts/teach.py --promote --grades grades.json

# 4) 排一份由易到难的学习计划
python3 scripts/curriculum.py --demo
python3 scripts/curriculum.py --syllabus my_plan.json

# 5) 把学会的排进间隔复现
python3 scripts/retention.py --demo
python3 scripts/retention.py --schedule --grade 5 --out state.json
python3 scripts/retention.py --retention --interval 16 --elapsed 7
```

## 退出码

| 码 | 含义 |
|---|---|
| 0 | 成功 / 门禁达标 |
| 1 | 用法错误 / 晋升被拦下（覆盖不足或回忆评分不够） |

`--promote` 被拦下时返回 1，可被 CI / 工作流物理拦下，避免虚假掌握进入"本领库"。

## 同系列

evaluate(质量) · debug(修复) · verify(验证) · optimize(优化) · **teach(教学)**。
