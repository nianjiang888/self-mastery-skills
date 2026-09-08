# 示例：连续两周训练记录 + 输出

下面是一份"增肌新手、每周 3–4 次、偶尔加量过猛"的两周记录，展示引擎如何量化与预警。

## 1）设目标

```bash
python scripts/fitness.py --data ./demo set --target_freq 4
```

## 2）记录（节选，实际 14 条）

```bash
python scripts/fitness.py --data ./demo log --date 2026-08-18 --type_sub strength --duration 50 --rpe 7 --sets 4 --reps 8 --weight 60 --parts 胸,三头 --sleep_prev 7 --sore 3
python scripts/fitness.py --data ./demo log --date 2026-08-20 --type_sub strength --duration 55 --rpe 8 --sets 4 --reps 6 --weight 65 --parts 背,二头 --sleep_prev 6 --sore 4
python scripts/fitness.py --data ./demo log --date 2026-08-22 --type_sub cardio --duration 40 --rpe 6 --zone 3 --parts 有氧
python scripts/fitness.py --data ./demo log --date 2026-08-25 --type_sub strength --duration 50 --rpe 9 --sets 5 --reps 5 --weight 70 --parts 腿 --sleep_prev 5 --sore 6
# ... 其余若干次，含一次 mobilty 恢复日
```

## 3）趋势（节选）

```
近 28 天训练趋势：
  记录次数：14（约每周 3.5 次）
  训练压力分合计：920.4
  平均时长：50 分钟 | 平均 RPE：7.6
  总吨位：约 18000 kg·次
  急性:慢性负荷比 ACWR：1.42（偏高（谨慎加量））
  单调性：1.85 | 紧张度：…
  最常练部位：胸（占 18%）
  前夜睡眠评分均值：6.2 / 10
  酸痛均值：4.1 / 10
```

## 4）风险扫描（节选）

```
伤痛风险与弱项扫描（近 28 天）：
  ACWR 1.42 → 偏高（谨慎加量）
  [中] 负荷不足/突增：…（依数据）
  [中] 训练频次偏低：近期每周约 3.5 次（目标 4 次）
  [中] 恢复不足：前夜睡眠评分均值 6.2（<7）
```

> 若某周末暴练导致 ACWR>1.5，则出现 `[高]` 严重度，且 `risk` 退出码为 1。

## 5）恢复评估（节选）

```
恢复评分（估算，0-100）：72
  主要拖累：前夜睡眠差，恢复受限
```

## 6）计划（节选）

```
下周最值得做的一个改变：
  [中] 恢复不足：前夜睡眠评分均值 6.2（<7），训练后恢复受限，建议优先睡好再加压
  → 行动：优先安排 1 个恢复/柔韧日，并确认前夜睡眠与酸痛在改善。
```

## 7）报告落盘

`reports/fitness-<当天日期>.md` 会生成一份含趋势 + 弱项预警的 Markdown，可长期存档对比。

---

**如何复现**：把上面的 `log` 命令按你真实的训练日期替换 `--date` 跑一遍即可，日期用相对今天连续的 14 天最能看出 ACWR 效果。
