#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""self-sleep-agent 真引擎：睡眠质量趋势 + 生理节律学习。

把"想睡好"变成可复核的爬坡记录：
  - log      记录一晚睡眠（就寝/入睡/起床/夜醒/主观质量/咖啡因/屏幕/运动/次日情绪）
  - trend    计算近期睡眠质量趋势、睡眠债、规律性
  - rhythm   从大量记录里学出你的睡眠中点与时型（早鸟/中间/夜猫），并估社会时差
  - nudge    依据近期模式给出可执行的生活化建议（非空话）
  - report   输出完整掌握度报告：趋势 + 节律 + 弱项预警
  - plan     给出这一周最值得做的一个改变

设计原则：
  - 纯标准库，确定性逻辑、可重跑、留实物证据（events.jsonl + profile.json + reports/*.md）
  - 退出码：0 正常 / 1 需关注（存在未达标的弱项）/ 4 系统性警报（参数或数据错误）
  - 所有计算从 events.jsonl 实时重算，保证重跑一致
  - 学术根基见 references/ 与 resources/，引擎只做确定性聚合，不臆造结论

注：本引擎是自我观察与节律学习的工具，不是医疗诊断，不替代医生。
"""
import argparse
import json
import math
import os
import statistics
import sys
from datetime import datetime, date

ENGINE_VERSION = "2.0.0"
DEFAULT_TARGET_MIN = 450          # 默认目标睡眠时长 7.5 小时
WEAK_EFFICIENCY = 85.0           # 睡眠效率低于此判弱项（%）
WEAK_LATENCY_MIN = 30            # 入睡潜伏期高于此判弱项（分钟）
WEAK_REGULARITY = 70.0           # 规律性低于此判弱项（0-100）
WEAK_DEBT_MIN = 30               # 日均睡眠债高于此判弱项（分钟）
CAFFEINE_CUTOFF_H = 6            # 咖啡因半衰期约5-6h，睡前>6h仍可能干扰
SCREEN_WEAK_MIN = 60             # 睡前屏幕>60min判弱项


def die(msg, code=4):
    sys.stderr.write("错误：" + msg + "\n")
    sys.exit(code)


def now_iso():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def today_str():
    return date.today().strftime("%Y-%m-%d")


def ensure_dirs(data):
    for sub in ("reports",):
        os.makedirs(os.path.join(data, sub), exist_ok=True)


def events_path(data):
    return os.path.join(data, "events.jsonl")


def profile_path(data):
    return os.path.join(data, "profile.json")


def append_event(data, ev):
    ensure_dirs(data)
    ev["ts"] = now_iso()
    p = events_path(data)
    # 同一 type+date 视为同一条记录：重记同晚会幂等覆盖，而非重复追加污染趋势
    if ev.get("type") and ev.get("date"):
        existing = []
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if rec.get("type") == ev["type"] and rec.get("date") == ev["date"]:
                        continue  # 跳过同日期旧记录
                    existing.append(line)
        with open(p, "w", encoding="utf-8") as f:
            for l in existing:
                f.write(l + "\n")
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    else:
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")


def load_events(data):
    p = events_path(data)
    if not os.path.exists(p):
        return []
    out = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    die("事件日志损坏，无法解析：" + p, 4)
    # 只取睡眠记录，按日期排序
    recs = [e for e in out if e.get("type") == "sleep"]
    recs.sort(key=lambda r: r.get("date", ""))
    return recs


def load_profile(data):
    p = profile_path(data)
    if not os.path.exists(p):
        return {"target_min": DEFAULT_TARGET_MIN}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_profile(data, obj):
    ensure_dirs(data)
    with open(profile_path(data), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


# ---------- 时间工具 ----------
def to_min(hhmm):
    """'HH:MM' -> 距零点分钟数；非法则报错。"""
    if not isinstance(hhmm, str) or ":" not in hhmm:
        die("时间格式应为 HH:MM，例如 23:30", 4)
    h, m = hhmm.split(":", 1)
    if not (h.isdigit() and m.isdigit()):
        die("时间包含非法字符：" + hhmm, 4)
    h, m = int(h), int(m)
    if h > 23 or m > 59:
        die("时间超出范围：" + hhmm, 4)
    return h * 60 + m


def norm_cross(start, end):
    """处理跨零点：若 end < start，视作次日，+1440。"""
    if end < start:
        return end + 1440
    return end


# ---------- 派生指标 ----------
def derive(rec):
    """从一条记录算出派生指标，写回 rec。"""
    bed = to_min(rec["bedtime"])
    onset = to_min(rec["onset"]) if rec.get("onset") else bed + (rec.get("latency") or 0)
    wake = to_min(rec["wake"])
    rise = to_min(rec["rise"]) if rec.get("rise") else wake
    onset = norm_cross(bed, onset)
    wake = norm_cross(onset, wake)
    rise = norm_cross(wake, rise) if rec.get("rise") else wake
    latency = onset - bed
    tib = rise - bed                       # 卧床时长 time in bed
    waso = rec.get("waso") or (rec.get("wakings", 0) * 15)  # 觉醒时长
    total = max(wake - onset - waso, 0)    # 总睡眠时长
    eff = round(total / tib * 100, 1) if tib > 0 else 0.0
    midpoint = (onset + (wake - waso)) / 2.0 if (wake - waso) >= onset else onset + total / 2.0
    midpoint = midpoint % 1440.0
    rec["_bed_min"] = bed
    rec["_onset_min"] = onset
    rec["_wake_min"] = wake
    rec["_rise_min"] = rise
    rec["_latency"] = latency
    rec["_tib"] = tib
    rec["_waso"] = waso
    rec["_total"] = total
    rec["_eff"] = eff
    rec["_mid"] = midpoint
    return rec


def fmt_min(m):
    """分钟数 -> 'Xh Ym'。"""
    m = int(round(m))
    return "%dh %dm" % (m // 60, m % 60)


def fmt_clock(m):
    m = int(round(m)) % 1440
    return "%02d:%02d" % (m // 60, m % 60)


# ---------- 聚合计算 ----------
def recent(recs, days):
    if not recs:
        return []
    cutoff = (datetime.now().date().toordinal() - days)
    out = []
    for r in recs:
        try:
            d = datetime.strptime(r["date"], "%Y-%m-%d").date().toordinal()
        except ValueError:
            continue
        if d >= cutoff:
            out.append(r)
    return out


def compute_trend(recs, target_min):
    if not recs:
        return None
    tots = [r["_total"] for r in recs]
    effs = [r["_eff"] for r in recs]
    lats = [r["_latency"] for r in recs]
    quals = [r.get("quality", 0) for r in recs if r.get("quality")]
    beds = [r["_bed_min"] for r in recs]
    wakes = [r["_wake_min"] for r in recs]
    avg_total = statistics.mean(tots)
    debt = max(target_min - avg_total, 0)
    regularity = regularity_score(beds, wakes)
    res = {
        "nights": len(recs),
        "avg_total": round(avg_total, 1),
        "avg_eff": round(statistics.mean(effs), 1),
        "avg_latency": round(statistics.mean(lats), 1),
        "min_eff": round(min(effs), 1),
        "avg_quality": round(statistics.mean(quals), 2) if quals else None,
        "debt": round(debt, 1),
        "regularity": round(regularity, 1),
        "bed_std": round(statistics.pstdev(beds), 0) if len(beds) > 1 else 0.0,
        "wake_std": round(statistics.pstdev(wakes), 0) if len(wakes) > 1 else 0.0,
    }
    return res


def regularity_score(beds, wakes):
    """睡眠规律性评分（Sleep Regularity Index 的简化代理）。
    基于就寝与起床时间的日间标准差映射：标准差越小越规律。
    诚实声明：这是 Phillips et al. 2017 SRI 的工程近似，非逐分钟逐对的全量 SRI。"""
    if len(beds) < 2:
        return 100.0
    bed_std = statistics.pstdev(beds)
    wake_std = statistics.pstdev(wakes)
    avg_std = (bed_std + wake_std) / 2.0
    # 经验映射：std 0min -> 100；std 90min -> ~0
    score = 100.0 - (avg_std / 90.0) * 100.0
    return max(0.0, min(100.0, score))


def compute_rhythm(recs):
    if not recs:
        return None
    mids = [r["_mid"] for r in recs]
    avg_mid = statistics.mean(mids)
    work = [r["_mid"] for r in recs if r.get("daytype") == "work"]
    free = [r["_mid"] for r in recs if r.get("daytype") == "free"]
    chrono = "中间型"
    if avg_mid < 180:
        chrono = "早鸟型（晨型）"
    elif avg_mid > 270:
        chrono = "夜猫型（晚型）"
    sjl = None
    if work and free:
        sjl = abs(statistics.mean(work) - statistics.mean(free)) / 60.0
    return {
        "avg_mid": round(avg_mid, 1),
        "avg_mid_clock": fmt_clock(avg_mid),
        "chrono": chrono,
        "sjl_hours": round(sjl, 2) if sjl is not None else None,
        "n_work": len(work),
        "n_free": len(free),
    }


def weak_spots(trend, recs, data):
    """返回弱项原因列表（中文）。空列表表示无弱项。"""
    prof = load_profile(data)
    target = prof.get("target_min", DEFAULT_TARGET_MIN)
    spots = []
    if trend is None:
        return ["暂无足够记录，无法评估"]
    if trend["avg_eff"] < WEAK_EFFICIENCY:
        spots.append("平均睡眠效率 %.1f%% 低于 %.0f%%（卧床但没睡着的时间偏多）"
                     % (trend["avg_eff"], WEAK_EFFICIENCY))
    if trend["avg_total"] < (target * 0.95):
        spots.append("平均睡眠时长 %s 低于目标（睡眠债累积中）" % fmt_min(trend["avg_total"]))
    if trend["debt"] > WEAK_DEBT_MIN:
        spots.append("日均睡眠债 %.0f 分钟，超过 %.0f 分钟阈值" % (trend["debt"], WEAK_DEBT_MIN))
    if trend["regularity"] < WEAK_REGULARITY:
        spots.append("睡眠规律性 %.1f 低于 %.0f（作息漂移，生物钟难稳）"
                     % (trend["regularity"], WEAK_REGULARITY))
    if trend["avg_latency"] > WEAK_LATENCY_MIN:
        spots.append("平均入睡潜伏期 %.0f 分钟，高于 %.0f 分钟（躺下难入睡）"
                     % (trend["avg_latency"], WEAK_LATENCY_MIN))
    # 咖啡因 / 屏幕（取近期）
    late_caf = [r for r in recs if r.get("caffeine_h") is not None and r["caffeine_h"] < CAFFEINE_CUTOFF_H]
    if late_caf:
        spots.append("有 %d 晚咖啡因摄入距就寝不足 %d 小时" % (len(late_caf), CAFFEINE_CUTOFF_H))
    high_screen = [r for r in recs if r.get("screen") is not None and r["screen"] > SCREEN_WEAK_MIN]
    if high_screen:
        spots.append("有 %d 晚睡前屏幕超过 %d 分钟" % (len(high_screen), SCREEN_WEAK_MIN))
    return spots


# ---------- 子命令 ----------
def cmd_log(args, data):
    if not args.date:
        die("缺少 --date（格式 YYYY-MM-DD）", 4)
    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        die("日期格式应为 YYYY-MM-DD：" + str(args.date), 4)
    if not args.bedtime or not args.wake:
        die("至少需提供 --bedtime 与 --wake", 4)
    rec = {
        "type": "sleep",
        "date": args.date,
        "bedtime": args.bedtime,
        "onset": args.onset or "",
        "wake": args.wake,
        "rise": args.rise or "",
        "wakings": args.wakings,
        "waso": args.waso,
        "latency": args.latency,
        "quality": args.quality,
        "caffeine_h": args.caffeine,
        "alcohol": args.alcohol,
        "screen": args.screen,
        "exercise": 1 if args.exercise else 0,
        "mood": args.mood,
        "daytype": args.daytype or "",
        "note": args.note or "",
    }
    derive(rec)
    append_event(data, rec)
    print("已记录 %s 的睡眠：" % args.date)
    print("  卧床 %s，入睡潜伏 %s，总睡眠 %s，效率 %s%%"
          % (fmt_min(rec["_tib"]), fmt_min(rec["_latency"]),
             fmt_min(rec["_total"]), rec["_eff"]))
    if rec.get("quality"):
        print("  主观质量 %d/5，次日情绪 %s"
              % (rec["quality"], rec.get("mood") if rec.get("mood") else "—"))
    print("  睡眠中点 %s（时型初判见 rhythm 命令）" % fmt_clock(rec["_mid"]))
    return 0


def cmd_trend(args, data):
    recs = [derive(r) for r in load_events(data)]
    if not recs:
        print("暂无睡眠记录，先用 log 记录几晚。")
        return 0
    prof = load_profile(data)
    target = args.target or prof.get("target_min", DEFAULT_TARGET_MIN)
    win = recent(recs, args.days)
    t = compute_trend(win, target)
    if not t:
        print("近 %d 天没有记录。" % args.days)
        return 0
    print("近 %d 晚睡眠趋势（目标 %s）：" % (t["nights"], fmt_min(target)))
    print("  平均总睡眠：%s" % fmt_min(t["avg_total"]))
    print("  平均睡眠效率：%.1f%%（最低 %.1f%%）" % (t["avg_eff"], t["min_eff"]))
    print("  平均入睡潜伏期：%s" % fmt_min(t["avg_latency"]))
    print("  平均主观质量：%s/5" % (t["avg_quality"] if t["avg_quality"] else "—"))
    print("  日均睡眠债：%s" % fmt_min(t["debt"]))
    print("  规律性评分：%.1f/100（就寝波动±%.0fmin，起床波动±%.0fmin）"
          % (t["regularity"], t["bed_std"], t["wake_std"]))
    return 0


def cmd_rhythm(args, data):
    recs = [derive(r) for r in load_events(data)]
    r = compute_rhythm(recs)
    if not r:
        print("记录不够，无法学出节律。建议先累计 14 晚以上，并用 --daytype work/free 标记。")
        return 0
    beds = [x["_bed_min"] for x in recs]
    wakes = [x["_wake_min"] for x in recs]
    reg = regularity_score(beds, wakes)
    print("从 %d 晚记录学出的生理节律：" % len(recs))
    print("  平均睡眠中点：%s" % r["avg_mid_clock"])
    print("  推断时型：%s" % r["chrono"])
    print("  睡眠规律性（SRI 工程近似）：%.1f/100" % reg)
    if r["sjl_hours"] is not None:
        print("  社会时差：%.2f 小时（工作 vs 自由日中点差）" % r["sjl_hours"])
        if r["sjl_hours"] >= 2:
            print("  ⚠ 社会时差偏大，周末补觉反而打乱生物钟")
    else:
        print("  社会时差：样本不足（需同时有 work 与 free 标记）")
    return 0


def cmd_nudge(args, data):
    recs = [derive(r) for r in load_events(data)]
    prof = load_profile(data)
    target = args.target or prof.get("target_min", DEFAULT_TARGET_MIN)
    win = recent(recs, args.days)
    t = compute_trend(win, target)
    if not t:
        print("近 %d 天没有记录，先 log 几晚再来看建议。" % args.days)
        return 0
    spots = weak_spots(t, win, data)
    if not spots:
        print("近期指标都在健康区间，维持当前节律即可。")
        return 0
    print("基于你的近期模式，建议优先做这些（按影响排序）：")
    # 简单优先级：规律性 > 时长债 > 效率 > 潜伏期 > 习惯
    order = ["规律性", "睡眠债", "效率", "入睡潜伏", "咖啡因", "屏幕"]
    spots.sort(key=lambda s: min([i for i, k in enumerate(order) if k in s], default=99))
    for s in spots:
        print("  - " + s)
    return 0


def cmd_report(args, data):
    recs = [derive(r) for r in load_events(data)]
    prof = load_profile(data)
    target = args.target or prof.get("target_min", DEFAULT_TARGET_MIN)
    if not recs:
        print("暂无睡眠记录，先用 log 记录几晚。")
        return 0
    win = recent(recs, args.days)
    t = compute_trend(win, target)
    if not t:
        print("近 %d 天没有记录，无法生成报告。可加大 --days，或先记录更多睡眠。" % args.days)
        return 0
    r = compute_rhythm(recs)
    spots = weak_spots(t, win, data)
    lines = []
    lines.append("# 睡眠掌握度报告 " + today_str())
    lines.append("")
    lines.append("- 评估窗口：近 %d 晚（共 %d 晚记录）" % (t["nights"], len(recs)))
    lines.append("- 目标睡眠时长：%s" % fmt_min(target))
    lines.append("")
    lines.append("## 近期趋势")
    lines.append("")
    lines.append("- 平均总睡眠：%s" % fmt_min(t["avg_total"]))
    lines.append("- 平均睡眠效率：%.1f%%（最低 %.1f%%）" % (t["avg_eff"], t["min_eff"]))
    lines.append("- 平均入睡潜伏期：%s" % fmt_min(t["avg_latency"]))
    lines.append("- 平均主观质量：%s/5" % (t["avg_quality"] if t["avg_quality"] else "—"))
    lines.append("- 日均睡眠债：%s" % fmt_min(t["debt"]))
    lines.append("- 规律性评分：%.1f/100" % t["regularity"])
    lines.append("")
    if r:
        lines.append("## 生理节律")
        lines.append("")
        lines.append("- 平均睡眠中点：%s" % r["avg_mid_clock"])
        lines.append("- 推断时型：%s" % r["chrono"])
        if r["sjl_hours"] is not None:
            lines.append("- 社会时差：%.2f 小时" % r["sjl_hours"])
        lines.append("")
    if spots:
        lines.append("## 弱项预警（需关注）")
        lines.append("")
        for s in spots:
            lines.append("- " + s)
        lines.append("")
    rep_path = os.path.join(data, "reports", "sleep-" + today_str() + ".md")
    with open(rep_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))
    print("\n报告已落盘：" + rep_path)
    return 1 if spots else 0


def cmd_plan(args, data):
    recs = [derive(r) for r in load_events(data)]
    prof = load_profile(data)
    target = args.target or prof.get("target_min", DEFAULT_TARGET_MIN)
    win = recent(recs, args.days)
    t = compute_trend(win, target)
    if not t:
        print("近 %d 天没有记录，先 log 几晚再来定本周计划。" % args.days)
        return 0
    spots = weak_spots(t, win, data)
    if not spots:
        print("本周没有紧急弱项，保持节律即可。")
        return 0
    # 选影响最大的一个作为本周计划
    order = ["规律性", "睡眠债", "效率", "入睡潜伏", "咖啡因", "屏幕"]
    spots.sort(key=lambda s: min([i for i, k in enumerate(order) if k in s], default=99))
    top = spots[0]
    print("本周冲刺计划：")
    print("  主攻：" + top)
    if "规律性" in top:
        print("  做法：固定起床时间（即使周末），就寝时间随睡眠债小幅前移，±30min 内。")
    elif "睡眠债" in top or "时长" in top:
        print("  做法：每晚提前 15-20 分钟就寝，连续 7 晚，优先补回债而非周末猛睡。")
    elif "效率" in top:
        print("  做法：缩短卧床时长至接近实际睡眠（刺激控制），减少床上清醒时间。")
    elif "入睡潜伏" in top:
        print("  做法：建立 30 分钟无屏幕缓冲，床只用于睡，睡不着就起坐。")
    elif "咖啡因" in top:
        print("  做法：咖啡因截止时间前移到下午 2 点前。")
    elif "屏幕" in top:
        print("  做法：睡前 60 分钟进入无屏幕时段，改用纸质或音频。")
    return 0


def build_parser():
    p = argparse.ArgumentParser(
        description="self-sleep-agent 引擎 v" + ENGINE_VERSION +
                    "：睡眠质量趋势 + 生理节律学习（AI Agent 引擎）")
    p.add_argument("--data", required=True, help="数据目录（存放 jsonl 与产物）")
    p.add_argument("--version", action="version",
                   version="self-sleep-agent " + ENGINE_VERSION)
    sub = p.add_subparsers(dest="cmd")

    a = sub.add_parser("log", help="记录一晚睡眠")
    a.add_argument("--date", default="")
    a.add_argument("--bedtime", default="")
    a.add_argument("--onset", default="")
    a.add_argument("--wake", default="")
    a.add_argument("--rise", default="")
    a.add_argument("--wakings", type=int, default=0)
    a.add_argument("--waso", type=int, default=0)
    a.add_argument("--latency", type=int, default=None,
                   help="入睡潜伏期（分钟，躺下到睡着）；提供则覆盖由 onset 推算")
    a.add_argument("--quality", type=int, default=0)
    a.add_argument("--caffeine", type=int, default=None,
                   help="咖啡因距就寝小时数（越小越近就寝）")
    a.add_argument("--alcohol", type=int, default=0, help="酒精单位数")
    a.add_argument("--screen", type=int, default=None, help="睡前屏幕分钟")
    a.add_argument("--exercise", action="store_true", help="当日是否运动")
    a.add_argument("--mood", type=int, default=0, help="次日情绪 1-5")
    a.add_argument("--daytype", default="", help="work/free，用于社会时差")
    a.add_argument("--note", default="")

    b = sub.add_parser("trend", help="近期趋势")
    b.add_argument("--days", type=int, default=14)
    b.add_argument("--target", type=int, default=0, help="目标睡眠分钟，默认450")

    c = sub.add_parser("rhythm", help="学出生理节律/时型")

    d = sub.add_parser("nudge", help="给出可执行建议")
    d.add_argument("--days", type=int, default=14)
    d.add_argument("--target", type=int, default=0)

    e = sub.add_parser("report", help="完整报告+弱项预警")
    e.add_argument("--days", type=int, default=14)
    e.add_argument("--target", type=int, default=0)

    f = sub.add_parser("plan", help="本周最值得做的一个改变")
    f.add_argument("--days", type=int, default=14)
    f.add_argument("--target", type=int, default=0)
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(4)
    data = os.path.abspath(args.data)
    ensure_dirs(data)
    handlers = {
        "log": cmd_log, "trend": cmd_trend, "rhythm": cmd_rhythm,
        "nudge": cmd_nudge, "report": cmd_report, "plan": cmd_plan,
    }
    if args.cmd not in handlers:
        die("未知子命令：" + args.cmd, 4)
    sys.exit(handlers[args.cmd](args, data))


if __name__ == "__main__":
    main()
