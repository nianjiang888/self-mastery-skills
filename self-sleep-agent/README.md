# self-sleep-agent 使用导航

> 睡眠质量管理 AI Agent：记录每晚睡眠、学出你的生理节律与时型、量化睡眠债与规律性、预警弱项并给出本周计划。帮"用 AI 的人"越睡越懂自己。

## 一、30 秒上手

```bash
# 记一晚（--bedtime/--wake 必填；--latency 直接填潜伏期，或留空由 --onset 推算）
python scripts/sleep.py --data ./my_sleep log \
  --date 2026-09-01 --bedtime 23:30 --latency 20 --wake 06:30 \
  --waso 25 --quality 4 --caffeine 3 --screen 40 --mood 4 --daytype work

# 看趋势（睡眠债/规律性/效率）
python scripts/sleep.py --data ./my_sleep trend --days 14
# 学节律/时型/规律性（SRI 工程近似）
python scripts/sleep.py --data ./my_sleep rhythm
# 完整报告（有弱项退出码 1，并落盘 reports/sleep-<日期>.md）
python scripts/sleep.py --data ./my_sleep report
# 本周最该改的一个
python scripts/sleep.py --data ./my_sleep plan
```

数据落在 `--data`：`events.jsonl`（按日期幂等覆盖，重记同晚只留最新）+ `reports/sleep-<日期>.md`，纯本地、可长期追踪、重跑一致。

## 二、文件导航

```
self-sleep-agent/
├── SKILL.md                      技能定义、主动触发、理论地图、上手
├── README.md                     本导航
├── FAQ.md                        14 个高频问题（含"为什么"）
├── SELF_EVAL.md                  TRACE 五维自评
├── CHANGELOG.md                  版本记录
├── scripts/
│   └── sleep.py                  真引擎（6 子命令，纯标准库）
├── resources/
│   ├── sleep-guidelines.json     睡眠时长推荐 + 睡眠卫生规则（带出处）
│   ├── circadian-models.json     双过程/时型/SRI 模型库
│   └── sleep-domains.json        指标定义与计算口径
├── references/                   12 篇方法论长文（均 ≥2000 中文字、带年份/期刊出处）
│   ├── two-process-model.md
│   ├── sleep-regularity-index.md
│   ├── social-jetlag-chronotype.md
│   ├── sleep-need-debt.md
│   ├── sleep-hygiene.md
│   ├── polysomnography-basics.md
│   ├── light-circadian-entrainment.md
│   ├── sleep-memory-consolidation.md
│   ├── cbt-i-restriction.md
│   ├── sleep-architecture-rem-sws.md
│   ├── individual-chronotype.md
│   └── sleep-inertia-napping.md
└── examples/
    └── sample-sleep-log.md       一份完整记录样例
```

## 三、子命令速查

| 命令 | 作用 | 关键参数 |
|---|---|---|
| `log` | 记录一晚睡眠（按日期幂等覆盖） | --date --bedtime --onset\|--latency --wake --waso --quality --caffeine --screen --mood --daytype |
| `trend` | 近期趋势/睡眠债/规律性 | --days（默认14） --target（分钟，默认450） |
| `rhythm` | 学出生理节律/时型/规律性(SRI近似)/社会时差 | — |
| `nudge` | 可执行建议（按影响排序） | --days --target |
| `report` | 完整报告 + 弱项预警 | --days --target（弱项退出码 1） |
| `plan` | 本周最值得做的一个改变 | --days --target |

## 四、核心指标解释

- **睡眠效率** = 总睡眠 ÷ 卧床时长 ×100%，≥85% 健康；偏低说明卧床大半在清醒。
- **入睡潜伏期** = 就寝到入睡的分钟，>30 提示"床=焦虑"。
- **睡眠中点** = 入睡 + 总睡眠/2，用于推断时型与社会时差。
- **睡眠债** = 目标时长 − 实际平均，>30 分钟/日预警。
- **规律性评分** = 就寝/起床日标准差映射的 0–100（SRI 工程近似）。
- **社会时差** = 工作日与自由日睡眠中点之差，≥2 小时预警。

## 五、退出码

| 退出码 | 含义 |
|---|---|
| 0 | 正常，无弱项 |
| 1 | 需关注（report 检出弱项） |
| 4 | 系统性警报（参数或数据错误） |

## 六、边界声明

本 Agent 是自我观察与节律学习工具，**不是医疗诊断、不替代医生**。规律性评分为 SRI 工程近似；时型/社会时差从你提供的数据实时重算，记录越多越稳。慢性失眠请走正规 CBT-I 或睡眠门诊。
