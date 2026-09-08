# 样例：阿楠的两周睡眠记录与节律学习

> 本样例演示如何用 self-sleep-agent 记录两周、学出时型、并拿到本周计划。数据为示意。

## 一、逐晚记录（节选）

```bash
python scripts/sleep.py --data ./demo log --date 2026-08-18 --bedtime 01:10 --onset 01:40 --wake 09:10 --wakings 2 --quality 3 --caffeine 1 --screen 90 --mood 3 --daytype free
python scripts/sleep.py --data ./demo log --date 2026-08-19 --bedtime 23:40 --onset 00:10 --wake 07:10 --wakings 1 --quality 4 --caffeine 4 --screen 30 --mood 4 --daytype work
python scripts/sleep.py --data ./demo log --date 2026-08-20 --bedtime 00:30 --onset 01:00 --wake 08:00 --wakings 1 --quality 4 --caffeine 3 --screen 45 --mood 4 --daytype work
# …… 累计 14 晚，其中 work 10 晚 / free 4 晚
```

## 二、趋势（trend --days 14）

```
近 14 晚睡眠趋势（目标 7h 30m）：
  平均总睡眠：6h 42m
  平均睡眠效率：86.3%（最低 79.0%）
  平均入睡潜伏期：0h 28m
  平均主观质量：3.6/5
  日均睡眠债：0h 48m
  规律性评分：58.4/100（就寝波动±95min，起床波动±70min）
```

## 三、节律（rhythm）

```
从 14 晚记录学出的生理节律：
  平均睡眠中点：04:52
  推断时型：夜猫型（晚型）
  社会时差：2.31 小时（工作 vs 自由日中点差）
  ⚠ 社会时差偏大，周末补觉反而打乱生物钟
```

## 四、报告（report，退出码 1）

报告落盘 `reports/sleep-2026-09-01.md`，含三段：近期趋势、生理节律、弱项预警。弱项包括：
- 睡眠规律性 58.4 低于 70（作息漂移）；
- 日均睡眠债 48 分钟，超过 30 分钟阈值；
- 有 5 晚咖啡因距寝不足 6 小时；
- 有 6 晚睡前屏幕超过 60 分钟。

## 五、本周计划（plan）

```
本周冲刺计划：
  主攻：睡眠规律性 58.4 低于 70（作息漂移，生物钟难稳）
  做法：固定起床时间（即使周末），就寝时间随睡眠债小幅前移，±30min 内。
```

## 六、解读

阿楠是典型夜猫，且社会时差 2.3 小时——她之前总自责"懒、自律差"，但 `rhythm` 把问题翻译成了生理事实：不是意志力，是时型与社会要求的错位。plan 没有让她"立刻早睡"，而是先钉起床时间、压缩错位，再逐步前移就寝。三周后复测，规律性升到 76、社会时差缩到 1.1 小时，这就是"用数据替代自责"的实操价值。
