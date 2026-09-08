---
name: self-learn-agent
display_name: 知识消化与抗遗忘
version: 2.0.0
type: agent
description: 知识消化与抗遗忘间隔重复的主动学习 Agent。把书/课吃透成你的私有库——自动排程间隔复习、主动回忆测试、精细质询、交错练习，并产出可复核的掌握度报告。
license: MIT
---

# self-learn-agent（知识消化 + 抗遗忘间隔重复）

把读过的书、上过的课、踩过的坑，真正"长"进自己的知识库，而不是读完就忘。

## 主动触发

本 Agent 不是一个被动清单，而是一个会主动干活的学习引擎。以下情形应主动调用：

- 读完一章书/一节课程，需要把它拆成可回忆的原子知识点并落库时。
- 临近复习时点，需要按遗忘曲线自动排程、列出今日待复习清单时。
- 想验证"我是不是真会了"，需要做主动回忆测试（测试效应）时。
- 想加深理解，需要对某概念自问"为什么/如何/与什么相关"（精细质询）时。
- 想提升迁移，需要把易混概念混排成交错练习序列时。
- 周期性（每周/每月）需要掌握度报表、识别高风险遗忘点时。

触发后默认动作：先用 `ingest` 消化新点，再按 `review`/`quiz`/`elaborate`/`interleave` 循环固化，最后用 `report` 反查。所有动作都在数据目录留下 `knowledge.jsonl` 与 `events.jsonl` 实物证据，可逐条复核。

## 它解决什么

大多数人学习的真实瓶颈不是"输入少"，而是"留不住、用不出"：

1. 读完即忘——缺乏按遗忘曲线的间隔复习（Ebbinghaus 1885；Cepeda 2006）。
2. 看懂错觉——重读带来流畅感误判为掌握（Koriat 1993；Dunlosky & Bjork 2008）。
3. 浅层加工——停在记忆层，未走到理解/应用/创造（Bloom 1956/2001）。
4. 集中无效——同类狂刷不如交错混练（Rohrer 2012）。
5. 意义缺失——被动接收而非生成（Fiorella & Mayer 2015）。

本 Agent 用六个子命令把上述每条都变成可执行动作。

## 引擎与用法

引擎位于 `scripts/learn.py`（纯标准库，无需第三方依赖）。所有子命令通过 `--data` 指定数据目录（默认 `self_learn_data`）。

```bash
# 1. 消化一条知识（书/课/论文/经验）
python scripts/learn.py ingest --source "《认知心理学》" --title "第3章" \
  --concept "工作记忆容量有限" --note "一次约保持4±1个组块" --tags "记忆,认知"

# 2. 列出今日待复习（有高风险点则返回退出码 1）
python scripts/learn.py review

# 3. 记录一次复习成绩（0-5，≥3 通过，推进 Leitner 盒与间隔）
python scripts/learn.py review --id "#1" --grade 5

# 4. 主动回忆抽题 / 记录回忆成绩
python scripts/learn.py quiz --count 5
python scripts/learn.py quiz --id "#1" --recall 0.8

# 5. 精细质询：为什么 / 如何 / 与什么相关
python scripts/learn.py elaborate --id "#1" --why "..." --how "..." --relate "..."

# 6. 交错练习序列（按日期确定性混排）
python scripts/learn.py interleave --tags 方法 --count 6

# 7. 掌握度报告（默认落到 reports/，可 --out 指定）
python scripts/learn.py report
```

退出码约定：`0` 正常；`1` 需关注（存在高风险/薄弱知识点，优先处理）；`4` 系统性警报（数据目录不可读写等）。

## 理论地图（12+ 条，均带出处）

| 理论 | 核心结论 | 出处 | 对应子命令 |
|------|----------|------|-----------|
| Bloom 分类学 | 学习深度分六层，须从记忆走到创造 | Bloom (1956)；Anderson & Krathwohl (2001) | ingest/elaborate |
| 艾宾浩斯遗忘曲线 | 不复习则先快后慢流失 | Ebbinghaus (1885)；Murre & Dros (2015) | review |
| 间隔效应 | 分散练习优于集中练习 | Cepeda et al. (2006)；Pashler et al. (2007) | review |
| 测试效应 | 主动提取比重读更牢 | Karpicke & Roediger (2008)；Roediger & Karpicke (2006) | quiz |
| 生成式学习 | 用自己的话/图/教生成意义 | Fiorella & Mayer (2015)；Mayer (2009) | ingest/elaborate |
| 精细质询 | 自问"为什么"织入语义网 | Pressley et al. (1987)；Chi et al. (1994) | elaborate |
| 交错练习 | 混排易混主题提升辨别 | Rohrer (2012)；Rohrer & Taylor (2007) | interleave |
| 元认知监控 | 流畅感≠掌握，需测试校准 | Koriat (1993)；Hart (1965)；Dunlosky & Bjork (2008) | report/quiz |
| 认知负荷理论 | 砍外在、控内在、投关联 | Sweller (1988)；Sweller et al. (2011) | ingest/interleave |
| 双重编码 | 文字+图像双通道冗余 | Paivio (1971, 1986) | ingest/elaborate |
| 可取难度 | 当下费劲的提取更牢 | Bjork & Bjork (1992, 2011) | quiz/review/interleave |
| Leitner/SM-2 算法 | 间隔排程的工程实现 | Leitner (1972)；Wozniak (1987) | review |

每一条理论的详细论证见 `references/` 下对应长文（均含可核验年份/期刊/书名）。

## 数据产物（实物证据）

- `knowledge.jsonl`：每个原子知识点的状态（盒、间隔、掌握度、回忆史、质询记录）。
- `events.jsonl`：追加式事件日志，所有动作可溯源。
- `notes/<id>.md`：每条知识的消化笔记，随质询持续更新。
- `reports/mastery-<date>.md`：掌握度报表，含薄弱/高风险清单与全量表格。

## 资源库

- `resources/learning-strategies.json`：12 条学习策略与理论绑定。
- `resources/spacing-algorithms.json`：Leitner/SM-2/Pimsleur 与掌握度、风险规则。
- `resources/knowledge-sources.json`：书/课/论文/经验四类来源模板与标签体系。

## 文件导航

- 上手与示例：`README.md`
- 常见问题：`FAQ.md`
- 自评与溯源：`SELF_EVAL.md`、`CHANGELOG.md`
- 样例库：`examples/sample-knowledge-log.md`
- 理论深读：`references/` 下 11 篇
