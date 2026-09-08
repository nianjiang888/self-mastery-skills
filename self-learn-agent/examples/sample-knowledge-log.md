# 样例：把《认知心理学》吃透成私有库

> 本文件演示 self-learn-agent 的一条真实流转：从消化 → 复习 → 自测 → 质询 → 报告。字段与节奏可直接参照。

## 第一步：消化（ingest）

```bash
python scripts/learn.py ingest --source "《认知心理学》" --title "第3章 工作记忆" \
  --concept "工作记忆容量有限" --note "一次只能保持约4±1个组块，超限需组块化压缩" \
  --tags "记忆,认知"
```

产出 `knowledge.jsonl` 一行（节选）：

```json
{
  "id": "6190bfc75470",
  "source": "《认知心理学》",
  "concept": "工作记忆容量有限",
  "bucket": 1,
  "interval_days": 1,
  "ease": 2.5,
  "due_date": "2026-09-01",
  "mastery": 0.05,
  "recall_history": [],
  "elaborations": []
}
```

同时生成 `notes/6190bfc75470.md` 消化笔记。

## 第二步：间隔复习（review）

当天列出待复习，记录一次通过复习：

```bash
python scripts/learn.py review --id "#1" --grade 5
```

`due_date` 推进到 `2026-09-04`，`bucket` 升到 2，`mastery` 上调（ passages 由 0.05 → 约 0.27），`events.jsonl` 追加一条 `type: review` 记录。

## 第三步：主动回忆（quiz）

```bash
python scripts/learn.py quiz --id "#1" --recall 0.8
```

`recall_history` 追加 `{date, recall:0.8}`，`mastery` 按 0.6*旧 + 0.4*0.8 混合更新。这正是 Karpicke & Roediger (2008) 测试效应的落地。

## 第四步：精细质询（elaborate）

```bash
python scripts/learn.py elaborate --id "#1" \
  --why "因为容量有限，所以必须压缩信息成组块" \
  --how "用思维导图把零散点合并" \
  --relate "与认知负荷理论的'减外在负荷'同源"
```

三问写回笔记 `notes/6190bfc75470.md`，`mastery` 小幅上调。对应 Pressley et al. (1987) 精细质询。

## 第五步：交错练习（interleave）

```bash
python scripts/learn.py interleave --tags 认知 --count 4
```

按日期种子混合"工作记忆/图式/认知负荷"等易混概念，输出一份混排序列，训练辨别（Rohrer 2012）。

## 第六步：掌握度报告（report）

```bash
python scripts/learn.py report
```

产出 `reports/mastery-2026-09-01.md`，含：平均掌握度、薄弱/高风险清单、全量知识点表格。若发现 `mastery<0.4` 的薄弱点或遗忘≥2 次的高风险点，引擎返回退出码 `1`，提醒优先处理——这是 Koriat (1993) 元认知监控的工程化。

## 一周后回看

重复 `review` 与 `quiz`，你会看到"工作记忆容量有限"的 `bucket` 逐步升到 5–7、`interval_days` 拉长到 30–60 天、`mastery` 稳定在 0.8 以上——它真正"长"进了你的私有库，而不是读完就忘。
