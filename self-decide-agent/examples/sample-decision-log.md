# 示例：一次完整可重跑的决策复盘轨迹

下面用一组真实可跑的输入，展示 `self-decide-agent` 的 7 个子命令如何串成闭环。复制粘贴即可复现。

## 0) 先看框架库

```bash
python scripts/decide.py frameworks
python scripts/decide.py frameworks --id bezos_doors
```

## 1) 事前：假设已经失败 + 二阶 + 可逆性校验

```bash
python scripts/decide.py premortem --context "是否接受A公司异地offer" --reversibility irreversible
```

生成 `premortem-是否接受A公司异地offer.md`，含五步：假设失败 → 反推失败模式 → 二阶连锁 → 单向门标准 → 后悔最小化。

## 2) 当下：锁定决策（含偏差预检 + 框架标注）

```bash
# 决策一：投资怕亏
python scripts/decide.py log --context "投资怕亏本想保住本金" \
    --options "持有;卖出" --chosen "持有" --expected "不亏钱" \
    --reversibility reversible --framework loss_aversion
#   → 输出检测到「损失厌恶」

# 决策二：异地 offer（单向门）
python scripts/decide.py log --context "是否接受异地offer" \
    --options "去;不去" --chosen "去" --expected "薪资+30%、三年晋升" \
    --reversibility irreversible --framework bezos_doors
```

## 3) 事后：回放打分 + 纠正可逆性误判

```bash
# 半年后回放 d2：其实可协商远程 → 原 irreversible 判错
python scripts/decide.py replay --id d2 --actual "成长不及预期，但可协商远程" \
    --outcome "职业曲线尚可" --score 45 --regret 60 --reversibility reversible
#   → 标记「可逆性误判」，写出 replay-d2.md
```

## 4) 模式：识别反复偏差

```bash
python scripts/decide.py bias
#   → 若损失厌恶出现 ≥2 次，退出 1，提示建检查清单
```

## 5) 报告：聚合误判率 + 常犯偏差 + 后悔最小化

```bash
python scripts/decide.py report
#   → 输出 decision-report.md，退出码 0/1/4 视严重程度
```

## 6) 查看已记录

```bash
python scripts/decide.py list
```

---

每一步都落一份文件产物（`decision-log.jsonl` + 各类 `.md`），且任意时刻重跑 `bias`/`report` 得到一致结论——这是「可重跑」与「留实物证据」的双重保证。
