# README：self-learn-agent 使用导航

> 定位：知识消化 + 抗遗忘间隔重复。把书/课吃透成你的私有库。

## 一、它是什么

一个能主动干活的 Python Agent（非清单）。核心引擎 `scripts/learn.py` 用六个子命令覆盖"消化—复习—自测—质询—交错—报告"的完整学习闭环，所有动作落 `knowledge.jsonl` / `events.jsonl` 并产出 markdown 笔记与报表，可逐条复核、可重跑。

## 二、30 秒上手

```bash
# 进入技能目录
cd E:/Skills/self/self-learn-agent

# 消化第一条知识
python scripts/learn.py ingest --source "《认知心理学》" --title "第3章" \
  --concept "工作记忆容量有限" --note "一次约保持4±1个组块" --tags "记忆,认知"

# 再消化一条（不同主题，便于后续交错）
python scripts/learn.py ingest --source "《认知心理学》" --title "第4章" \
  --concept "图式自动化降低负荷" --note "专家靠图式减少工作记忆占用" --tags "认知,负荷"

# 列出今日待复习
python scripts/learn.py review

# 记录一次复习（grade 0-5，≥3 通过）
python scripts/learn.py review --id "#1" --grade 5

# 主动回忆自测
python scripts/learn.py quiz --id "#1" --recall 0.8

# 精细质询：为什么/如何/相关
python scripts/learn.py elaborate --id "#1" --why "容量有限所以需组块化" \
  --how "用思维导图压缩信息" --relate "与认知负荷理论相关"

# 交错练习序列
python scripts/learn.py interleave --tags 认知 --count 4

# 掌握度报告
python scripts/learn.py report
```

## 三、子命令速查

| 子命令 | 作用 | 关键参数 | 退出码含义 |
|--------|------|----------|-----------|
| `ingest` | 消化知识，落库+笔记 | `--source --concept --note --tags` | 0 成功 |
| `review` | 间隔复习调度/记录 | `--id --grade --date` | 0 正常 / 1 有高风险 |
| `quiz` | 主动回忆测试 | `--id --recall --count` | 0 正常 |
| `elaborate` | 精细质询 | `--id --why --how --relate` | 0 成功 |
| `interleave` | 交错练习序列 | `--tags --count --date` | 0 正常 |
| `report` | 掌握度报告 | `--out --date` | 0 正常 / 1 有薄弱 |

退出码：`0` 正常 / `1` 需关注（高风险或薄弱点）/ `4` 系统性警报。

## 四、数据目录结构

```
self_learn_data/
├── knowledge.jsonl      # 知识点状态库（盒/间隔/掌握度/回忆史/质询）
├── events.jsonl         # 追加式事件日志（所有动作溯源）
├── notes/<id>.md        # 每条知识的消化笔记（随质询更新）
└── reports/mastery-<日期>.md  # 掌握度报表
```

## 五、推荐周节奏

1. **每日**：读新材料 → `ingest` 消化；按 `review` 提醒复习当日项。
2. **每读一节**：`quiz` 合书自测一次；对难点 `elaborate` 三问。
3. **每周**：`interleave` 混排易混概念；`report` 对账主观 vs 客观掌握度。
4. **每月**：通读 `report`，集中补高风险点，归档笔记。

## 六、文件地图

- 引擎：`scripts/learn.py`
- 资源：`resources/learning-strategies.json`、`spacing-algorithms.json`、`knowledge-sources.json`
- 理论深读：`references/`（11 篇，均带出处）
- 问答：`FAQ.md`
- 样例库：`examples/sample-knowledge-log.md`
- 自评/变更：`SELF_EVAL.md`、`CHANGELOG.md`

## 七、样例库

`examples/sample-knowledge-log.md` 给出一个真实的"消化→复习→自测→质询→报告"流转示例，可直接参照其字段与节奏使用。
