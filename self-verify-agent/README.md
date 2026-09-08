# self-verify-agent · 正确性验证与交付门禁引擎

在"相信 / 发布"之前，自己对自己的结论做正交复核：执行门禁 + 自洽性 + 步骤核对 + 证伪探针。
**不达标物理拦下。** 与 self-evaluate（质量）、self-debug（修复）同宗，构成自我修正流水线。

## 文件导航

```
self-verify-agent/
├── SKILL.md                      引擎定义、主动触发、边界
├── scripts/
│   ├── verify.py                 门禁引擎（gate/stepcheck/probe/checks/record）
│   └── consistency.py            自洽性硬核（Self-Consistency 多数投票 + 收敛度）
├── resources/
│   └── verify_checks.json        五类验证清单（EXEC/SELF_CONSISTENCY/STEP/EDGE/ALIGN）
├── references/
│   ├── verify-theory.md          验证哲学 + 三大理论根基 + DeepSeek 反例
│   ├── self-consistency-method.md 多路径采样、收敛度量化、失效边界
│   └── assertion-culture.md      断言文化、门禁、记命中率
├── FAQ.md                        场景应对与"自我验证 vs 自评"辨析
├── README.md                     本文件
└── SELF_EVAL.md                  本包 TRACE 五维自评（5.0/5）
```

## 快速上手

### 1) 执行门禁（最常用）
```bash
# 不通过 → 退出码 1，物理拦下
python3 scripts/verify.py --gate --command "pytest -q"
# 预期应当失败的场景（如验证一个 bug 真的存在）
python3 scripts/verify.py --gate --command "python3 should_fail.py" --expect-fail
```

### 2) 自洽性（多条路径收敛度）
```bash
# 把多条推理路径存进文件，用 ---- 分段，或写成 JSON 数组
python3 scripts/consistency.py --vote --file 路径.txt
# 看演示（5 条路径 3:2 分裂）
python3 scripts/consistency.py --demo
```

### 3) 步骤核对（PRM 风格）
```bash
python3 scripts/verify.py --stepcheck --text "步骤1...\n步骤2...\n步骤3..."
```

### 4) 证伪探针
```bash
python3 scripts/verify.py --probe --text "这个方法永远有效，因为..."
```

### 5) 加载验证清单
```bash
python3 scripts/verify.py --checks            # 全部五类
python3 scripts/verify.py --checks ALIGN      # 只对齐类
```

### 6) 记录验证命中率
```bash
python3 scripts/verify.py --record "我当时验证过空列表不崩" 1   # 后来证明对
python3 scripts/verify.py --record "我以为并发安全" 0            # 后来证明错
```

## 退出码约定

| 退出码 | 含义 |
|--------|------|
| 0 | 验证通过 / 收敛 / 无薄弱点 |
| 1 | 门禁拦下 / 未收敛 / 存在存疑步或可被推翻点 |
| 2 | 预检未过（参数非法、文件缺失等），详见 stderr 中文报错 |

## 依赖

纯 Python 3.8+ 标准库，无第三方依赖。所有日志（verify_log.jsonl）仅落本地，打包时已排除。
