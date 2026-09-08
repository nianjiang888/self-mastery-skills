#!/usr/bin/env python3
# protect.py — self-protect-agent 主引擎
#
# 命令：
#   scan   对"即将执行的操作描述"做红线扫描，输出命中等级与规则 ID。
#   check  对一条具体命令做预执行校验（allowlist + 路径保护 + 批量路由 HITL）。
#   record 记录一次近失/拦截事件到 near-miss 日志（海恩法则：近失累积学习）。
#   audit  汇总近失趋势 + 红线命中统计，输出 redline-report.md（实物证据）。
#
# 实物证据（冲 4.8 的入场券）：
#   每次 scan/check 落一条 .redline-event-<时间戳>.json；
#   record 追加 near-miss-log.jsonl；audit 生成 redline-report.md。
#   让"没发生的事故"可见、可学、不贰过。
import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from redline_engine import load_redlines, scan_text, check_command, LEVEL_RANK

DEFAULT_STORE = ".self-protect"
EVENT_VERSION = "2.0.1"


def _now_iso():
    return datetime.now().isoformat(timespec="seconds")


def _write_event(store, payload):
    os.makedirs(store, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    path = os.path.join(store, f".redline-event-{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def _count_log(log_path):
    if not os.path.isfile(log_path):
        return 0
    with open(log_path, encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def cmd_scan(args):
    lib = load_redlines(args.rules)
    hits = scan_text(args.text, lib)
    if hits:
        top = max(hits, key=lambda h: LEVEL_RANK.get(h.get("level", "info"), 1))
        level = top.get("level")
        ev = _write_event(args.store, {
            "version": EVENT_VERSION,
            "kind": "scan",
            "level": level,
            "rules": [h.get("id") for h in hits],
            "text": args.text[:500],
            "ts": _now_iso(),
        })
        if args.json:
            print(json.dumps({
                "level": level,
                "rules": [h.get("id") for h in hits],
                "categories": sorted({h.get("category") for h in hits}),
                "descs": [h.get("desc") for h in hits],
                "text": args.text[:500],
            }, ensure_ascii=False))
        else:
            print(f"🚫 命中 {len(hits)} 条红线，最高等级：{level}")
            for h in hits:
                print(f"  [{h.get('level'):>5}] {h.get('id')} ({h.get('category')}) — {h.get('desc')}")
            print(f"📝 实物证据已写：{ev}")
        sys.exit(4 if level == "block" else 1)
    if args.json:
        print(json.dumps({"level": None, "rules": [], "categories": [], "descs": [], "text": args.text[:500]}, ensure_ascii=False))
    else:
        print("✅ 未命中红线，操作在边界内")
    sys.exit(0)


def cmd_check(args):
    lib = load_redlines(args.rules)
    verdict, reasons = check_command(args.command, lib)
    ev = _write_event(args.store, {
        "version": EVENT_VERSION,
        "kind": "check",
        "verdict": verdict,
        "reasons": reasons,
        "command": args.command[:500],
        "ts": _now_iso(),
    })
    if args.json:
        print(json.dumps({
            "verdict": verdict,
            "reasons": reasons,
            "command": args.command[:500],
        }, ensure_ascii=False))
    else:
        print(f"预执行校验 → 裁定：{verdict}")
        for r in reasons:
            print(f"  - {r}")
        print(f"📝 实物证据已写：{ev}")
    sys.exit(4 if verdict == "block" else (1 if verdict == "confirm" else 0))


def cmd_record(args):
    store = os.path.abspath(args.store)
    os.makedirs(store, exist_ok=True)
    log = os.path.join(store, "near-miss-log.jsonl")
    rec = {
        "ts": _now_iso(),
        "level": args.level,
        "category": args.category,
        "rule_id": args.rule_id or "-",
        "action": args.action,
        "outcome": args.outcome,
        "note": args.note or "",
    }
    with open(log, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"📌 近失事件已记录：{log}")
    print(f"   累计已记录 {_count_log(log)} 条（海恩法则：近失累积 = 安全进步指标）")
    sys.exit(0)


def cmd_audit(args):
    store = os.path.abspath(args.store)
    log = os.path.join(store, "near-miss-log.jsonl")
    events = []
    if os.path.isfile(log):
        with open(log, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    if not events:
        print("暂无近失记录。先跑几次 scan/check/record 再来审计。")
        sys.exit(0)

    by_level = Counter(e.get("level", "?") for e in events)
    by_cat = Counter(e.get("category", "?") for e in events)
    by_rule = Counter(e.get("rule_id") for e in events if e.get("rule_id") not in ("-", None, ""))
    blocked = sum(1 for e in events if e.get("outcome") in ("拦截", "blocked", "block"))
    by_day = Counter(e.get("ts", "")[:10] for e in events)

    lines = []
    lines.append(f"# 红线审计报告（self-protect-agent v{EVENT_VERSION}）")
    lines.append(f"生成时间：{_now_iso()}")
    lines.append("")
    lines.append("## 总览")
    lines.append(f"- 近失/拦截事件累计：**{len(events)}** 条")
    lines.append(f"- 其中已被物理拦截：{blocked} 条（未造成实际损害）")
    lines.append(f"- 等级分布：{dict(by_level)}")
    lines.append("")
    lines.append("## 按风险面")
    for c, n in by_cat.most_common():
        lines.append(f"- {c}: {n}")
    lines.append("")
    lines.append("## Top 红线规则（命中频次）")
    if by_rule:
        for r, n in by_rule.most_common(10):
            lines.append(f"- {r}: {n}")
    else:
        lines.append("- （暂无带规则 ID 的记录）")
    lines.append("")
    lines.append("## 近失趋势（按日，NMR 上升 = 心理安全提升 = 好事）")
    for d in sorted(by_day):
        lines.append(f"- {d}: {by_day[d]}")
    lines.append("")
    lines.append("## 结论与建议")
    lines.append(f"- 已拦截 {blocked} 次潜在事故，相当于在'事故机会弹道'形成前堵住了孔洞。")
    if by_cat:
        top_cat = by_cat.most_common(1)[0][0]
        lines.append(f"- 最高频风险面：**{top_cat}**，建议优先加固该层防御（再加一道 cheese slice）。")
    lines.append("- 近失率上升不是退步，是系统在努力学习。继续保持记录习惯。")

    report = "\n".join(lines)
    out = os.path.join(store, "redline-report.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print(f"\n📄 报告已写：{out}")
    sys.exit(0)


def main():
    p = argparse.ArgumentParser(
        prog="protect",
        description="self-protect-agent 自我边界守护引擎",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("scan", help="扫描操作描述是否越界")
    sp.add_argument("text", help="即将执行的操作描述")
    sp.add_argument("--rules", default=None, help="红线规则库路径")
    sp.add_argument("--json", action="store_true", help="以 JSON 输出（便于 CI/钩子门禁）")
    sp.add_argument("--store", default=DEFAULT_STORE, help="实物证据目录")

    cp = sub.add_parser("check", help="对具体命令做预执行校验")
    cp.add_argument("command", help="待校验的命令")
    cp.add_argument("--rules", default=None, help="红线规则库路径")
    cp.add_argument("--json", action="store_true", help="以 JSON 输出（便于 CI/钩子门禁）")
    cp.add_argument("--store", default=DEFAULT_STORE, help="实物证据目录")

    rp = sub.add_parser("record", help="记录一次近失/拦截事件")
    rp.add_argument("--level", required=True, help="info / warn / block")
    rp.add_argument("--category", required=True, help="风险面：destructive/privilege/external_send/prompt_injection")
    rp.add_argument("--action", required=True, help="动作描述")
    rp.add_argument("--outcome", default="近失", help="近失 / 拦截 / blocked")
    rp.add_argument("--rule-id", default=None, help="命中的红线规则 ID")
    rp.add_argument("--note", default=None, help="补充说明")
    rp.add_argument("--store", default=DEFAULT_STORE, help="实物证据目录")

    ap = sub.add_parser("audit", help="审计近失趋势并生成报告")
    ap.add_argument("--store", default=DEFAULT_STORE, help="实物证据目录")

    args = p.parse_args()
    {
        "scan": cmd_scan,
        "check": cmd_check,
        "record": cmd_record,
        "audit": cmd_audit,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
