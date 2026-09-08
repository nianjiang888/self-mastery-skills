#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""self-debug-agent 频谱故障定位（SBFL）。

给定程序的「频谱」——每一行代码被多少通过测试覆盖、被多少失败测试覆盖——
用经典 SBFL 公式给每行算「可疑度」，排出最可能是病根的行。

公式：
  Tarantula:  suspicious = (Fp/(Fp+Ff)) / ( Fp/(Fp+Ff) + Sp/(Sp+Sf) )
              Fp=该行被失败测试覆盖次数, Ff=该行被通过测试覆盖次数
              Sp=失败测试总数, Sf=通过测试总数
  Ochiai:     suspicious = Fp / sqrt( Sf_total * (Fp+Ff) )
              Sf_total=失败测试总数, Sf=通过测试总数

文献：Jones & Harrold 2002 (Tarantula)；Abreu et al. 2007 (Ochiai)。
Ochiai 在多项实证中稳定优于 Tarantula，故默认以 Ochiai 排序。
"""
import sys
import os
import json

EXIT_BAD_ARGS = 4


def _demo_spectrum():
    """内置示例：一个明显有 bug 的函数，3 通过 1 失败。"""
    # 行: passed(被通过测试覆盖次数), failed(被失败测试覆盖次数)
    return [
        {"line": 1, "src": "def divide(a, b):", "passed": 4, "failed": 1},
        {"line": 2, "src": "    if b == 0:", "passed": 4, "failed": 1},
        {"line": 3, "src": "        return 0", "passed": 1, "failed": 0},
        {"line": 4, "src": "    return a / b", "passed": 3, "failed": 1},
        {"line": 5, "src": "def main():", "passed": 4, "failed": 1},
    ]


def _tarantula(passed_cov, failed_cov, total_passed, total_failed):
    if total_passed == 0 and total_failed == 0:
        return 0.0
    nf = failed_cov / total_failed if total_failed else 0.0
    ns = passed_cov / total_passed if total_passed else 0.0
    denom = nf + ns
    return nf / denom if denom else 0.0


def _ochiai(failed_cov, passed_cov, total_failed, total_passed):
    denom = (total_failed) * (failed_cov + passed_cov)
    if denom <= 0:
        return 0.0
    return failed_cov / (denom ** 0.5)


def localize(spectrum, total_passed, total_failed, top=None):
    rows = []
    for s in spectrum:
        f = s.get("failed", 0)
        p = s.get("passed", 0)
        tar = _tarantula(p, f, total_passed, total_failed)
        och = _ochiai(f, p, total_failed, total_passed)
        rows.append({
            "line": s.get("line"),
            "src": s.get("src", ""),
            "passed": p, "failed": f,
            "tarantula": round(tar, 4),
            "ochiai": round(och, 4),
        })
    rows.sort(key=lambda r: r["ochiai"], reverse=True)
    if top:
        rows = rows[:top]
    return rows


def _print(rows):
    print("【频谱故障定位】按 Ochiai 可疑度降序（Top 病灶在前）")
    print("%-5s %-9s %-9s %-10s %-10s  %s" % ("行", "通过覆盖", "失败覆盖", "Tarantula", "Ochiai", "源码"))
    for r in rows:
        print("%-5s %-9s %-9s %-10s %-10s  %s" % (
            r["line"], r["passed"], r["failed"], r["tarantula"], r["ochiai"], r["src"]))


def main(argv):
    spectrum = None
    total_passed = 0
    total_failed = 0
    top = None
    i = 0
    demo = False
    while i < len(argv):
        a = argv[i]
        if a == "--demo":
            demo = True
        elif a == "--top":
            top = int(argv[i + 1]); i += 1
        elif a == "--spectrum":
            with open(argv[i + 1], "r", encoding="utf-8") as f:
                data = json.load(f)
            spectrum = data.get("lines", data if isinstance(data, list) else [])
            total_passed = data.get("total_passed", 0)
            total_failed = data.get("total_failed", 0)
            i += 1
        i += 1

    if demo or spectrum is None:
        if spectrum is None:
            print("（未提供 --spectrum，使用内置示例）")
            spectrum = _demo_spectrum()
            total_passed = 4
            total_failed = 1
    rows = localize(spectrum, total_passed, total_failed, top)
    _print(rows)
    if rows:
        top1 = rows[0]
        print("\n最可能病灶：第 %s 行「%s」（Ochiai=%.4f）" % (top1["line"], top1["src"], top1["ochiai"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
