#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""self-evaluate-agent · 元认知校准子命令 calibrate.py v2.0.0。

元认知（metacognition）的可计算那一半：不只是"做事"，而是"知道自己做得对不对"。
本脚本量化"你以为你知道"和"实际对不对"之间的偏差——过度自信是 AI 和人类共同的监控失灵。

指标：
  - Brier Score：概率预测的均方误差，0=完美，越高越差。
  - 分桶校准（reliability）：把自信度分桶，比较"平均自信"和"实际准确率"。
  - 过度自信指数 OCI = (平均自信 − 实际准确率)，正=过度自信，负=欠自信。
  - 桶级校准误差：每桶 |平均自信 − 实际准确率|。

用法：
  calibrate.py --record "这段代码无越界" 0.9 0      # 记一条：我以为90%对，实际错(0)
  calibrate.py --record "函数返回非空" 0.7 1        # 记一条：我以为70%对，实际对(1)
  calibrate.py --analyze [--bins 10]                # 出校准报告
  calibrate.py --history                             # 看历史样本

日志留本地（calibration_log.jsonl），是你私人的"自知之明账本"。
"""
import sys, os, json, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CALIB_LOG = os.path.join(ROOT, "calibration_log.jsonl")

class PreflightError(Exception):
    def __init__(self, msg, code=1):
        super().__init__(msg)
        self.code = code

def _now():
    return datetime.datetime.now().isoformat(timespec="seconds")

def _load():
    if not os.path.isfile(CALIB_LOG):
        return []
    return [json.loads(l) for l in open(CALIB_LOG, encoding="utf-8") if l.strip()]

def cmd_record(claim, conf, outcome):
    try:
        conf = float(conf)
        outcome = int(outcome)
    except (TypeError, ValueError):
        raise PreflightError("--record 需要 <主张> <置信度0-1> <实际对错0/1>", 1)
    if not (0.0 <= conf <= 1.0):
        raise PreflightError("置信度必须在 0-1 之间，收到：%s" % conf, 1)
    if outcome not in (0, 1):
        raise PreflightError("实际对错必须是 0 或 1，收到：%s" % outcome, 1)
    rec = {"ts": _now(), "claim": claim, "confidence": conf, "outcome": outcome}
    with open(CALIB_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    verdict = "打脸了（过度自信）" if (conf >= 0.8 and outcome == 0) else ("吻合" if outcome == 1 else "低估了")
    print("✅ 已记录：自信 %.2f / 实际 %d → %s" % (conf, outcome, verdict))
    print("   %s" % claim)
    print("   日志：%s" % CALIB_LOG)

def cmd_analyze(bins):
    rows = _load()
    if len(rows) < 2:
        raise PreflightError("样本太少（%d 条），至少 2 条才能算校准；先 --record 几条" % len(rows), 3)
    confs = [r["confidence"] for r in rows]
    outs = [r["outcome"] for r in rows]
    n = len(rows)
    mean_conf = sum(confs) / n
    accuracy = sum(outs) / n                      # 实际正确率
    # Brier Score = mean((conf - outcome)^2)
    brier = sum((c - o) ** 2 for c, o in zip(confs, outs)) / n
    # 过度自信指数（原始定义：自信 − 准确率）
    oci = mean_conf - accuracy

    print("=" * 60)
    print("元认知校准报告（%d 条样本）" % n)
    print("-" * 60)
    print("  平均自信度：%.3f" % mean_conf)
    print("  实际准确率：%.3f" % accuracy)
    print("  Brier Score：%.3f   （0=完美校准，越接近0越好）" % brier)
    print("  过度自信指数 OCI：%+.3f   （正=过度自信，负=欠自信）" % oci)

    # 分桶校准
    print("-" * 60)
    print("  分桶校准（自信区间 | 样本数 | 平均自信 | 实际准确率 | 偏差）：")
    edges = [i / bins for i in range(bins + 1)]
    bucket_stats = []
    for b in range(bins):
        lo, hi = edges[b], edges[b + 1]
        cell = [r for r in rows if lo <= r["confidence"] <= (hi if b < bins - 1 else hi + 1e-9) or
                (b == bins - 1 and abs(r["confidence"] - 1.0) < 1e-9)]
        if not cell:
            continue
        cmean = sum(x["confidence"] for x in cell) / len(cell)
        omean = sum(x["outcome"] for x in cell) / len(cell)
        bias = cmean - omean
        bucket_stats.append((lo, hi, len(cell), cmean, omean, bias))
        print("    [%.2f,%.2f] | %2d | %.3f | %.3f | %+.3f"
              % (lo, hi, len(cell), cmean, omean, bias))

    # 结论与建议
    print("-" * 60)
    if oci > 0.10:
        print("  结论：显著过度自信。你对自己的判断过于乐观——高自信常常配不上高正确率。")
        print("  建议：① 任何 conf≥0.8 的主张，强制找一条反例再放行；")
        print("        ② 用 --record 持续记，让 OCI 随样本变多自然回落；")
        print("        ③ 把'我确定'改成'我赌 X% 对'，把模糊自信变成可测数字。")
    elif oci < -0.10:
        print("  结论：欠自信。你低估了自己——实际对的比你说的多。")
        print("  建议：适度提高公开置信度，避免无谓的'可能/大概'稀释可信度。")
    else:
        print("  结论：校准良好，自信与准确率基本匹配。保持记录以维持。")
    # 最危险桶：高自信但低准确率
    danger = [b for b in bucket_stats if b[3] >= 0.7 and b[4] < b[3] - 0.15]
    if danger:
        worst = max(danger, key=lambda b: b[3] - b[4])
        print("  ⚠ 最危险区间：[%.2f,%.2f] —— 平均自信 %.2f 却只对了 %.2f，是过度自信重灾区。"
              % (worst[0], worst[1], worst[3], worst[4]))
    print("=" * 60)

def cmd_history():
    rows = _load()
    if not rows:
        print("（暂无校准样本）")
        return
    for r in rows:
        mark = "✓对" if r["outcome"] == 1 else "✗错"
        print("  %s  自信%.2f  %s  %s" % (r["ts"], r["confidence"], mark, r["claim"][:40]))

def _parse_argv(argv):
    a = {}
    i = 0
    while i < len(argv):
        x = argv[i]
        if x == "--record":
            if i + 3 >= len(argv):
                raise PreflightError("--record 需要 <主张> <置信度> <实际对错>", 1)
            a["record"] = [argv[i + 1], argv[i + 2], argv[i + 3]]; i += 4
        elif x == "--analyze":
            a["analyze"] = True; i += 1
        elif x == "--history":
            a["history"] = True; i += 1
        elif x == "--bins":
            if i + 1 >= len(argv):
                raise PreflightError("缺少 --bins 的值", 1)
            a["bins"] = int(argv[i + 1]); i += 2
        else:
            i += 1
    return a

def main():
    try:
        a = _parse_argv(sys.argv[1:])
    except PreflightError as e:
        print("❌ %s" % e); sys.exit(e.code)
    try:
        if "record" in a:
            cmd_record(a["record"][0], a["record"][1], a["record"][2])
        elif "analyze" in a:
            cmd_analyze(a.get("bins", 10))
        elif "history" in a:
            cmd_history()
        else:
            print("用法：")
            print("  calibrate.py --record \"<主张>\" <置信度0-1> <实际对错0/1>")
            print("  calibrate.py --analyze [--bins 10]")
            print("  calibrate.py --history")
            sys.exit(1)
    except PreflightError as e:
        print("❌ %s" % e); sys.exit(e.code)
    except ValueError as e:
        print("❌ 参数数值非法：%s" % e); sys.exit(1)
    except Exception as e:
        print("❌ 意外错误：%s" % e); sys.exit(3)

if __name__ == "__main__":
    main()
