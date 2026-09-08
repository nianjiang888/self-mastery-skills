#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""self-optimize-agent 的贝叶斯式建议器（可计算硬核）。

对标 self-evaluate 的 calibrate.py（元认知校准）、self-debug 的 localize.py（SBFL）、
self-verify 的 consistency.py（Self-Consistency）：用可计算的数学把"下一步试什么"变成数字。

方法（见 references/optim-theory.md）：
1. 把每个历史实验点 (旋钮组合 x, 得分 y) 当作观测。
2. 用简单核回归（kernel regression，高斯核）拟合成代理模型，给出任意 x 的预测均值与不确定性。
3. 用 Expected Improvement（EI）采集函数，在搜索空间里挑"最值得试"的下一个 x。

EI(x) = E[ max(0, f(x) - f_best) ]，对高斯预测近似为：
    if σ>0: EI = Δ·Φ(Δ/σ) + σ·φ(Δ/σ)
    else:   0
其中 Δ = μ(x) - f_best + ξ（ξ 为探索抖动，默认 0.01），Φ/φ 为正态 CDF/PDF。

为保持轻量、零依赖、全中文可解释，本实现用网格/随机候选点枚举 + 高斯核回归，
不引入 scipy。对中小搜索空间足够，且每一步都可被用户读懂。
"""
import os
import re
import sys
import json
import math
import argparse
import itertools

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOG_PATH = os.path.join(ROOT, "experiment_log.jsonl")


def _norm_cdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def _norm_pdf(z):
    return math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)


def _load_history(space, log_path):
    """从日志抽取 (x_dict, y) 观测。x 的键来自 space 的 knobs。"""
    knobs = space.get("knobs", {})
    rows = []
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                # 仅取 sample 记录里带 knob 配置的；为演示用，兼容 --run 不带 knob 的情况
                if r.get("action") == "sample" and "knobs" in r:
                    rows.append((r["knobs"], float(r.get("candidate_score", r.get("baseline_score", 0)))))
    return knobs, rows


def _encode(knobs, combo):
    """把旋钮组合编码成数值向量（连续→原值，离散/类别→枚举下标）。"""
    vec = []
    for name in knobs:
        spec = knobs[name]
        typ = spec.get("type", "continuous")
        val = combo.get(name)
        if typ == "continuous":
            lo, hi = spec["range"]
            if hi == lo:
                vec.append(0.0)
            else:
                vec.append((float(val) - lo) / (hi - lo))
        else:
            opts = spec["values"]
            idx = opts.index(val) if val in opts else 0
            vec.append(float(idx) / max(1, len(opts) - 1))
    return vec


def _kernel(a, b, length=1.0):
    d = sum((x - y) ** 2 for x, y in zip(a, b))
    return math.exp(-0.5 * d / (length * length))


def _predict(vec, X, Y, length=1.0, sigma_n=1e-6):
    """核回归预测：均值 + 不确定性（留一近似的不确定度）。"""
    if not X:
        return 0.0, 1.0
    num = 0.0
    den = 0.0
    for xi, yi in zip(X, Y):
        w = _kernel(vec, xi, length)
        num += w * yi
        den += w
    mu = (num / den) if den > 0 else 0.0
    # 不确定度：与【最近】已知点的距离越小越确定（kernel 越接近 1，uncertainty 越接近 0）
    max_k = max(_kernel(vec, xi, length) for xi in X)
    uncertainty = 1.0 - max_k
    return mu, max(uncertainty, sigma_n)


def _expected_improvement(mu, sigma, f_best, xi=0.01, direction="higher"):
    if sigma <= 0:
        return 0.0
    if direction == "higher":
        delta = mu - f_best + xi
    else:
        delta = f_best - mu + xi
    z = delta / sigma
    ei = delta * _norm_cdf(z) + sigma * _norm_pdf(z)
    return max(0.0, ei)


def _enumerate_combos(knobs, cap=2000):
    """枚举（或随机采样）候选组合，避免组合爆炸。"""
    domains = {}
    for name, spec in knobs.items():
        typ = spec.get("type", "continuous")
        if typ == "continuous":
            lo, hi = spec["range"]
            step = spec.get("step", (hi - lo) / 10.0)
            vals = []
            v = lo
            while v <= hi + 1e-9:
                vals.append(round(v, 4))
                v += step
            domains[name] = vals
        else:
            domains[name] = spec["values"]
    keys = list(domains.keys())
    combos = []
    for vals in itertools.product(*[domains[k] for k in keys]):
        combos.append(dict(zip(keys, vals)))
        if len(combos) >= cap:
            break
    return combos


def suggest_next(space_path, log_path):
    """返回 {'candidate': {...}, 'rationale': str}。"""
    with open(space_path, "r", encoding="utf-8") as f:
        space = json.load(f)
    knobs, history = _load_history(space, log_path)
    direction = space.get("direction", "higher")
    f_best = max((y for _, y in history), default=space.get("baseline_score", 0.0))
    X = [_encode(knobs, x) for x, _ in history]
    Y = [y for _, y in history]
    combos = _enumerate_combos(knobs)
    best = None
    best_ei = -1.0
    for combo in combos:
        vec = _encode(knobs, combo)
        if vec in X:
            continue  # 已试过，跳过
        mu, sigma = _predict(vec, X, Y, length=0.2)
        ei = _expected_improvement(mu, sigma, f_best, direction=direction)
        if ei > best_ei:
            best_ei = ei
            best = combo
    if best is None:
        return {"candidate": {}, "rationale": "搜索空间已穷尽或所有组合均已试过，建议扩大 space 或停止。"}
    rationale = "在历史 %d 个观测上做核回归代理，用 Expected Improvement 选不确定且可能更高的区域；当前最佳=%s。" % (
        len(history), round(f_best, 3))
    return {"candidate": best, "rationale": rationale}


def cmd_suggest(args):
    space = args.space
    if not space or not os.path.exists(space):
        space = os.path.join(ROOT, "resources", "optim_space.json")
    if not os.path.exists(space):
        print("【前置检查未通过】未找到优化空间 %s" % space, file=sys.stderr)
        return 1
    rec = suggest_next(space, LOG_PATH)
    print("基于历史实验的下一个建议候选：")
    if not rec["candidate"]:
        print("  " + rec["rationale"])
    else:
        for k, v in rec["candidate"].items():
            print("  %s = %s" % (k, v))
        print("  建议依据：%s" % rec["rationale"])
    return 0


def cmd_demo(args):
    """内置演示：用合成历史展示 EI 推荐逻辑。"""
    demo_space = {
        "direction": "higher",
        "baseline_score": 0.5,
        "knobs": {
            "temperature": {"type": "continuous", "range": [0.0, 1.0], "step": 0.1},
        },
    }
    demo_log = os.path.join(ROOT, "_demo_log.jsonl")
    with open(demo_log, "w", encoding="utf-8") as f:
        # 合成：温度 0.2 附近较好
        samples = [
            ({"temperature": 0.0}, 0.40),
            ({"temperature": 0.2}, 0.66),
            ({"temperature": 0.4}, 0.72),
            ({"temperature": 0.6}, 0.60),
            ({"temperature": 0.8}, 0.50),
            ({"temperature": 1.0}, 0.30),
        ]
        for x, y in samples:
            f.write(json.dumps({"action": "sample", "knobs": x, "candidate_score": y}) + "\n")
    rec = _suggest_with_space(demo_space, demo_log)
    print("演示（合成历史：温度 0.2 附近得分高）：")
    for k, v in rec["candidate"].items():
        print("  %s = %s" % (k, v))
    print("  依据：%s" % rec["rationale"])
    try:
        os.remove(demo_log)
    except Exception:
        pass
    return 0


def _suggest_with_space(space, log_path):
    knobs = space.get("knobs", {})
    # 解析合成日志
    history = []
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                if r.get("action") == "sample" and "knobs" in r:
                    history.append((r["knobs"], float(r.get("candidate_score", 0))))
    direction = space.get("direction", "higher")
    f_best = max((y for _, y in history), default=space.get("baseline_score", 0.0))
    X = [_encode(knobs, x) for x, _ in history]
    Y = [y for _, y in history]
    combos = _enumerate_combos(knobs)
    best, best_ei = None, -1.0
    for combo in combos:
        vec = _encode(knobs, combo)
        if vec in X:
            continue
        mu, sigma = _predict(vec, X, Y, length=0.2)
        ei = _expected_improvement(mu, sigma, f_best, direction=direction)
        if ei > best_ei:
            best_ei, best = ei, combo
    if best is None:
        return {"candidate": {}, "rationale": "空间穷尽"}
    return {"candidate": best, "rationale": "EI 推荐；历史最佳=%s" % round(f_best, 3)}


def build_parser():
    p = argparse.ArgumentParser(description="self-optimize-agent 贝叶斯式建议器")
    p.add_argument("--suggest", action="store_true", help="推荐下一个候选")
    p.add_argument("--space", help="优化空间 json 路径")
    p.add_argument("--demo", action="store_true", help="内置演示")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.demo:
            return cmd_demo(args)
        if args.suggest:
            return cmd_suggest(args)
        print("请指定 --suggest 或 --demo。")
        return 2
    except Exception as e:
        print("【运行错误】%s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
