# self-master-agent 导航（README）

> 一句话：把「想精通一门技能」变成可复核的爬坡——五层登顶阶梯 + 真实实战检验 + 登顶曲线 + 弱项预警。

## 30 秒上手

```bash
# 登记一门要精通的技能
python scripts/master.py --data ./my_master add --name "Python 性能优化" \
    --goal "能把慢代码提速10倍" --target 5 --level 1

# 定义五级阶梯判据（每层写可核验标准）
python scripts/master.py --data ./my_master ladder --id "#1" \
    --define "L1:能读懂火焰图;L2:能定位一类瓶颈;L3:能稳定提速2倍;L4:能设计缓存策略;L5:能定义团队性能规范"

# 做真实实战（必须带 evidence）
python scripts/master.py --data ./my_master drill --id "#1" \
    --task "优化导出脚本" --difficulty 2 --result success --confidence 4 --evidence "export_v2.py"

# 自评校准 + 看报告/下一步
python scripts/master.py --data ./my_master measure --id "#1" --score 2
python scripts/master.py --data ./my_master report
python scripts/master.py --data ./my_master plan --id "#1"
```

## 文件导航

| 路径 | 内容 |
|---|---|
| `SKILL.md` | 技能定义、主动触发段、理论地图、快速上手 |
| `scripts/master.py` | **真引擎**（6 子命令，纯标准库，退出码 0/1/4） |
| `resources/mastery-levels.json` | 五级阶梯通用判据库（含 version 2.0.0） |
| `resources/deliberate-practice.json` | 刻意练习八原则库 |
| `resources/skill-domains.json` | 常见技能领域阶梯示例 |
| `references/` | 11 篇理论长文（带可核验出处） |
| `FAQ.md` | 12 个常见疑问 |
| `SELF_EVAL.md` | 对「真引擎」的 TRACE 五维自评 |
| `CHANGELOG.md` | 版本与变更记录 |
| `examples/sample-mastery.md` | 一份完整的登顶记录样例 |

## 子命令速查

| 命令 | 必填参数 | 说明 |
|---|---|---|
| `add` | `--name [--goal] [--target] [--level]` | 登记技能 |
| `ladder` | `--id [--define "L1:..;L2:.."]` | 设定/查看阶梯 |
| `drill` | `--id --task --difficulty --result [--confidence] [--evidence]` | 记录实战 |
| `measure` | `--id --score [--note]` | 自评层级 |
| `report` | （无） | 报告+曲线+弱项（退出码 1=有弱项） |
| `plan` | `--id` | 下一步缺口 |

## 退出码

- `0` 正常
- `1` 需关注（存在未达标弱项，见 report 弱项预警）
- `4` 系统性警报（参数非法、技能不存在、数据损坏）

## 设计原则（为什么不是又一个「学习清单」）

1. **棘轮不可逆**：每次真实实战与晋升都被写入 `events.jsonl`，进度只进不退。
2. **真实优先**：晋升只看「真实实战成功 + 自评达标」，模拟不计数。
3. **校准幻觉**：用 `measure`+`drill` 双轨，专治「以为会了」的能力错觉。
4. **可见产出**：`report` 的登顶曲线让长期复利一眼可见。

理论根基详见 `references/`（Dreyfus / Ericsson / Bloom / ACT-R / Fitts / Kahneman-Klein / Csikszentmihalyi / Salomon-Perkins / Dweck / Bloom掌握学习 / Koriat）。
