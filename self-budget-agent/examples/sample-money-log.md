# 完整样例：小明的第一月记账

这是一份端到端的演示，从零开始走一遍 self-budget-agent 的全部命令。**照抄即可跑通。**

人物设定：小明，税后月收入 12000，房租 3500，手上有现金储备 8000，之前从没记过账。

---

## 第 0 步：建档案

```bash
python scripts/budget.py --data ./demo set \
  --income 12000 --target_save_rate 20 --emergency_fund 8000 \
  --cat_budget 餐饮=1500,交通=500,娱乐=800
```

输出：

```
已更新个人财务设置：{"income": 12000.0, "target_save_rate": 20.0, "emergency_fund": 8000.0, "cat_budget": {"餐饮": 1500.0, "交通": 500.0, "娱乐": 800.0}}
```

`--cat_budget` 是**月度**额度，引擎会按你查询的窗口天数自动折算对比。

## 第 1 步：记一个月

发工资：

```bash
python scripts/budget.py --data ./demo log --date 2026-08-20 --kind in --amount 12000 --category 工资
```

固定支出：

```bash
python scripts/budget.py --data ./demo log --date 2026-08-22 --kind out --amount 3500 --category 房租
python scripts/budget.py --data ./demo log --date 2026-08-23 --kind out --amount 180 --category 水电
python scripts/budget.py --data ./demo log --date 2026-08-23 --kind out --amount 99 --category 订阅 --note 视频会员+云盘
```

日常餐饮（分开记，不要月底一次性汇总）：

```bash
python scripts/budget.py --data ./demo log --date 2026-08-21 --kind out --amount 120 --category 餐饮
python scripts/budget.py --data ./demo log --date 2026-08-24 --kind out --amount 120 --category 餐饮
python scripts/budget.py --data ./demo log --date 2026-08-27 --kind out --amount 120 --category 餐饮
python scripts/budget.py --data ./demo log --date 2026-08-30 --kind out --amount 120 --category 餐饮
```

两笔娱乐——注意这里出现了冲动消费：

```bash
python scripts/budget.py --data ./demo log --date 2026-08-25 --kind out --amount 300 --category 娱乐
python scripts/budget.py --data ./demo log --date 2026-08-28 --kind out --amount 950 --category 娱乐 --note 朋友聚会AA
```

## 第 2 步：看全景

```bash
python scripts/budget.py --data ./demo trend --days 30
```

输出：

```
近 30 天收支概览（8 条记录）：
  收入 12000.00 | 支出 5230.00 | 净结余 6770.00
  储蓄率：56.4%
  折算月支出：5230.00
  必需 76.1% / 想要 23.9% | 固定支出占比 66.9%
  应急金覆盖：1.5 个月
  支出前几名：房租 3500.00(66.9%)，娱乐 1250.00(23.9%)，餐饮 480.00(9.2%)
  日支出波动（变异系数）：1.55（有支出的 7 天）
```

怎么读：储蓄率 56.4% 看着很漂亮，但那是因为只记了 8 笔，**样本严重不足**。折算月支出 5230 是被低估的——真实月份里打车、日用品、人情往来都还没进来。所以第一个月的目标不是"得出正确结论"，而是**养出记录的习惯**。

## 第 3 步：对预算

```bash
python scripts/budget.py --data ./demo budget --days 30
```

输出：

```
预算执行（近 30 天，50/30/20 参照）：
  必需 76.1%（参照 50%） | 想要 23.9%（参照 30%） | 可存 0.0%（参照 20%）
  餐饮：预算 1500 / 实际 480.00（32%）→ 正常
  交通：预算 500 / 实际 0.00（0%）→ 正常
  娱乐：预算 800 / 实际 1250.00（156%）→ 超支
```

娱乐超支 56%——这就是那个"漏钱口"。

注意「可存 0.0%」这一栏：它是 `100 - 必需 - 想要`，只有当必需+想要小于 100% 时才为正。这里因为所有支出都被归进了必需或想要，所以显示为 0。**真正该看的储蓄率是 `trend` 里那个**（按收入算的）。

## 第 4 步：扫风险

```bash
python scripts/budget.py --data ./demo risk --days 30
```

输出：

```
财务风险与弱项扫描（近 30 天）：
  储蓄率 56.4% | 应急金覆盖 1.5 月 | 固定支出占比 66.9%
  [中] 应急金覆盖 1.5 个月（目标 3 个月）
  [中] 固定支出占 66.9%（>50%），支出结构偏刚性
  [中] 分类「娱乐」超预算 56.2%（>20%），是最直接的漏钱口
  [低] 日支出波动大（变异系数 1.55），说明有大额冲动消费
  优先行动：设发薪日自动转出固定金额补齐应急金，别靠每月手动决定存多少
```

退出码 `1`——因为存在中严重度项。这条退出码是给 agent 用的：看到 1 就知道该主动介入了。

## 第 5 步：只改一个

```bash
python scripts/budget.py --data ./demo plan --days 30
```

输出：

```
本周最值得做的一个改变：
  [中] 应急金覆盖 1.5 个月（目标 3 个月）
  → 行动：设发薪日自动转出固定金额补齐应急金，别靠每月手动决定存多少。
  （另有 3 项次要问题，跑 risk 看全部）
```

注意行动与提示是**同一条**——早期版本里两者按不同优先级链选取，出现过"提示应急金不足、建议去降房租"的矛盾输出，v2.0.0 已修。

## 第 6 步：出报告

```bash
python scripts/budget.py --data ./demo report --days 30
```

除屏幕输出外，还会落盘一份 `reports/budget-<日期>.md`。这是**可复核的实物证据**——一个月后再跑一次，两份报告并排看，变化一目了然。

---

## 记错了怎么办

用同一个 `--id` 重记一次即可覆盖，不会重复计数：

```bash
# 原来记成 950，实际是 650
python scripts/budget.py --data ./demo log \
  --date 2026-08-28 --kind out --amount 650 --category 娱乐 --id 2026-08-28#1
```

不指定 `--id` 时，引擎按 `日期#序号` 自动生成（如 `2026-08-28#1`）。想知道某笔的 id，看 `log` 命令的输出。

---

## 数据长什么样

`events.jsonl` 每行一条 JSON：

```json
{"type": "budget", "id": "2026-08-22#1", "date": "2026-08-22", "kind": "out", "amount": 3500.0, "category": "房租", "note": "", "ts": "2026-09-01 16:22:40"}
```

纯文本，可用任何编辑器查看，可自己写脚本分析，可 git 版本管理。`profile.json` 存你的收入、目标、应急金、分类预算。

## 隐私

所有数据写在 `--data` 指定的本地目录，引擎**不联网、不上传**。
