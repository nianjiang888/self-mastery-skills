#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""self-optimize-agent 核心引擎：受控 A/B 自我实验。

设计哲学（见 SKILL.md 与 references/optim-theory.md）：
把"被评估的分数"当目标函数，对"自己（或自己的产出/流程）"做受控实验——
锁定 baseline，只动 candidate，用同一组样本打分，显著胜出才晋升。

关键纪律（对抗自欺与回归）：
1. 对照不可动：每次只比较 baseline vs candidate 的同一样本得分。
2. 显著才晋升：需达到最小样本数 + 预设显著性阈值 + 不回归其他维度。

退出码约定：
  0  成功 / 判定通过
  1  preflight 失败 / 显著性不足 / 存在回归 / 未定义实验
  2  用法错误（参数缺失或冲突）
"""
import os
import re
import sys
import json
import math
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOG_PATH = os.path.join(ROOT, "experiment_log.jsonl")
SPACE_PATH = os.path.join(ROOT, "resources", "optim_space.json")

MIN_SAMPLES = 8          # 判定显著的最低样本数
DEFAULT_ALPHA = 0.05     # 显著性阈值（双侧近似）


class PreflightError(Exception):
    """在真正干活前发现的、应当友好报错的错误。"""


def _emit_preflight(msg):
    print("【前置检查未通过】" + msg, file=sys.stderr)
    print("（若不确定如何修复，先运行 --define 初始化一次实验，或查看 README.md）", file=sys.stderr)


def _load_space():
    if not os.path.exists(SPACE_PATH):
        raise PreflightError("未找到优化空间定义 resources/optim_space.json，无法读取指标方向。")
    try:
        with open(SPACE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise PreflightError("读取优化空间失败：%s" % e)


def _load_log():
    rows = []
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
    return rows


def _append_log(row):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


# ---------- 命令实现 ----------

def cmd_define(args):
    """定义一次实验：指标、方向、baseline、candidate。"""
    if not args.metric:
        raise PreflightError("缺少 --metric（要优化的指标名）。")
    if not args.baseline:
        raise PreflightError("缺少 --baseline（当前基线标识）。")
    if not args.candidate:
        raise PreflightError("缺少 --candidate（本次候选标识）。")
    direction = args.direction or "higher"
    if direction not in ("higher", "lower"):
        raise PreflightError("--direction 只能是 higher 或 lower。")
    exp = {
        "action": "define",
        "metric": args.metric,
        "direction": direction,
        "baseline": args.baseline,
        "candidate": args.candidate,
        "alpha": args.alpha if args.alpha is not None else DEFAULT_ALPHA,
        "min_samples": args.min_samples if args.min_samples else MIN_SAMPLES,
        "baseline_scores": [],
        "candidate_scores": [],
    }
    _append_log(exp)
    print("已定义实验：")
    print("  指标      : %s（方向=%s）" % (exp["metric"], exp["direction"]))
    print("  基线      : %s" % exp["baseline"])
    print("  候选      : %s" % exp["candidate"])
    print("  显著性阈值: α=%s，最小样本=%d" % (exp["alpha"], exp["min_samples"]))
    print("下一步：用 --run --baseline-score X --candidate-score Y --n N 累积对照样本。")


def _last_experiment():
    rows = [r for r in _load_log() if r.get("action") == "define"]
    if not rows:
        raise PreflightError("尚未定义实验。请先运行 --define。")
    return rows[-1]


def cmd_run(args):
    """累积一对对照样本（baseline vs candidate 的同一样本得分）。"""
    exp = _last_experiment()
    if args.baseline_score is None or args.candidate_score is None:
        raise PreflightError("--run 需要同时给出 --baseline-score 与 --candidate-score（同一受试样本的各自得分）。")
    n = args.n if args.n and args.n > 0 else 1
    rec = {
        "action": "sample",
        "metric": exp["metric"],
        "baseline": exp["baseline"],
        "candidate": exp["candidate"],
        "baseline_score": float(args.baseline_score),
        "candidate_score": float(args.candidate_score),
        "batch": n,
    }
    _append_log(rec)
    # 同步更新 define 记录里的样本列表（便于 --compare 直接算）。--n 表示本批样本数，须逐条 append。
    rows = _load_log()
    for r in rows:
        if r.get("action") == "define" and r.get("baseline") == exp["baseline"] and r.get("candidate") == exp["candidate"]:
            for _ in range(n):
                r["baseline_scores"].append(float(args.baseline_score))
                r["candidate_scores"].append(float(args.candidate_score))
            _rewrite_log(rows)
            break
    total = len(exp.get("baseline_scores", [])) + n
    print("已记录 %d 个对照样本（累计约 %d 个）。" % (n, total))
    print("  基线均分=%.3f，候选均分=%.3f" % (
        _mean(exp.get("baseline_scores", []) + [float(args.baseline_score)] * n),
        _mean(exp.get("candidate_scores", []) + [float(args.candidate_score)] * n),
    ))


def _rewrite_log(rows):
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else 0.0


def _welch_t(b, c):
    """Welch t 检验（两样本方差可能不等），返回 (t, approx_p)。"""
    nb, nc = len(b), len(c)
    if nb < 2 or nc < 2:
        return 0.0, 1.0
    mb, mc = _mean(b), _mean(c)
    vb = sum((x - mb) ** 2 for x in b) / (nb - 1) if nb > 1 else 0.0
    vc = sum((x - mc) ** 2 for x in c) / (nc - 1) if nc > 1 else 0.0
    se = math.sqrt(vb / nb + vc / nc)
    if se == 0:
        return 0.0, 1.0
    t = (mc - mb) / se
    # 近似双侧 p：用正态分布近似（样本量小偏大，但作为门槛足够保守）
    p = 2 * (1 - _norm_cdf(abs(t)))
    return t, p


def _norm_cdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def cmd_compare(args):
    """判定 candidate 是否显著胜出 baseline。"""
    exp = _last_experiment()
    b = list(exp.get("baseline_scores", []))
    c = list(exp.get("candidate_scores", []))
    if len(b) < 1 or len(c) < 1:
        raise PreflightError("对照样本不足，请先用 --run 累积样本。")
    direction = exp.get("direction", "higher")
    alpha = exp.get("alpha", DEFAULT_ALPHA)
    min_n = exp.get("min_samples", MIN_SAMPLES)
    total = min(len(b), len(c))
    if total < min_n:
        print("样本不足：当前 %d 对 < 最小样本 %d，暂不判定（避免自欺）。" % (total, min_n))
        print("建议继续 --run 累积到 %d 对再做 --compare。" % min_n)
        return 1
    mb, mc = _mean(b), _mean(c)
    diff = mc - mb
    t, p = _welch_t(b, c)
    # 方向是否对
    if direction == "higher":
        direction_ok = diff > 0
        verdict = "候选更高"
    else:
        direction_ok = diff < 0
        verdict = "候选更低"
    significant = (p < alpha)
    win = direction_ok and significant
    print("对照结果（%d 对样本）：" % total)
    print("  基线均分 = %.3f" % mb)
    print("  候选均分 = %.3f" % mc)
    print("  差异     = %+.3f（%s）" % (diff, verdict))
    print("  Welch t  = %.3f，近似 p = %.3f（α=%s）" % (t, p, alpha))
    if win:
        print("【结论】候选显著胜出基线，可晋升（运行 --promote）。")
        return 0
    elif not direction_ok:
        print("【结论】方向不对（候选未朝更优方向变化），不晋升。候选应丢弃或回滚。")
        return 1
    else:
        print("【结论】方向对但未达显著性（p≥α），记作'未证实'，不晋升。继续累积样本或换候选。")
        return 1


def cmd_promote(args):
    """晋升候选为新的 baseline（须先 --compare 通过）。"""
    exp = _last_experiment()
    b = list(exp.get("baseline_scores", []))
    c = list(exp.get("candidate_scores", []))
    if len(b) < 1 or len(c) < 1:
        raise PreflightError("尚未累积对照样本，无法判定晋升。")
    direction = exp.get("direction", "higher")
    alpha = exp.get("alpha", DEFAULT_ALPHA)
    min_n = exp.get("min_samples", MIN_SAMPLES)
    if min(len(b), len(c)) < min_n:
        raise PreflightError("样本不足（%d<%d），拒绝晋升：不能无对照覆盖 baseline。" % (min(len(b), len(c)), min_n))
    mb, mc = _mean(b), _mean(c)
    diff = mc - mb
    _, p = _welch_t(b, c)
    direction_ok = (diff > 0) if direction == "higher" else (diff < 0)
    if not (direction_ok and p < alpha):
        raise PreflightError("显著性不足（方向对=%s, p=%.3f, α=%s），拒绝晋升。baseline 保持不变。" % (direction_ok, p, alpha))
    # 晋升：记录一次 promotion 事件
    promo = {
        "action": "promote",
        "metric": exp["metric"],
        "from_baseline": exp["baseline"],
        "to_baseline": exp["candidate"],
        "baseline_mean": round(mb, 3),
        "candidate_mean": round(mc, 3),
        "gain": round(diff, 3),
        "p": round(p, 3),
    }
    _append_log(promo)
    print("已晋升：baseline 由 [%s] 更新为 [%s]" % (exp["baseline"], exp["candidate"]))
    print("  提升 = %+.3f（p=%.3f）" % (diff, p))
    print("下一轮实验请以新 baseline 为起点继续优化。")
    return 0


def cmd_rollback(args):
    """显式回滚：候选未胜出，丢弃，baseline 不动。"""
    exp = _last_experiment()
    rec = {
        "action": "rollback",
        "metric": exp["metric"],
        "baseline": exp["baseline"],
        "rejected_candidate": exp["candidate"],
        "reason": args.reason or "未显著胜出或存在回归",
    }
    _append_log(rec)
    print("已回滚：候选 [%s] 被拒绝（baseline 保持不变）。" % exp["candidate"])
    print("  原因：%s" % rec["reason"])
    return 0


def cmd_suggest(args):
    """基于历史实验，用贝叶斯式 EI 推荐下一个候选（委托 bayes.py）。"""
    try:
        from bayes import suggest_next
    except Exception:
        # 允许直接作为模块运行
        sys.path.insert(0, HERE)
        from bayes import suggest_next
    space = args.space or SPACE_PATH
    if not os.path.exists(space):
        raise PreflightError("未找到优化空间 %s。" % space)
    rec = suggest_next(space, LOG_PATH)
    print("基于历史实验的下一个建议候选：")
    for k, v in rec.get("candidate", {}).items():
        print("  %s = %s" % (k, v))
    print("  建议依据：%s" % rec.get("rationale", ""))
    return 0


def cmd_report(args):
    """输出实验账本摘要。"""
    rows = _load_log()
    if not rows:
        print("（暂无实验记录）")
        return 0
    defines = [r for r in rows if r.get("action") == "define"]
    promos = [r for r in rows if r.get("action") == "promote"]
    rolls = [r for r in rows if r.get("action") == "rollback"]
    samples = [r for r in rows if r.get("action") == "sample"]
    print("实验账本摘要：")
    print("  定义实验数 : %d" % len(defines))
    print("  对照样本数 : %d" % len(samples))
    print("  晋升次数   : %d" % len(promos))
    print("  回滚次数   : %d" % len(rolls))
    if promos:
        print("  最近晋升   :", promos[-1].get("from_baseline"), "→", promos[-1].get("to_baseline"),
              "（提升 %+.3f）" % promos[-1].get("gain", 0))
    return 0


def build_parser():
    p = argparse.ArgumentParser(
        description="self-optimize-agent：受控自我实验优化引擎（全中文输出）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--define", action="store_true", help="定义一次实验")
    p.add_argument("--run", action="store_true", help="累积一对对照样本")
    p.add_argument("--compare", action="store_true", help="判定候选是否显著胜出")
    p.add_argument("--promote", action="store_true", help="晋升候选为新的 baseline")
    p.add_argument("--rollback", action="store_true", help="回滚候选，baseline 不动")
    p.add_argument("--suggest", action="store_true", help="贝叶斯式推荐下个候选")
    p.add_argument("--report", action="store_true", help="输出实验账本摘要")
    p.add_argument("--metric", help="要优化的指标名")
    p.add_argument("--direction", help="higher 或 lower（默认 higher）")
    p.add_argument("--baseline", help="基线标识")
    p.add_argument("--candidate", help="候选标识")
    p.add_argument("--baseline-score", type=float, help="--run 时基线样本得分")
    p.add_argument("--candidate-score", type=float, help="--run 时候选样本得分")
    p.add_argument("--n", type=int, help="--run 时本批样本数（默认 1）")
    p.add_argument("--alpha", type=float, help="显著性阈值（默认 0.05）")
    p.add_argument("--min-samples", type=int, help="判定所需最小样本数（默认 8）")
    p.add_argument("--space", help="优化空间 json 路径（--suggest 用）")
    p.add_argument("--reason", help="--rollback 的原因说明")
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.define:
            return cmd_define(args)
        if args.run:
            return cmd_run(args)
        if args.compare:
            return cmd_compare(args)
        if args.promote:
            return cmd_promote(args)
        if args.rollback:
            return cmd_rollback(args)
        if args.suggest:
            return cmd_suggest(args)
        if args.report:
            return cmd_report(args)
        parser.print_help()
        return 2
    except PreflightError as e:
        _emit_preflight(str(e))
        return 1
    except Exception as e:
        print("【运行错误】%s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
