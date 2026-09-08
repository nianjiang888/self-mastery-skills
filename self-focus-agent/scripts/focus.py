#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
self-focus-agent · 深度工作/防干扰引擎 v2.0.0

帮用户进入并守住心流：规划专注块、记录实际专注与干扰、量化专注力与打断频次、
看清「什么最常打断我」，并在干扰过多或长期专注严重不足时主动报警。

子命令
  plan       规划一个专注块（主题 / 计划时长），落到 focus-log.jsonl
  log        记录一次专注块实际（实际时长 / 被打断次数 / 干扰来源）
  interrupt  记录单次干扰（来源：微信 / 同事 / 自己刷手机 …）
  measure    计算实际专注时长与打断频次，干扰过多或时长不足退出 1
  report     专注趋势 + 干扰 Top 来源，长期严重不足退出 4

退出码
  0  正常
  1  干扰过多或专注时长不足（单块/本期需关注）
  4  长期专注严重不足警报（窗口内日均专注远低于基线）

实物证据（4.8 基准：留可重跑文件）
  focus-log.jsonl：每次 plan/log/interrupt 一行纯数据，可任意时刻重跑分析。
  focus-measure.md / focus-report.md：各命令生成的产物，均为可复核的 markdown。
仅用标准库，中文报错，确定性、可重跑。
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

DEFAULT_STORE = ".self-focus"
EVENT_VERSION = "2.0.0"

# ----------------------------------------------------------------------------
# 基线阈值（与 resources/focus-baselines.json 保持一致；缺失时回退默认值）
# ----------------------------------------------------------------------------
DEFAULT_BASELINES = {
    "version": EVENT_VERSION,
    "interrupt_warn": 3,            # 单块打断次数 ≥ 此值 → 退出 1
    "focus_deficit_ratio": 0.5,     # 实际时长 < 计划时长 × 此比例 → 时长不足
    "longterm_window_days": 7,      # 长期警报统计窗口（天）
    "longterm_min_active_days": 3,  # 窗口内至少这么多个有专注的天才判警报
    "longterm_alert_minutes": 90,   # 窗口内「日均专注分钟」低于此 → 退出 4
    "sources": {
        "微信": ["微信", "wechat", "wx", "聊天"],
        "同事": ["同事", "colleague", "找我", "老板", "上级"],
        "自己刷手机": ["刷手机", "刷视频", "玩手机", "短视频", "刷抖音", "逛网页"],
        "电话": ["电话", "phone", "来电", "通话"],
        "邮件": ["邮件", "email", "mail", "收件箱"],
        "会议": ["会议", "开会", "meeting", "碰头"],
        "环境噪音": ["噪音", "吵", "noise", "装修", "施工"],
        "自己走神": ["走神", "发呆", "分心", "走思", "胡思乱想"],
        "其他": ["其他", "其它", "other", "杂事"],
    },
}


# ----------------------------------------------------------------------------
# 存储与 IO
# ----------------------------------------------------------------------------
def script_dir():
    return os.path.dirname(os.path.abspath(__file__))


def default_baselines_path():
    return os.path.join(script_dir(), "..", "resources", "focus-baselines.json")


def load_baselines(path):
    """加载基线；失败回退默认，保证引擎永不出错崩溃。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = dict(DEFAULT_BASELINES)
        merged.update(data)
        merged.setdefault("sources", DEFAULT_BASELINES["sources"])
        return merged
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULT_BASELINES)


def log_file(store):
    return os.path.join(store, "focus-log.jsonl")


def ensure_store(store):
    os.makedirs(store, exist_ok=True)


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_entries(store):
    path = log_file(store)
    entries = []
    if not os.path.exists(path):
        return entries
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def append_entry(store, entry):
    ensure_store(store)
    with open(log_file(store), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def next_id(store, kind):
    """按种类自增编号（p/b/i + 序号），同一 store 内稳定。"""
    entries = load_entries(store)
    seq = sum(1 for e in entries if e.get("kind") == kind) + 1
    prefix = {"plan": "p", "block": "b", "interrupt": "i"}.get(kind, "x")
    return "%s%d" % (prefix, seq)


def normalize_source(text, sources_map):
    """把任意干扰来源文本归一到词典中的规范来源。"""
    if not text:
        return "其他"
    t = text.strip().lower()
    for canon, kws in sources_map.items():
        for kw in kws:
            if kw.lower() in t:
                return canon
    return "其他"


def to_day(ts):
    return ts[:10]


# ----------------------------------------------------------------------------
# 子命令：plan（规划专注块）
# ----------------------------------------------------------------------------
def cmd_plan(args, bl):
    theme = (args.theme or "").strip()
    if not theme:
        print("错误：--theme（专注主题）不能为空", file=sys.stderr)
        return 2
    if args.planned_minutes <= 0:
        print("错误：--planned-minutes（计划时长，分钟）必须为正数", file=sys.stderr)
        return 2
    entry = {
        "kind": "plan",
        "ts": now_iso(),
        "id": next_id(args.store, "plan"),
        "theme": theme,
        "planned_minutes": args.planned_minutes,
        "version": EVENT_VERSION,
    }
    append_entry(args.store, entry)
    print("已规划专注块 %s：主题「%s」，计划 %d 分钟" % (entry["id"], theme, args.planned_minutes))
    print("提示：用 `log --plan-id %s ...` 在结束后回填实际专注。" % entry["id"])
    return 0


# ----------------------------------------------------------------------------
# 子命令：log（记录一次专注块实际）
# ----------------------------------------------------------------------------
def cmd_log(args, bl):
    if args.actual_minutes <= 0:
        print("错误：--actual-minutes（实际专注分钟）必须为正数", file=sys.stderr)
        return 2
    sources = [normalize_source(s, bl["sources"]) for s in (args.sources or [])]
    # 去重保序
    seen = set()
    sources = [s for s in sources if not (s in seen or seen.add(s))]
    entry = {
        "kind": "block",
        "ts": now_iso(),
        "id": next_id(args.store, "block"),
        "plan_id": (args.plan_id or "").strip() or None,
        "theme": (args.theme or "").strip(),
        "actual_minutes": args.actual_minutes,
        "interruptions": args.interruptions,
        "sources": sources,
        "version": EVENT_VERSION,
    }
    append_entry(args.store, entry)
    print("已记录专注块 %s：实际 %d 分钟，打断 %d 次，来源=%s" % (
        entry["id"], args.actual_minutes, args.interruptions,
        "、".join(sources) or "（无）"))
    return 0


# ----------------------------------------------------------------------------
# 子命令：interrupt（记录单次干扰）
# ----------------------------------------------------------------------------
def cmd_interrupt(args, bl):
    source = normalize_source(args.source, bl["sources"])
    entry = {
        "kind": "interrupt",
        "ts": now_iso(),
        "id": next_id(args.store, "interrupt"),
        "block_id": (args.block_id or "").strip() or None,
        "source": source,
        "note": (args.note or "").strip(),
        "version": EVENT_VERSION,
    }
    append_entry(args.store, entry)
    print("已记录单次干扰 %s：来源「%s」" % (entry["id"], source))
    if not args.block_id:
        print("提示：未指定 --block-id，该干扰将计入全局来源统计但不归属具体专注块。")
    return 0


# ----------------------------------------------------------------------------
# 数据聚合：把 block 与关联 interrupt 合并成「带完整打断数」的块视图
# ----------------------------------------------------------------------------
def build_block_views(entries):
    """返回 list of dict：每个 block 合并其关联 interrupt 的打断数与来源。"""
    interrupts = [e for e in entries if e.get("kind") == "interrupt"]
    views = []
    for b in entries:
        if b.get("kind") != "block":
            continue
        linked = [i for i in interrupts if i.get("block_id") == b.get("id")]
        extra_interrupts = len(linked)
        extra_sources = [i.get("source", "其他") for i in linked]
        all_sources = list(b.get("sources", [])) + extra_sources
        seen = set()
        all_sources = [s for s in all_sources if not (s in seen or seen.add(s))]
        views.append({
            "id": b.get("id"),
            "plan_id": b.get("plan_id"),
            "theme": b.get("theme", ""),
            "ts": b.get("ts", ""),
            "actual_minutes": b.get("actual_minutes", 0),
            "explicit_interruptions": b.get("interruptions", 0),
            "linked_interruptions": extra_interrupts,
            "total_interruptions": b.get("interruptions", 0) + extra_interrupts,
            "sources": all_sources,
        })
    return views


def gather_source_tally(views, interrupts_all, scope_block_ids=None):
    """统计来源频次；scope_block_ids 给定时只统计归属该范围的干扰。"""
    tally = Counter()
    for v in views:
        if scope_block_ids is not None and v["id"] not in scope_block_ids:
            continue
        for s in v["sources"]:
            tally[s] += 1
    for i in interrupts_all:
        bid = i.get("block_id")
        if scope_block_ids is not None:
            if bid not in scope_block_ids:
                continue
        else:
            if bid:  # 已归属的由 view 统计；未归属的全局也计
                continue
        tally[i.get("source", "其他")] += 1
    return tally


# ----------------------------------------------------------------------------
# 子命令：measure（计算实际专注时长与打断频次）
# ----------------------------------------------------------------------------
def cmd_measure(args, bl):
    entries = load_entries(args.store)
    if not entries:
        print("尚无专注记录，先用 `plan` / `log` / `interrupt` 累积数据。")
        return 0

    views = build_block_views(entries)
    interrupts_all = [e for e in entries if e.get("kind") == "interrupt"]

    if args.block_id:
        scope = [v for v in views if v["id"] == args.block_id]
        if not scope:
            print("错误：未找到专注块 %s" % args.block_id, file=sys.stderr)
            return 2
    else:
        scope = views

    total_actual = sum(v["actual_minutes"] for v in scope)
    total_interrupt = sum(v["total_interruptions"] for v in scope)
    n_blocks = len(scope)
    tally = gather_source_tally(views, interrupts_all,
                                scope_block_ids={v["id"] for v in scope})

    # 时长不足判定：关联了 plan 且实际 < 计划 × 比例
    plan_map = {e.get("id"): e for e in entries if e.get("kind") == "plan"}
    deficit_blocks = []
    for v in scope:
        if v["plan_id"] and v["plan_id"] in plan_map:
            planned = plan_map[v["plan_id"]].get("planned_minutes", 0)
            if planned > 0 and v["actual_minutes"] < planned * bl["focus_deficit_ratio"]:
                deficit_blocks.append((v["id"], v["actual_minutes"], planned))

    # 干扰过多判定
    over_interrupt = [v for v in scope if v["total_interruptions"] >= bl["interrupt_warn"]]

    lines = []
    lines.append("# 专注度量报告")
    lines.append("")
    lines.append("- 生成时间：%s" % now_iso())
    lines.append("- 统计范围：%s" % ("专注块 %s" % args.block_id if args.block_id else "全部 %d 个专注块" % n_blocks))
    lines.append("")
    lines.append("## 一、核心指标")
    lines.append("- 实际专注总时长：**%d 分钟**（约 %.1f 小时）" % (total_actual, total_actual / 60.0))
    lines.append("- 专注块数：%d" % n_blocks)
    lines.append("- 打断总次数：**%d 次**" % total_interrupt)
    if n_blocks:
        lines.append("- 单块平均打断：%.2f 次" % (total_interrupt / n_blocks))
    lines.append("")
    lines.append("## 二、干扰来源分布")
    if tally:
        for s, c in tally.most_common():
            lines.append("- %s：%d 次" % (s, c))
    else:
        lines.append("- 暂无干扰来源记录。")
    lines.append("")
    lines.append("## 三、预警")
    if over_interrupt:
        lines.append("- 干扰过多：%s 打断次数 ≥ %d（阈值），建议排查这些块的干扰源。" % (
            "、".join(v["id"] for v in over_interrupt), bl["interrupt_warn"]))
    if deficit_blocks:
        lines.append("- 时长不足：%s 实际专注低于计划的 %.0f%%。" % (
            "、".join(b[0] for b in deficit_blocks), bl["focus_deficit_ratio"] * 100))
    if not over_interrupt and not deficit_blocks:
        lines.append("- 未触发干扰过多或时长不足预警。")

    report = "\n".join(lines) + "\n"
    ensure_store(args.store)
    out_path = os.path.join(args.store, "focus-measure.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print("报告已写入：%s" % out_path)

    if over_interrupt or deficit_blocks:
        return 1
    return 0


# ----------------------------------------------------------------------------
# 子命令：report（专注趋势 + 干扰 Top 来源）
# ----------------------------------------------------------------------------
def cmd_report(args, bl):
    entries = load_entries(args.store)
    if not entries:
        print("尚无专注记录，先用 `plan` / `log` / `interrupt` 累积数据。")
        return 0

    views = build_block_views(entries)
    interrupts_all = [e for e in entries if e.get("kind") == "interrupt"]

    # 按天聚合
    day_actual = defaultdict(int)
    day_blocks = defaultdict(int)
    day_interrupt = defaultdict(int)
    day_sources = defaultdict(Counter)
    for v in views:
        d = to_day(v["ts"])
        day_actual[d] += v["actual_minutes"]
        day_blocks[d] += 1
        day_interrupt[d] += v["total_interruptions"]
        for s in v["sources"]:
            day_sources[d][s] += 1
    for i in interrupts_all:
        if i.get("block_id"):
            continue
        d = to_day(i.get("ts", ""))
        day_interrupt[d] += 1
        day_sources[d][i.get("source", "其他")] += 1

    days = sorted(day_actual.keys())
    total_actual = sum(day_actual.values())
    total_interrupt = sum(day_interrupt.values())
    total_blocks = sum(day_blocks.values())

    # 全局来源 Top
    global_tally = Counter()
    for c in day_sources.values():
        global_tally.update(c)

    # 长期窗口警报
    if days:
        last_day = datetime.fromisoformat(days[-1])
        window_start = last_day - timedelta(days=bl["longterm_window_days"] - 1)
        win_days = [d for d in days if datetime.fromisoformat(d) >= window_start]
        win_active = [d for d in win_days if day_blocks[d] >= 1]
        win_actual = sum(day_actual[d] for d in win_days)
        win_blocks = sum(day_blocks[d] for d in win_days)
        win_interrupt = sum(day_interrupt[d] for d in win_days)
    else:
        win_active, win_actual, win_blocks, win_interrupt = [], 0, 0, 0

    alert4 = (len(win_active) >= bl["longterm_min_active_days"]
              and win_actual / max(len(win_active), 1) < bl["longterm_alert_minutes"])
    avg_interrupt_win = (win_interrupt / win_blocks) if win_blocks else 0
    warn1 = (win_blocks >= 2 and avg_interrupt_win >= bl["interrupt_warn"])

    lines = []
    lines.append("# 专注趋势报告")
    lines.append("")
    lines.append("- 生成时间：%s" % now_iso())
    lines.append("- 数据跨度：%s ~ %s，共 %d 个专注块" % (days[0], days[-1], total_blocks))
    lines.append("")
    lines.append("## 一、每日趋势")
    lines.append("| 日期 | 专注(分) | 块数 | 打断 |")
    lines.append("|---|---|---|---|")
    for d in days:
        lines.append("| %s | %d | %d | %d |" % (d, day_actual[d], day_blocks[d], day_interrupt[d]))
    lines.append("")
    lines.append("## 二、干扰来源 Top（看清什么最常打断我）")
    if global_tally:
        for s, c in global_tally.most_common(8):
            lines.append("- **%s**：%d 次" % (s, c))
    else:
        lines.append("- 暂无干扰来源记录。")
    lines.append("")
    lines.append("## 三、长期专注评估（窗口 %d 天）" % bl["longterm_window_days"])
    if win_active:
        avg_focus = win_actual / len(win_active)
        lines.append("- 窗口内有专注的天数：%d 天" % len(win_active))
        lines.append("- 窗口日均专注：**%.1f 分钟**" % avg_focus)
        lines.append("- 窗口打断/块均值：%.2f 次" % avg_interrupt_win)
    else:
        lines.append("- 窗口内无专注记录。")
    lines.append("")
    lines.append("## 四、结论与建议")
    if alert4:
        lines.append("- 🔴 **长期警报（退出码 4）**：窗口内日均专注 %.1f 分钟，远低于基线 %d 分钟。" % (
            win_actual / max(len(win_active), 1), bl["longterm_alert_minutes"]))
        lines.append("  建议：把深度工作排进日历固定时段、降低计划时长降低启动门槛、用 `interrupt` 找出高频打断源并物理隔离。")
    elif warn1:
        lines.append("- 🟡 **本窗口干扰偏多（退出码 1）**：打断/块均值 %.2f 次 ≥ 阈值 %d。" % (
            avg_interrupt_win, bl["interrupt_warn"]))
        lines.append("  建议：聚焦 Top 来源，做针对性防干扰（如微信免打扰、戴耳机、关通知）。")
    else:
        lines.append("- 🟢 专注状态稳定，继续保持记录。")
    lines.append("- 通用建议：每周看一次本报告，把「干扰来源 Top」当成待办去逐个消除。")

    report = "\n".join(lines) + "\n"
    ensure_store(args.store)
    out_path = os.path.join(args.store, "focus-report.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print("报告已写入：%s" % out_path)

    if alert4:
        return 4
    if warn1:
        return 1
    return 0


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------
def build_parser():
    p = argparse.ArgumentParser(prog="focus", description="self-focus-agent 深度工作/防干扰引擎")
    p.add_argument("--store", default=DEFAULT_STORE, help="数据目录（默认 .self-focus）")
    p.add_argument("--baselines", default=default_baselines_path(),
                   help="基线阈值与干扰来源词典路径")
    sub = p.add_subparsers(dest="cmd")

    pp = sub.add_parser("plan", help="规划一个专注块")
    pp.add_argument("--theme", required=True, help="专注主题")
    pp.add_argument("--planned-minutes", type=int, required=True, help="计划时长（分钟）")

    pl = sub.add_parser("log", help="记录一次专注块实际")
    pl.add_argument("--actual-minutes", type=int, required=True, help="实际专注分钟")
    pl.add_argument("--interruptions", type=int, default=0, help="被打断次数（默认0）")
    pl.add_argument("--sources", nargs="*", default=[], help="干扰来源（可多个）")
    pl.add_argument("--theme", help="专注主题（可选，便于回溯）")
    pl.add_argument("--plan-id", help="关联的 plan id（可选）")

    pi = sub.add_parser("interrupt", help="记录单次干扰")
    pi.add_argument("--source", required=True, help="干扰来源（微信/同事/自己刷手机…）")
    pi.add_argument("--block-id", help="归属的专注块 id（可选）")
    pi.add_argument("--note", help="补充说明")

    pm = sub.add_parser("measure", help="计算专注时长与打断频次")
    pm.add_argument("--block-id", help="只统计该专注块（默认全部）")

    pr = sub.add_parser("report", help="专注趋势 + 干扰 Top 来源")
    return p


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.cmd:
        parser.print_help()
        return 0
    bl = load_baselines(args.baselines)
    handlers = {
        "plan": lambda a: cmd_plan(a, bl),
        "log": lambda a: cmd_log(a, bl),
        "interrupt": lambda a: cmd_interrupt(a, bl),
        "measure": lambda a: cmd_measure(a, bl),
        "report": lambda a: cmd_report(a, bl),
    }
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
