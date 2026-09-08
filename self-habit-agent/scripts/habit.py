#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
self-habit-agent · 习惯叠加 / streak 引擎 v2.0.0

把新行为「接」在旧锚点上，养成就不丢。本引擎不靠意志力口号，而是把
「习惯叠加（habit stacking）」落成可重跑的数据与算法：定义锚点→新行为→
提示线索，每日打卡，自动算连击、断签、养成进度，并对长期未养成发出警报。

子命令
  define    定义习惯：锚点行为 + 新行为 + 提示线索 → habit-log.jsonl
  checkin   每日打卡（可回溯 --date，可去重）
  streak    连击统计：当前连击 / 最长连击
  lapse     中断检测：断签天数、是否中断
  report    养成进度报告：按习惯显示进度%、最稳 / 最易断习惯

退出码
  0  正常
  1  连击中断或进度停滞（需关注）
  4  长期未养成警报（某习惯连续中断超过阈值，或长期未达目标）

理论锚点（详见 references/）
  - 习惯叠加 habit stacking（James Clear《Atomic Habits》"After X, I will Y"）
  - 习惯回路 线索-渴求-反应-奖赏（Duhigg）
  - 习惯养成天数（Lally et al. 2009，中位 66 天，区间 18–254）
  - 微习惯（Guise）
  - 执行意图 implementation intentions（Gollwitzer）
"""

import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timezone

DEFAULT_STORE = ".self-habit"
EVENT_VERSION = "2.0.0"
DEFAULT_TARGET_DAYS = 66      # Lally et al. 2009 中位养成天数
LAPSE_ALERT_DAYS = 7          # 连续中断超此阈值 → 退出码 4
STALL_DAYS = 3                # 连续未打卡达此值 → 视为进度停滞（退出码 1）


# ----------------------------------------------------------------------------
# 存储与 IO
# ----------------------------------------------------------------------------
def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def log_file(store):
    return os.path.join(store, "habit-log.jsonl")


def ensure_store(store):
    os.makedirs(store, exist_ok=True)


def append_event(store, entry):
    ensure_store(store)
    with open(log_file(store), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


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


def load_habits(store):
    """返回 hid -> 最新定义（按 ts 取后写者），并附 name->hid 索引。"""
    habits = {}
    by_name = {}
    for e in load_events(store):
        if e.get("type") != "define":
            continue
        hid = e.get("hid")
        habits[hid] = e
        by_name[e.get("name", "").lower()] = hid
    return habits, by_name


def load_checkins(store):
    """返回 hid -> set(日期字符串 YYYY-MM-DD)。"""
    out = {}
    for e in load_events(store):
        if e.get("type") != "checkin":
            continue
        out.setdefault(e.get("hid"), set()).add(e.get("date"))
    return out


def parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def resolve_today(today_str):
    if today_str:
        return parse_date(today_str)
    return date.today()


# ----------------------------------------------------------------------------
# 连击 / 中断算法
# ----------------------------------------------------------------------------
def compute_streak(dates, today):
    """dates: 排序后的 date 对象列表。返回 (当前连击, 最长连击)。"""
    if not dates:
        return 0, 0
    longest = 1
    cur = 1
    for i in range(1, len(dates)):
        delta = (dates[i] - dates[i - 1]).days
        if delta == 1:
            cur += 1
        elif delta == 0:
            pass  # 同日重复，忽略
        else:
            cur = 1
        longest = max(longest, cur)
    # 当前连击仅在「最近一次打卡是今天或昨天」时算存活
    last = dates[-1]
    if (today - last).days <= 1:
        cs = 1
        for i in range(len(dates) - 1, 0, -1):
            delta = (dates[i] - dates[i - 1]).days
            if delta == 1:
                cs += 1
            else:
                break
        current = cs
    else:
        current = 0
    return current, longest


def missed_days(dates, today):
    """断签天数 = 自最近一次打卡以来错过的完整天数。无打卡返回 0。"""
    if not dates:
        return 0
    last = max(dates)
    return max(0, (today - last).days - 1)


def habit_metrics(hid, habits, checkins, today):
    h = habits.get(hid, {})
    raw = sorted(parse_date(d) for d in checkins.get(hid, set()))
    cur, lon = compute_streak(raw, today)
    miss = missed_days(raw, today)
    target = int(h.get("target_days") or DEFAULT_TARGET_DAYS)
    has_data = len(raw) > 0
    progress = min(100, round(cur / target * 100)) if target > 0 else 0
    formed = lon >= target and has_data
    return {
        "hid": hid,
        "name": h.get("name", hid),
        "anchor": h.get("anchor", ""),
        "behavior": h.get("behavior", ""),
        "cue": h.get("cue", ""),
        "target_days": target,
        "current": cur,
        "longest": lon,
        "missed": miss,
        "progress": progress,
        "formed": formed,
        "has_data": has_data,
        "broken": has_data and miss >= 1,
        "alert": has_data and miss >= LAPSE_ALERT_DAYS,
        "stalled": has_data and miss >= STALL_DAYS,
    }


# ----------------------------------------------------------------------------
# 子命令：define
# ----------------------------------------------------------------------------
def cmd_define(args):
    store = args.store
    name = (args.name or "").strip()
    if not name:
        print("错误：define 必须提供 --name（习惯名称）", file=sys.stderr)
        return 2
    anchor = (args.anchor or "").strip()
    behavior = (args.behavior or "").strip()
    cue = (args.cue or "").strip() or "（未指定，请补充一个稳定、可见的提示线索）"
    target = args.target_days or DEFAULT_TARGET_DAYS

    habits, by_name = load_habits(store)
    hid = args.id
    if not hid:
        if name.lower() in by_name:
            hid = by_name[name.lower()]          # 同名则更新既有习惯
        else:
            hid = "h%d" % (len(habits) + 1)
    formula = "在「%s」之后，我会「%s」（提示线索：%s）" % (
        anchor or "（锚点行为）", behavior or "（新行为）", cue)

    ev = {
        "ts": now_iso(),
        "type": "define",
        "hid": hid,
        "name": name,
        "anchor": anchor,
        "behavior": behavior,
        "cue": cue,
        "formula": formula,
        "target_days": target,
        "version": EVENT_VERSION,
    }
    append_event(store, ev)
    print("已定义习惯 %s：%s" % (hid, name))
    print("叠加公式：%s" % formula)
    print("养成目标：连续 %d 天（Lally et al. 2009 中位 66 天，区间 18–254，因人而异）" % target)
    return 0


# ----------------------------------------------------------------------------
# 子命令：checkin
# ----------------------------------------------------------------------------
def resolve_hid(args, store):
    hid = (args.id or "").strip()
    if hid:
        return hid
    name = (args.name or "").strip()
    if name:
        _, by_name = load_habits(store)
        return by_name.get(name.lower())
    return None


def cmd_checkin(args):
    store = args.store
    hid = resolve_hid(args, store)
    if not hid:
        print("错误：checkin 需提供 --id 或 --name 指明习惯", file=sys.stderr)
        return 2
    habits, _ = load_habits(store)
    if hid not in habits:
        print("错误：未找到习惯 %s，请先 define" % hid, file=sys.stderr)
        return 2

    d = args.date
    if not d:
        d = resolve_today(args.today).isoformat()
    try:
        chk = parse_date(d)
    except ValueError:
        print("错误：--date 格式应为 YYYY-MM-DD，收到：%s" % d, file=sys.stderr)
        return 2

    checkins = load_checkins(store)
    if d in checkins.get(hid, set()):
        print("习惯 %s 在 %s 已打卡，跳过重复记录" % (hid, d))
        return 0

    append_event(store, {
        "ts": now_iso(),
        "type": "checkin",
        "hid": hid,
        "date": d,
        "version": EVENT_VERSION,
    })
    raw = sorted(parse_date(x) for x in checkins.get(hid, set())) + [chk]
    raw = sorted(set(raw))
    cur, lon = compute_streak(raw, resolve_today(args.today))
    print("已为习惯 %s 记录 %s 打卡" % (hid, d))
    print("当前连击：%d 天　最长连击：%d 天" % (cur, lon))
    return 0


# ----------------------------------------------------------------------------
# 子命令：streak
# ----------------------------------------------------------------------------
def cmd_streak(args):
    store = args.store
    today = resolve_today(args.today)
    habits, _ = load_habits(store)
    checkins = load_checkins(store)
    if not habits:
        print("尚无习惯定义。先用 `define` 定义锚点与新行为。")
        return 0

    show = [args.id] if args.id else list(habits.keys())
    broke_any = False
    lines = ["# 连击统计", ""]
    lines.append("- 计算基准日：%s" % today.isoformat())
    lines.append("")
    for hid in show:
        h = habits.get(hid)
        if not h:
            print("警告：未找到习惯 %s" % hid, file=sys.stderr)
            continue
        raw = sorted(parse_date(d) for d in checkins.get(hid, set()))
        cur, lon = compute_streak(raw, today)
        miss = missed_days(raw, today)
        flag = ""
        if raw and miss >= 1:
            broke_any = True
            flag = "　⚠ 已中断（断签 %d 天）" % miss
        lines.append("- **%s**（%s）：当前 %d 天 / 最长 %d 天%s" % (
            h["name"], hid, cur, lon, flag))

    report = "\n".join(lines) + "\n"
    print(report)
    return 1 if broke_any else 0


# ----------------------------------------------------------------------------
# 子命令：lapse
# ----------------------------------------------------------------------------
def cmd_lapse(args):
    store = args.store
    today = resolve_today(args.today)
    habits, _ = load_habits(store)
    checkins = load_checkins(store)
    if not habits:
        print("尚无习惯定义。先用 `define` 定义。")
        return 0

    show = [args.id] if args.id else list(habits.keys())
    alert_any = False
    broke_any = False
    lines = ["# 中断检测", ""]
    lines.append("- 计算基准日：%s" % today.isoformat())
    lines.append("- 阈值：断签 ≥ %d 天为停滞(1)，≥ %d 天为长期未养成警报(4)" % (STALL_DAYS, LAPSE_ALERT_DAYS))
    lines.append("")
    for hid in show:
        h = habits.get(hid)
        if not h:
            continue
        raw = sorted(parse_date(d) for d in checkins.get(hid, set()))
        miss = missed_days(raw, today)
        if not raw:
            lines.append("- **%s**（%s）：尚未开始打卡" % (h["name"], hid))
            continue
        if miss >= LAPSE_ALERT_DAYS:
            alert_any = True
            lines.append("- **%s**（%s）：⛔ 连续断签 %d 天，触发长期警报(4)" % (h["name"], hid, miss))
        elif miss >= 1:
            broke_any = True
            lines.append("- **%s**（%s）：⚠ 已断签 %d 天（中断）" % (h["name"], hid, miss))
        else:
            lines.append("- **%s**（%s）：✅ 未断签（最近一次 %s）" % (
                h["name"], hid, max(raw).isoformat()))

    report = "\n".join(lines) + "\n"
    print(report)
    if alert_any:
        return 4
    if broke_any:
        return 1
    return 0


# ----------------------------------------------------------------------------
# 子命令：report
# ----------------------------------------------------------------------------
def cmd_report(args):
    store = args.store
    today = resolve_today(args.today)
    habits, _ = load_habits(store)
    checkins = load_checkins(store)
    if not habits:
        print("尚无习惯定义。先用 `define` 定义。")
        return 0

    metrics = [habit_metrics(hid, habits, checkins, today) for hid in habits]

    # 最稳 / 最易断
    started = [m for m in metrics if m["has_data"]]
    if started:
        stable = max(started, key=lambda m: (m["current"], m["longest"]))
        fragile = min(started, key=lambda m: (m["current"], -m["missed"]))
    else:
        stable = fragile = None

    alert_any = any(m["alert"] for m in metrics)
    broke_any = any(m["broken"] for m in metrics)

    lines = []
    lines.append("# 习惯养成进度报告")
    lines.append("")
    lines.append("- 生成时间：%s" % now_iso())
    lines.append("- 计算基准日：%s" % today.isoformat())
    lines.append("- 习惯总数：%d，已开始打卡：%d" % (len(metrics), len(started)))
    lines.append("")
    lines.append("## 一、逐习惯进度")
    for m in metrics:
        status = "已养成 ✅" if m["formed"] else ("中断 ⚠" if m["broken"] else "进行中")
        lines.append("")
        lines.append("### %s（%s）" % (m["name"], m["hid"]))
        lines.append("- 叠加公式：在「%s」之后，我会「%s」" % (m["anchor"], m["behavior"]))
        lines.append("- 提示线索：%s" % m["cue"])
        lines.append("- 当前连击：%d 天　最长连击：%d 天　目标：%d 天" % (
            m["current"], m["longest"], m["target_days"]))
        lines.append("- 养成进度：%d%%（%s）" % (m["progress"], status))
        if m["has_data"]:
            lines.append("- 断签天数：%d" % m["missed"])
    lines.append("")
    lines.append("## 二、最稳 / 最易断")
    if stable and fragile:
        lines.append("- **最稳习惯**：%s（当前连击 %d 天，进度 %d%%）" % (
            stable["name"], stable["current"], stable["progress"]))
        lines.append("- **最易断习惯**：%s（当前连击 %d 天，断签 %d 天，进度 %d%%）" % (
            fragile["name"], fragile["current"], fragile["missed"], fragile["progress"]))
    else:
        lines.append("- 暂无已开始打卡的习惯，无法比较。")
    lines.append("")
    lines.append("## 三、下一步建议")
    for m in metrics:
        if m["alert"]:
            lines.append("- ⛔ %s：连续断签 %d 天，已远超养成窗口，建议用微习惯重启（降到 1 分钟版本），别因「全断」而放弃。" % (
                m["name"], m["missed"]))
        elif m["broken"]:
            lines.append("- ⚠ %s：已断签 %d 天，今天补一次即可接回连击，别等「周一再开始」。" % (m["name"], m["missed"]))
        elif m["formed"]:
            lines.append("- ✅ %s：已达目标连击，进入自动化阶段，继续保持但可降低监控频率。" % m["name"])
        else:
            lines.append("- 🔄 %s：进度 %d%%，保持每日打卡，把提示线索放在锚点行为「之后」的必经之处。" % (
                m["name"], m["progress"]))

    report = "\n".join(lines) + "\n"
    ensure_store(store)
    out_path = os.path.join(store, "habit-report.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print("报告已写入：%s" % out_path)

    if alert_any:
        return 4
    if broke_any:
        return 1
    return 0


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------
def build_parser():
    # 主解析器持有真实默认值；子解析器用 SUPPRESS，避免把 --store/--today
    # 的默认值覆盖掉主解析器已解析出的值（argparse 已知坑：同选项父子都定义会回退默认）。
    main_common = argparse.ArgumentParser(add_help=False)
    main_common.add_argument("--store", default=DEFAULT_STORE, help="数据目录（默认 .self-habit）")
    main_common.add_argument("--today", default=None, help="覆盖『今天』日期(YYYY-MM-DD)，用于回溯/测试")

    sub_common = argparse.ArgumentParser(add_help=False)
    sub_common.add_argument("--store", default=argparse.SUPPRESS, help="数据目录（默认 .self-habit）")
    sub_common.add_argument("--today", default=argparse.SUPPRESS, help="覆盖『今天』日期(YYYY-MM-DD)")

    p = argparse.ArgumentParser(prog="habit", parents=[main_common],
                               description="self-habit-agent 习惯叠加 / streak 引擎")
    sub = p.add_subparsers(dest="cmd", required=True)

    pd = sub.add_parser("define", parents=[sub_common], help="定义习惯（锚点+新行为+线索）")
    pd.add_argument("--id", help="习惯 ID（缺省自动分配；同名则更新）")
    pd.add_argument("--name", required=True, help="习惯名称")
    pd.add_argument("--anchor", help="锚点行为（既有习惯，After X）")
    pd.add_argument("--behavior", help="新行为（I will Y）")
    pd.add_argument("--cue", help="提示线索（稳定、可见）")
    pd.add_argument("--target-days", type=int, default=DEFAULT_TARGET_DAYS, help="养成目标天数（默认 66）")

    pc = sub.add_parser("checkin", parents=[sub_common], help="每日打卡")
    pc.add_argument("--id", help="习惯 ID")
    pc.add_argument("--name", help="习惯名称")
    pc.add_argument("--date", default=None, help="打卡日期 YYYY-MM-DD（默认今天）")

    ps = sub.add_parser("streak", parents=[sub_common], help="连击统计")
    ps.add_argument("--id", default=None, help="仅看某习惯（缺省全部）")

    pl = sub.add_parser("lapse", parents=[sub_common], help="中断检测")
    pl.add_argument("--id", default=None, help="仅看某习惯（缺省全部）")

    pr = sub.add_parser("report", parents=[sub_common], help="养成进度报告")
    return p


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    args = build_parser().parse_args(argv)
    handlers = {
        "define": cmd_define,
        "checkin": cmd_checkin,
        "streak": cmd_streak,
        "lapse": cmd_lapse,
        "report": cmd_report,
    }
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
