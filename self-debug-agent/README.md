# self-debug-agent 使用导航

> 自主调试引擎：复现 → 归类 → 治愈 → 验证 → 回归。让 Agent（或你）自主调试自己写的程序，并把每个 bug 变成永久抗体。

## 文件导航

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 引擎定义、主动触发段、边界红线、与 self 系列关系 |
| `scripts/debug.py` | 调试纪律引擎：复现 / 归类 / 治愈循环 / 验证 / 自动回归 / 报告 |
| `scripts/localize.py` | SBFL 频谱故障定位（Tarantula + Ochiai 可疑度排序）|
| `resources/bug_taxonomy.json` | 六类 bug 签名、根因、修法、探针提示 |
| `references/debug-theory.md` | 调试理论：假设检验 / Delta Debugging / Self-Debugging / SBFL |
| `references/repro-method.md` | 复现方法学：最小复现 / 环境钉固 / flaky 隔离 |
| `references/regression-culture.md` | 回归文化：每 bug→永久回归测试、学习闭环 |
| `FAQ.md` | 场景问答 |
| `SELF_EVAL.md` | 用 TRACE 五维对本包做深度自评 |

## 快速上手

```bash
# 1) 复现：萃取最小失败事实
python3 scripts/debug.py --reproduce --trace /tmp/trace.txt --code app.py

# 2) 归类 + 定位
python3 scripts/debug.py --classify --trace /tmp/trace.txt --code app.py
python3 scripts/localize.py --spectrum spectrum.json --top 10

# 3) 治愈循环（失败→根因反思→重试行）
python3 scripts/debug.py --heal --trace /tmp/trace.txt --code app.py --max-rounds 5

# 4) 验证修复
python3 scripts/debug.py --verify --test "pytest -q"

# 5) 免疫：把 bug 落成永久回归测试
python3 scripts/debug.py --regress --bug "空列表时除零" --case "summarize([])" --expect "抛 ValueError"

# 6) 复盘：治愈台账 + 回归墙
python3 scripts/debug.py --report
```

## 退出码

| 码 | 含义 |
|---|---|
| 0 | 成功（复现成立 / 验证通过 / 记录完成）|
| 1 | 纪律拦截（前置不满足，如没复现就修、回归含脆弱特征）|
| 2 | 无法复现（无错误类型）|
| 3 | 验证失败 / 治愈未收敛 |
| 4 | 参数错误 |

## 核心纪律（红线）

- 不复现，不修；
- 不靠感觉定位（宣称病灶必须附证据）；
- 不吞错误（`try/except: pass` 压错不算治愈）；
- 不制造脆弱测试（断言必须确定性）；
- 不过度自信（到上限没收敛就如实报告卡点）。

## 理论根基

- Self-Debugging（Chen et al., ICLR 2024）
- Delta Debugging（Zeller, FSE 1999）
- SBFL：Tarantula（Jones & Harrold 2002）/ Ochiai（Abreu et al. 2007）
