#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
self-discipline-agent · 自律承诺装置引擎 v2.0.0

把"做/不做某事"从靠意志硬扛，变成可核查的机制：
登记承诺 -> 到期前打卡履约 -> 自动检测违约 -> 问责报告暴露最易破的承诺类型。

子命令
  commit   登记一条承诺（内容/期限/后果或押金/监督人/类别）
  checkin  履约打卡（按承诺 id，记录时间戳）
  streak   连续履约统计
  audit    违约检测：期限已过且无打卡 = 违约；输出问责报告
  report   周期问责报告（履约率/违约模式/最易破类型）

退出码
  0  正常
  1  发现反复违约模式（同类承诺多次违约）
  4  系统性失守警报（某类承诺 100% 违约或总履约率极低）
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

DEFAULT_STORE = ".self-discipline"
EVENT_VERSION = "2.0.0"

CATEGORY_HINTS = {
    "健康": ["运动", "健身", "跑步", "睡眠", "作息", "早睡", "饮食", "戒烟", "戒酒"],
    "工作": ["报告", "任务", "项目", "学习", "读书", "复习", "加班", " deadline", "提交"],
    "财务": ["储蓄", "存款", "记账", "消费", "剁手", "冲动消费", "预算"],
    "情绪": ["发火", "情绪", "耐心", "冲动", "争吵", "冷静"],
    "习惯": ["习惯", "打卡", "每日", "坚持", "早起", "冥想"],
}


# ----------------------------------------------------------------------------
# 存储
# ----------------------------------------------------------------------------
def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def log_file(store):
    return os.path.join(store, "discipline-log.jsonl")


def ensure_store(store):
    os.makedirs(store, exist_ok=True)


def append_event(store, event):
    ensure_store(store)
    event.setdefault("version", EVENT_VERSION)
    with open(log_file(store), "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def load_events(store):
    path = log_file(store)
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def guess_category(text, explicit=None):
    if explicit:
        return explicit
    for cat, hints in CATEGORY_HINTS.items():
        if any(h in text for h in hints):
            return cat
    return "未分类"


def parse_deadline(s):
    """接受 YYYY-MM-DD 或 ISO；返回 date 对象。"""
    s = (s or "").strip()
    if not s:
        return None
    try:
        if len(s) == 10 and s[4] == "-":
            return datetime.strptime(s, "%Y-%m-%d").date()
        return datetime.fromisoformat(s).date()
    except ValueError:
        return None


# ----------------------------------------------------------------------------
# 子命令
# ----------------------------------------------------------------------------
def cmd_commit(args):
    events = load_events(args.store)
    cid = "c%d" % (sum(1 for e in events if e.get("type") == "commit") + 1)
    content = (args.content or "").strip()
    if not content:
        print("错误：--content 不能为空", file=sys.stderr)
        return 2
    deadline = parse_deadline(args.deadline)
    if args.deadline and deadline is None:
        print("错误：--deadline 格式应为 YYYY-MM-DD", file=sys.stderr)
        return 2
    cat = guess_category(content, args.category)
    append_event(args.store, {
        "type": "commit",
        "id": cid,
        "ts": now_iso(),
        "content": content,
        "deadline": args.deadline or "",
        "stake": (args.stake or "").strip(),
        "partner": (args.partner or "").strip(),
        "category": cat,
    })
    print("已登记承诺 %s（类别：%s，期限：%s）" % (cid, cat, args.deadline or "无"))
    if args.stake:
        print("  后果/押金：%s" % args.stake)
    if args.partner:
        print("  监督人：%s" % args.partner)
    return 0


def cmd_checkin(args):
    events = load_events(args.store)
    if not args.id:
        print("错误：checkin 需要 --id", file=sys.stderr)
        return 2
    commits = [e for e in events if e.get("type") == "commit" and e.get("id") == args.id]
    if not commits:
        print("错误：找不到承诺 %s" % args.id, file=sys.stderr)
        return 2
    append_event(args.store, {"type": "checkin", "id": args.id, "ts": now_iso()})
    print("承诺 %s 已打卡履约 ✅" % args.id)
    return 0


def compute_status(events):
    """返回 {cid: {commit_event, checkins:[ts], status, breached_at}}。"""
    commits = [e for e in events if e.get("type") == "commit"]
    checkins = defaultdict(list)
    for e in events:
        if e.get("type") == "checkin":
            checkins[e["id"]].append(e["ts"])
    result = {}
    now = datetime.now(timezone.utc).astimezone()
    for c in commits:
        cid = c["id"]
        dl = parse_deadline(c.get("deadline"))
        cks = checkins.get(cid, [])
        if cks:
            # 在期限前（或无限期）打卡即履约
            if dl is None:
                status = "kept"
            else:
                kept_before = any(
                    datetime.fromisoformat(ts) <= datetime.combine(dl, datetime.max.time().replace(tzinfo=now.tzinfo))
                    for ts in cks
                )
                status = "kept" if kept_before else "breached"
        else:
            if dl is None:
                status = "open"  # 无期限且未打卡：仍开放
            elif datetime.combine(dl, datetime.min.time().replace(tzinfo=now.tzinfo)) < now:
                status = "breached"
            else:
                status = "open"
        result[cid] = {"commit": c, "checkins": cks, "status": status}
    return result


def cmd_streak(args):
    events = load_events(args.store)
    status = compute_status(events)
    # 按承诺创建时间排序，统计连续履约
    ordered = sorted(status.values(), key=lambda x: x["commit"]["ts"])
    cur = 0
    best = 0
    last_kept = False
    for item in ordered:
        if item["status"] == "kept":
            cur += 1
            last_kept = True
            best = max(best, cur)
        else:
            cur = 0
            last_kept = False
    print("当前连续履约：%d · 最长连击：%d" % (cur, best))
    return 0


def cmd_audit(args):
    events = load_events(args.store)
    status = compute_status(events)
    if not status:
        print("尚无承诺记录。先用 `commit` 登记。")
        return 0
    breached = [v for v in status.values() if v["status"] == "breached"]
    kept = [v for v in status.values() if v["status"] == "kept"]
    open_c = [v for v in status.values() if v["status"] == "open"]

    # 违约按类别聚合
    by_cat = Counter(v["commit"].get("category", "未分类") for v in breached)

    lines = []
    lines.append("# 问责报告（audit）")
    lines.append("")
    lines.append("- 生成时间：%s" % now_iso())
    lines.append("- 承诺总数：%d（履约 %d / 违约 %d / 待定 %d）" % (
        len(status), len(kept), len(breached), len(open_c)))
    lines.append("")
    lines.append("## 违约清单")
    if breached:
        for v in breached:
            c = v["commit"]
            lines.append("- **%s** [%s]：%s（期限 %s）" % (c["id"], c.get("category"), c["content"], c.get("deadline") or "无"))
    else:
        lines.append("- 无违约，保持得不错。")
    lines.append("")
    lines.append("## 最易破的承诺类型")
    if by_cat:
        for cat, n in by_cat.most_common():
            lines.append("- %s：%d 次违约" % (cat, n))
    else:
        lines.append("- 暂无违约，无法归类。")
    lines.append("")
    lines.append("> 反复违约同一类，说明靠意志硬扛该类承诺无效，")
    lines.append("> 应改用更强的承诺装置（押金/监督人/if-then 预案），而非『下次注意』。")

    report = "\n".join(lines) + "\n"
    ensure_store(args.store)
    path = os.path.join(args.store, "audit-report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print("报告已写入：%s" % path)

    # 退出码
    if not breached:
        return 0
    # 系统性失守：某类别 ≥2 条且全部违约，或总履约率 < 30%
    total_closed = len(kept) + len(breached)
    rate = (len(kept) / total_closed) if total_closed else 1.0
    cat_breach = Counter()
    cat_total = Counter()
    for v in status.values():
        cat = v["commit"].get("category", "未分类")
        cat_total[cat] += 1
        if v["status"] == "breached":
            cat_breach[cat] += 1
    any_full_breach = any(cat_total[c] >= 2 and cat_breach[c] == cat_total[c] for c in cat_total)
    if rate < 0.3 or any_full_breach:
        return 4
    return 1


def cmd_report(args):
    events = load_events(args.store)
    status = compute_status(events)
    if not status:
        print("尚无承诺记录。")
        return 0
    kept = [v for v in status.values() if v["status"] == "kept"]
    breached = [v for v in status.values() if v["status"] == "breached"]
    total_closed = len(kept) + len(breached)
    rate = (len(kept) / total_closed * 100) if total_closed else 0
    by_cat = defaultdict(lambda: [0, 0])  # cat -> [kept, breached]
    for v in status.values():
        cat = v["commit"].get("category", "未分类")
        if v["status"] == "kept":
            by_cat[cat][0] += 1
        elif v["status"] == "breached":
            by_cat[cat][1] += 1

    lines = []
    lines.append("# 自律周期报告")
    lines.append("")
    lines.append("- 生成时间：%s" % now_iso())
    lines.append("- 履约率：**%.0f%%**（%d 履约 / %d 违约）" % (rate, len(kept), len(breached)))
    lines.append("")
    lines.append("## 各类别表现（履约/违约）")
    for cat, (k, b) in sorted(by_cat.items(), key=lambda x: -(x[1][1])):
        lines.append("- %s：%d / %d" % (cat, k, b))
    lines.append("")
    lines.append("## 下一步")
    lines.append("- 对高违约类别，登记时务必加 `--stake`（押金/后果）与 `--partner`（监督人）。")
    lines.append("- 用 `report` 每周回顾，让履约率单调不降。")
    report = "\n".join(lines) + "\n"
    ensure_store(args.store)
    path = os.path.join(args.store, "discipline-report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print("报告已写入：%s" % path)
    return 0


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------
def build_parser():
    p = argparse.ArgumentParser(prog="discipline", description="self-discipline-agent 承诺装置引擎")
    p.add_argument("--store", default=DEFAULT_STORE)
    sub = p.add_subparsers(dest="cmd")

    pc = sub.add_parser("commit", help="登记承诺")
    pc.add_argument("--content", required=True, help="承诺内容")
    pc.add_argument("--deadline", help="期限 YYYY-MM-DD（留空=无期限）")
    pc.add_argument("--stake", help="违约后果/押金")
    pc.add_argument("--partner", help="监督人")
    pc.add_argument("--category", help="类别（留空自动识别）")

    pi = sub.add_parser("checkin", help="履约打卡")
    pi.add_argument("--id", required=True, help="承诺 id")

    sub.add_parser("streak", help="连续履约统计")
    sub.add_parser("audit", help="违约检测与问责报告")
    sub.add_parser("report", help="周期问责报告")
    return p


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.cmd:
        parser.print_help()
        return 0
    handlers = {
        "commit": cmd_commit,
        "checkin": cmd_checkin,
        "streak": cmd_streak,
        "audit": cmd_audit,
        "report": cmd_report,
    }
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
