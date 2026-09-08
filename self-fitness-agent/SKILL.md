---
name: self-fitness-agent
display_name: 健身训练管理
version: 2.0.0
type: skill
description: 健身训练管理 AI Agent：帮你记录每次训练、算清训练负荷与恢复、提前预警伤痛风险、给出渐进式下周计划。适合想增肌/减脂/强身却总受伤、练了没效果、坚持不下来的普通人。把"想动起来"变成可追踪、可坚持、不受伤的爬坡。
keywords: [健身, 运动, 增肌, 减脂, 练肌肉, 增肌计划, 减脂计划, 训练计划, 健身打卡, 训练记录, 运动受伤, 伤痛预防, 恢复, 过度训练, 练不动, 坚持运动, 训练负荷, 力量训练, 有氧, 健身新手, 肌肉, workout, fitness, hypertrophy, training load, injury prevention]
triggers:
  - 想增肌/减脂/强身但不知道怎么练、练多少
  - 总受伤、练完疼好几天、担心运动受伤
  - 练了几周没效果、进入平台期
  - 坚持不下来、三天打鱼两天晒网
  - 想知道自己练过量了还是练少了
  - 听人说"要渐进超负荷"但不懂怎么操作
  - 睡眠差、酸痛重，不知道还能不能加量
license: MIT
---

# self-fitness-agent：把"想动起来"变成可追踪、不受伤的爬坡

## 一、这个 Agent 是干什么的

self-fitness-agent 是「自我」系列里专注于**运动训练**的一个能主动干活的 AI Agent。它的服务对象是「用 AI 的人」本人——那个办了卡却怕受伤、跟风练了没效果、flag 立了又倒的你。

它不替你举铁，也不做医疗诊断，而是把"想练好"这件模糊的愿望，拆解成一组**可记录、可计算、可复核**的指标：

- **训练负荷量化**：用工程近似的"训练压力分"记录每次训练的量与强度，累计成周/月趋势；
- **伤痛风险预警**：用急性:慢性负荷比（ACWR）、单调性、单部位过度使用，提前点名"你快练伤了"；
- **恢复评估**：把前夜睡眠、酸痛、RPE 趋势合成恢复分，告诉你"今天该加还是该歇"；
- **渐进式计划**：每次只给你"本周最值得做的一个改变"，避免建议过载。

它背后站着一整套运动科学（详见 `references/` 与 `resources/`）：训练负荷与损伤模型（Gabbett）、ACSM 运动处方、渐进超负荷、肌肥大机制、训练频率与分化、恢复与睡眠、DOMS、心率区间、周期化、热身防伤、久坐与 NEAT、过度训练综合征、蛋白质与合成。不是"健身博主的经验"，而是**带年份、期刊、书名出处**的循证底座。

## 二、主动触发（重要）

这个 Agent **不是等你去翻文档才动的说明书**。当以下情形出现时，它会主动介入：

- 你提到"想增肌/减脂/强身但不知道怎么练"——主动建议从 `set` 设目标 + `log` 记录起步，并给最小上手步骤；
- 你已经记了 2–3 周——主动跑 `trend` / `risk` / `report`，把负荷、频率、弱项摆出来；
- 报告出现弱项（退出码 1）或风险高危——主动用 `plan` 给出本周唯一主攻项，并解释为什么选它；
- 你说"我周末猛练一天补回来"——主动用 ACWR 点破"一次暴练比规律练更伤"；
- 你说"练完疼好几天、怕受伤"——主动用 DOMS 与伤痛风险理论区分正常酸痛与过度信号；
- 你说"睡眠差/很酸还能加量吗"——主动用 `recover` 算恢复分，把"练"和"恢复"绑定决策；
- 你提到长期疲劳、表现下滑——主动用过度训练理论提醒前哨定位，严重持续走正规运动医学。

换句话说：它在该出手时出手，在该收手时收手（不替代医生/康复师），在该教育时教育（用理论而非鸡汤）。

## 三、理论地图（13 篇均带出处）

| # | 主题 | 代表出处 |
|---|---|---|
| 1 | 训练负荷与伤痛（ACWR） | Gabbett 2016, *Br J Sports Med* 50:273-280 |
| 2 | 运动处方 FITT 框架 | Garber 2011, *Med Sci Sports Exerc* 43:1334-1359 |
| 3 | 渐进超负荷 | Kraemer & Ratamess 2004, *Physiol Rev* 84:419-428 |
| 4 | 肌肥大三机制 | Schoenfeld 2010, *J Strength Cond Res* 24:2857-2872 |
| 5 | 训练频率与分化 | Schoenfeld 2016, *Sports Med* 46:1689-1697 |
| 6 | 恢复与睡眠 | Watson 2017, *Sleep Med Clin* 12:563-573 |
| 7 | DOMS 与主动恢复 | Cheung 2003, *J Athl Train* 38:364-372 |
| 8 | 心率区间 Karvonen | Tanaka 2001, *J Am Coll Cardiol* 37:153-156 |
| 9 | 周期化 | Kiely 2012, *J Strength Cond Res* 26:641-654 |
| 10 | 热身防伤 | Fradkin 2006, *J Sci Med Sport* 9:32-35 |
| 11 | 久坐与 NEAT | Levine 2002, *Best Pract Res Endocrinol Metab* 16:679-702 |
| 12 | 过度训练综合征 | Meeusen 2013, *Eur J Sport Sci* 13:1-24 |
| 13 | 蛋白质与合成 | Morton 2018, *Br J Sports Med* 52:376-384 |

## 四、快速上手

```bash
# 0) 设个人目标（周频次），可选
python scripts/fitness.py --data ./my_fit set --target_freq 4

# 1) 记一次训练（力量/有氧/柔韧/专项）
python scripts/fitness.py --data ./my_fit log \
  --date 2026-09-01 --type_sub strength --duration 50 --rpe 7 \
  --sets 4 --reps 8 --weight 60 --parts 胸,三头 --sleep_prev 7 --sore 3

# 2) 看趋势（近 28 天负荷/频次/ACWR）
python scripts/fitness.py --data ./my_fit trend --days 28

# 3) 伤痛风险扫描（高风险退出码 1）
python scripts/fitness.py --data ./my_fit risk --days 28

# 4) 恢复评估
python scripts/fitness.py --data ./my_fit recover --days 14

# 5) 本周最该做的一个改变
python scripts/fitness.py --data ./my_fit plan --days 28

# 6) 完整报告（弱项退出码 1）
python scripts/fitness.py --data ./my_fit report --days 28
```

数据落在 `--data`：`events.jsonl` + `profile.json` + `reports/fitness-<日期>.md`，纯本地、可长期追踪、重跑一致。

## 五、子命令速查

| 命令 | 作用 | 关键参数 |
|---|---|---|
| `set` | 设置个人目标（target_freq） | --target_freq |
| `log` | 记录一次训练 | --date --type_sub --duration --rpe --sets --reps --weight --parts --sleep_prev --sore |
| `trend` | 负荷/频次/强度趋势 | --days（默认 28） |
| `recover` | 恢复评分 | --days（默认 14） |
| `risk` | 伤痛风险与弱项扫描（高严重度退出码 1） | --days（默认 28） |
| `plan` | 下周最值得做的一个改变 | --days（默认 28） |
| `report` | 完整报告（弱项退出码 1） | --days（默认 28） |

## 六、边界声明

- 这是**前哨工具**：帮你量化与预警，不做医疗诊断；
- 伤痛持续、关节锐痛、长期疲劳——请走正规运动医学/康复；
- 训练压力分为工程近似，绝对值不对外承诺，看重**趋势与比值**（ACWR、单调性）。

详见 `README.md`（导航）、`FAQ.md`（14 问）、`references/`（理论长文）、`examples/`（完整样例）。
