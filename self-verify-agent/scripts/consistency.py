#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""self-verify-agent 的自洽性硬核：Self-Consistency 的可计算实现。

核心思想（Wang et al., 2022, Google）：
  对同一个问题采样多条独立的推理路径，每条路径给出最终答案，
  取"出现次数最多的答案"作为结论；最高票占比即「收敛度」——
  收敛度越高，结论越可信。

本脚本把这件事做成可运行、可量化的工具，对标：
  - self-evaluate 的 calibrate.py（Brier/OCI 校准）
  - self-debug   的 localize.py（Ochiai 可疑度）
三者都是"把模糊的'我感觉'变成数字"的硬核引擎。

仅用标准库，中文输出。开关式 CLI 与文档示例一致。
"""

import argparse
import json
import os
import re
import sys

ANSWER_PATTERNS = [
    re.compile(r"(?:answer|最终答案|结果|答案|结论)\s*[:：=]?\s*(?:是|为)?\s*([0-9][0-9.,]*|true|false|yes|no)", re.IGNORECASE),
    re.compile(r"(?:the answer is|result is|equals?)\s*([0-9][0-9.,]*)", re.IGNORECASE),
]


def _extract_answer(text):
    if not text:
        return None
    candidates = []
    for pat in ANSWER_PATTERNS:
        for m in pat.finditer(text):
            candidates.append(m.group(1).strip().lower())
    if candidates:
        return candidates[-1]
    nums = re.findall(r"[0-9][0-9.,]*", text)
    if nums:
        return nums[-1]
    return None


def vote(paths):
    answers = [_extract_answer(p) for p in paths]
    valid = [(i, a) for i, a in enumerate(answers) if a is not None]
    if not valid:
        return {"ok": False, "reason": "没有任何路径能抽出最终答案，无法投票。"}
    counts = {}
    for _, a in valid:
        counts[a] = counts.get(a, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    top_answer, top_count = ranked[0]
    convergence = top_count / len(valid)
    outliers = [i for i, a in valid if a != top_answer]
    return {
        "ok": True,
        "total_paths": len(paths),
        "valid_paths": len(valid),
        "ranking": ranked,
        "top_answer": top_answer,
        "top_count": top_count,
        "convergence": round(convergence, 3),
        "outlier_indices": outliers,
        "verdict": "收敛" if convergence >= 0.6 else "未收敛（置信度不足）",
    }


def cmd_vote_file(path):
    if not os.path.exists(path):
        print("【预检未过】找不到路径文件：%s" % path, file=sys.stderr)
        return 2
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if content.strip().startswith("["):
        try:
            paths = json.loads(content)
        except Exception as e:
            print("【预检未过】JSON 解析失败：%s" % e, file=sys.stderr)
            return 2
    else:
        paths = [blk.strip() for blk in re.split(r"\n-{3,}\n", content) if blk.strip()]
    return _print_vote(paths)


def _print_vote(paths):
    res = vote(paths)
    if not res.get("ok"):
        print("【自洽性】%s" % res["reason"])
        return 1
    print("【自洽性】路径总数 %d，有效 %d。" % (res["total_paths"], res["valid_paths"]))
    print("【自洽性】投票排名：")
    for ans, cnt in res["ranking"]:
        print("   - 答案「%s」：%d 票" % (ans, cnt))
    print("【自洽性】最高票「%s」占 %.1f%% —— %s。" %
          (res["top_answer"], res["convergence"] * 100, res["verdict"]))
    if res["outlier_indices"]:
        print("【自洽性·警告】第 %s 条路径与多数不一致，它们是潜在错误源，应单独复核。"
              % (",".join(str(i + 1) for i in res["outlier_indices"])))
    if res["convergence"] < 0.6:
        print("【自洽性·拦下】收敛度低于 0.6，结论未稳，别急着交付。")
        return 1
    print("【自洽性·通过】✅ 多路径收敛，结论可信度较高。")
    return 0


def cmd_demo():
    print("【演示】一道算术题：商店 25% 折扣后再 10% 折扣，原价 80，最终价？")
    print("（现实中 80×0.75×0.9=54；但有人会错算成 80×0.65=52）\n")
    demo = [
        "路径1：先打75折=60，再打9折=54。Answer: 54",
        "路径2：总折扣35%，80×0.65=52。最终答案：52",
        "路径3：80*(1-0.25)=60，60*(1-0.10)=54。答案 54",
        "路径4：80-20=60，60-6=54。结果 54",
        "路径5：先减25%再减10%，合并减35%，80*0.65=52。答案是 52",
    ]
    return _print_vote(demo)


def build_parser():
    p = argparse.ArgumentParser(description="Self-Consistency 自洽性引擎（中文输出）。")
    p.add_argument("--vote", action="store_true", help="对路径文件做多数投票与收敛度分析")
    p.add_argument("--file", default=None, help="路径文件：用 ---- 分段，或 JSON 数组")
    p.add_argument("--demo", action="store_true", help="内置演示（5 条路径，3:2 分裂）")
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.demo:
            return cmd_demo()
        if args.vote:
            return cmd_vote_file(args.file)
    except KeyboardInterrupt:
        print("【中断】用户终止。", file=sys.stderr)
        return 130
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
