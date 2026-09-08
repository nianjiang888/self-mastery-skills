# self-soothe-agent 使用导航

情绪调节与 CBT 工具包。把「一来情绪就乱、越想越糟、用错方式自我安慰反而更累」变成可记录、可计算、可复核的日课。

## 30 秒开始

```bash
python scripts/soothe.py --data ./my_soothe log \
  --emotion 焦虑 --trigger "项目又延期" --intensity 4 \
  --distortion fortune-telling --action "刷手机" --relief 1 --impact 睡眠
python scripts/soothe.py --data ./my_soothe risk
python scripts/soothe.py --data ./my_soothe plan
```

## 节奏建议

| 什么时候 | 跑什么 | 目的 |
|----------|--------|------|
| 情绪刚过 | `log` 记一笔 | 把模糊难受落成数据 |
| 睡前 / 周末 | `trend` 或 `risk` | 看本周模式 |
| 想练但不知道练啥 | `plan` | 拿唯一行动 |
| 怀疑掉进某陷阱 | `script --key <扭曲>` | 逐条反驳 |
| 想留存复盘 | `report` | 落 markdown |

## 文件导航

| 文件 | 内容 |
|------|------|
| `SKILL.md` | Agent 定义、主动触发、理论地图、子命令 |
| `scripts/soothe.py` | 真引擎（8 子命令，纯标准库） |
| `resources/soothe-scripts.json` | 认知破局剧本库（10 类扭曲 + 应对低效 + 情绪过载） |
| `resources/soothe-models.json` | 指标定义、阈值、主导扭曲推断逻辑 |
| `resources/soothe-domains.json` | 字段 schema、弱项规则、退出码、边界 |
| `references/` | 13 篇方法论长文（带出处） |
| `FAQ.md` | 按「你会怎么问」组织的高频问题 |
| `SELF_EVAL.md` | 五维自评（TRACE 全 5.0） |
| `CHANGELOG.md` | 版本与开发记录 |
| `examples/sample-soothe-log.md` | 端到端走查示例 |

## 情绪事件字段

| 字段 | 含义 | 必填 |
|------|------|------|
| emotion | 情绪类型（焦虑/愤怒/悲伤…） | 是 |
| trigger | 诱因（发生了什么） | 是 |
| intensity | 强度 1-5（1 轻微 5 失控） | 是 |
| thought | 自动思维/当时脑子里的话 | 否 |
| distortion | 认知扭曲 key（见下） | 否 |
| action | 当时用了什么方式应对 | 否 |
| relief | 缓解程度 0-5（0 没用 5 完全平复） | 否 |
| impact | 影响面：无/睡眠/关系/工作/身体/专注 | 否（默认无） |

## 十类认知扭曲（distortion 取值）

非黑即白 `all-or-nothing` · 以偏概全 `overgeneralization` · 心理过滤 `mental-filter` · 否定积极 `disqualify-positive` · 读心 `mind-reading` · 灾难预言 `fortune-telling` · 放大灾难 `magnification` · 情绪化推理 `emotional-reasoning` · 应该句式 `should` · 贴标签 `labeling` · 个人化 `personalization`

## 指标定义（窗口内统计）

- **频率**：件/周 = 窗口事件数 / (窗口天数/7)
- **平均强度**：intensity 均值（1-5）
- **强度趋势**：前半段 vs 后半段均值，差 >0.2 判升/降，否则平稳（同日记录保护为平稳）
- **主导认知扭曲**：出现最多的扭曲 tag，占比 ≥40% 才算清晰模式
- **应对有效性**：relief 均值（0-5），<2.5 判应对低效
- **高频诱因**：出现次数前 3 的 trigger
- **影响面**：睡眠/关系等波及占比

## 退出码

| 码 | 含义 |
|----|------|
| 0 | 正常（无中/高严重度弱项） |
| 1 | 需关注（risk/plan/report 存在中或高严重度） |
| 2 | 用法错误（未知子命令） |
| 4 | 参数或数据不可用（缺参/越界/资源缺失） |

## 边界

情绪调节教练，不是诊断，不替代医生/咨询师；有自伤/伤人风险请立即联系专业机构。数据全部留在本地 `--data` 目录，无网络请求。
