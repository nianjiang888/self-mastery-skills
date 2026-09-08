#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
self-fitness-agent 真引擎
==========================

记录训练、量化训练负荷与恢复、预警伤痛风险、给出渐进式下周计划。
服务对象是「用 AI 的人」本人——那个想动却总受伤、练了没效果、坚持不下来的你我。

设计原则（与 self 系列一致）：
- 纯标准库，确定性、可重跑；
- 留实物证据：events.jsonl（按 date+type 幂等覆盖）+ reports/fitness-<日期>.md；
- 退出码：0 正常 / 1 需关注（弱项或风险）/ 4 系统性警报（参数或数据不可用）。

注意：这是「前哨」工具，不做医疗诊断，伤痛持续请走正规康复/运动医学。
"""

import os
import sys
import json
import argparse
from datetime import datetime, date, timedelta

ENGINE_VERSION = "2.0.0"

DEFAULT_TARGET_FREQ = 3          # 健康维持建议周频次
ACWR_HIGH = 1.5                  # 急性:慢性负荷比 高风险的临界
ACWR_LOW = 0.8                   # 退练临界
MONOTONY_HIGH = 2.0              # 单调性过高临界
OVERUSE_SHARE = 0.6              # 单部位占比过高临界
RECOVER_POOR_SLEEP = 6.0         # 前夜睡眠评分低于此=恢复差
RECOVER_POOR_SORE = 6.0          # 酸痛高于此=恢复差


# ------------------------- 基础 IO -------------------------
def ensure_dirs(data):
    os.makedirs(data, exist_ok=True)
    os.makedirs(os.path.join(data, "reports"), exist_ok=True)


def events_path(data):
    return os.path.join(data, "events.jsonl")


def now_iso():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _load_all(data):
    p = events_path(data)
    if not os.path.exists(p):
        return []
    out = []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def load_events(data):
    return [r for r in _load_all(data) if r.get("type") == "fitness"]


def append_event(data, ev):
    """按 type+date 幂等覆盖：重记同一天同类型只保留最新，避免重复计数污染趋势。"""
    ensure_dirs(data)
    ev["ts"] = now_iso()
    rows = _load_all(data)
    key = (ev.get("type"), ev.get("date"))
    kept = [r for r in rows if (r.get("type"), r.get("date")) != key]
    kept.append(ev)
    kept.sort(key=lambda r: (r.get("date", ""), r.get("type", "")))
    with open(events_path(data), "w", encoding="utf-8") as f:
        for r in kept:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def save_profile(data, prof):
    ensure_dirs(data)
    with open(os.path.join(data, "profile.json"), "w", encoding="utf-8") as f:
        json.dump(prof, f, ensure_ascii=False, indent=2)


def load_profile(data):
    p = os.path.join(data, "profile.json")
    if not os.path.exists(p):
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def recent(recs, days):
    if days <= 0:
        return recs
    cut = (date.today() - timedelta(days=days)).isoformat()
    return [r for r in recs if r.get("date", "") >= cut]


def die(msg, code=4):
    print("错误：" + msg, file=sys.stderr)
    sys.exit(code)


# ------------------------- 派生指标 -------------------------
def to_min(hhmm):
    """'23:30' -> 1410；非法返回 None。"""
    if not hhmm:
        return None
    try:
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return None


def derive(rec):
    """计算单次训练派生指标，返回新 dict（不修改原记录）。"""
    r = dict(rec)
    typ = (r.get("type_sub") or "strength").lower()
    r["type_sub"] = typ
    duration = float(r.get("duration") or 0)
    rpe = float(r.get("rpe") or 0)
    sets = float(r.get("sets") or 0)
    reps = float(r.get("reps") or 0)
    weight = float(r.get("weight") or 0)
    zone = float(r.get("zone") or 0)

    # 单次训练压力分（工程近似，仅用于趋势/比值，绝对量不对外承诺）
    base = duration * (rpe / 10.0)
    if typ == "strength":
        strength_bonus = sets * reps * (0.5 if weight == 0 else weight / 40.0)
        load = base + strength_bonus
        tonnage = sets * reps * weight  # 总吨位 kg·次
    else:
        strength_bonus = 0.0
        load = base
        tonnage = 0.0
    r["load"] = round(load, 2)
    r["tonnage"] = round(tonnage, 2)
    r["intensity_factor"] = round((zone / 5.0) if zone else (rpe / 10.0), 3)
    # 部位集合
    parts_raw = r.get("parts") or ""
    r["parts_list"] = [p.strip() for p in str(parts_raw).split(",") if p.strip()]
    return r


# ------------------------- 趋势/负荷 -------------------------
def _daily_load(recs, days_back, ref_date):
    """返回完整日历网格：ref_date 往前 days_back 天（含），每天 load 之和（无记录记 0）。

    休息日必须计为 0，否则单调性/负荷比值会因'只统计有训练的日子'而失真。
    """
    grids = []
    for i in range(days_back - 1, -1, -1):
        day = ref_date - timedelta(days=i)
        ds = day.isoformat()
        s = 0.0
        for r in recs:
            if r.get("date", "") == ds:
                s += float(r.get("load") or 0)
        grids.append(s)
    return grids


def compute_trend(recs, days=28):
    if not recs:
        return None
    today = date.today()
    win = recent(recs, days)
    if not win:
        return None
    total_load = sum(float(r.get("load") or 0) for r in win)
    n_days = max(1, days)
    freq = len(win)
    # 周频次（按窗口推算）
    weekly_freq = round(freq / (days / 7.0), 2) if days else 0
    avg_rpe = round(sum(float(r.get("rpe") or 0) for r in win) / len(win), 2)
    avg_duration = round(sum(float(r.get("duration") or 0) for r in win) / len(win), 1)
    total_tonnage = round(sum(float(r.get("tonnage") or 0) for r in win), 1)

    # 急性(7天) / 慢性(28天周均) 负荷比 ACWR
    acute = sum(_daily_load(recs, 7, today))
    chronic_days = _daily_load(recs, 28, today)
    chronic_weekly = (sum(chronic_days) / 4.0) if chronic_days else 0.0
    acwr = round(acute / chronic_weekly, 2) if chronic_weekly > 0 else 1.0

    # 单调性 = 日均负荷 / 日负荷标准差（近 7 天，含休息日 0）
    d7 = _daily_load(recs, 7, today)
    if d7 and sum(d7) > 0:
        mean = sum(d7) / len(d7)
        var = sum((x - mean) ** 2 for x in d7) / len(d7)
        sd = var ** 0.5
        monotony = round(mean / sd, 2) if sd > 0 else 9.99
        strain = round(monotony * acute, 1)
    else:
        monotony = 0.0
        strain = 0.0

    # 部位分布
    part_count = {}
    for r in win:
        for p in r.get("parts_list") or []:
            part_count[p] = part_count.get(p, 0) + 1
    total_parts = sum(part_count.values()) or 1
    part_share = {p: round(c / total_parts, 2) for p, c in part_count.items()}

    # 恢复信号（可选字段）
    sleep_vals = [float(r.get("sleep_prev") or 0) for r in win if r.get("sleep_prev")]
    sore_vals = [float(r.get("sore") or 0) for r in win if r.get("sore")]
    avg_sleep = round(sum(sleep_vals) / len(sleep_vals), 2) if sleep_vals else None
    avg_sore = round(sum(sore_vals) / len(sore_vals), 2) if sore_vals else None

    return {
        "window_days": days,
        "nights": len(win),
        "total_load": round(total_load, 1),
        "weekly_freq": weekly_freq,
        "avg_rpe": avg_rpe,
        "avg_duration": avg_duration,
        "total_tonnage": total_tonnage,
        "acwr": acwr,
        "monotony": monotony,
        "strain": strain,
        "part_share": part_share,
        "avg_sleep_prev": avg_sleep,
        "avg_sore": avg_sore,
    }


# ------------------------- 伤痛风险 / 弱项 -------------------------
def weak_spots(t, recs, data):
    """返回弱项中文列表（每个元素 = (严重度, 文案)）。"""
    if not t:
        return []
    prof = load_profile(data) or {}
    target_freq = prof.get("target_freq", DEFAULT_TARGET_FREQ)
    spots = []
    acwr = t.get("acwr", 1.0)
    if acwr > ACWR_HIGH:
        spots.append(("高", "急性负荷突增：近 7 天负荷是常态的 %.2f 倍（>%.1f），伤痛风险显著升高，应降量或加恢复日" % (acwr, ACWR_HIGH)))
    elif acwr < ACWR_LOW:
        spots.append(("中", "负荷不足：近 7 天负荷只有常态的 %.2f 倍（<%.1f），可能进入退练区间，建议渐进加量" % (acwr, ACWR_LOW)))
    if t.get("monotony", 0) > MONOTONY_HIGH:
        spots.append(("中", "训练太单一：单调性 %.2f（>%.1f），同样刺激让身体适应也易劳损，建议加入不同动作/节奏" % (t["monotony"], MONOTONY_HIGH)))
    # 单部位过度使用
    part_share = t.get("part_share", {})
    if part_share:
        top_part, top_share = max(part_share.items(), key=lambda kv: kv[1])
        if top_share > OVERUSE_SHARE:
            spots.append(("高", "单部位过度使用：'%s' 占近期训练的 %.0f%%（>%d%%），考虑分化训练或加恢复" % (top_part, top_share * 100, int(OVERUSE_SHARE * 100))))
    if t.get("weekly_freq", 0) < target_freq:
        spots.append(("中", "训练频次偏低：近期每周约 %.1f 次（目标 %d 次），对健康维持与习惯养成偏少" % (t["weekly_freq"], target_freq)))
    # 恢复信号
    if t.get("avg_sleep_prev") is not None and t["avg_sleep_prev"] < RECOVER_POOR_SLEEP:
        spots.append(("中", "恢复不足：前夜睡眠评分均值 %.1f（<%d），训练后恢复受限，建议优先睡好再加压" % (t["avg_sleep_prev"], int(RECOVER_POOR_SLEEP))))
    if t.get("avg_sore") is not None and t["avg_sore"] > RECOVER_POOR_SORE:
        spots.append(("中", "酸痛偏重：近期酸痛均值 %.1f（>%d），身体可能未恢复，安排主动恢复" % (t["avg_sore"], int(RECOVER_POOR_SORE))))
    # 缺少恢复日（近 7 天有负荷但无低强度/柔韧）
    low = [r for r in recs if (date.today() - datetime.strptime(r["date"], "%Y-%m-%d").date()).days < 7 and (r.get("type_sub") in ("mobility", "recovery") or float(r.get("rpe") or 9) <= 3)]
    if not low and t.get("acwr", 0) >= ACWR_LOW:
        spots.append(("低", "近 7 天没有恢复/低强度训练，长期缺恢复日易累积疲劳"))
    return spots


def acwr_label(acwr):
    if acwr > ACWR_HIGH:
        return "高风险（突增）"
    if acwr >= 1.3:
        return "偏高（谨慎加量）"
    if acwr >= ACWR_LOW:
        return "安全甜区"
    return "偏低（退练风险）"


# ------------------------- 子命令 -------------------------
def cmd_log(args, data):
    if not args.date or not args.type_sub:
        die("log 需要 --date 与 --type（strength/cardio/mobility/sport）", 4)
    rec = {
        "type": "fitness",
        "date": args.date,
        "type_sub": args.type_sub,
        "duration": args.duration,
        "intensity": args.intensity,
        "zone": args.zone,
        "rpe": args.rpe,
        "sets": args.sets,
        "reps": args.reps,
        "weight": args.weight,
        "parts": args.parts or "",
        "sleep_prev": args.sleep_prev,
        "sore": args.sore,
        "note": args.note or "",
    }
    append_event(data, rec)
    print("已记录 %s 的 %s 训练（%s 分钟，RPE %s）" % (args.date, args.type_sub, args.duration, args.rpe))
    return 0


def cmd_trend(args, data):
    recs = [derive(r) for r in load_events(data)]
    if not recs:
        print("还没有训练记录。先用 log 记一次，例如：")
        print('  python scripts/fitness.py --data ./my_fit log --date 2026-09-01 --type_sub strength --duration 50 --rpe 7 --sets 4 --reps 8 --weight 60 --parts 胸,三头')
        return 0
    t = compute_trend(recs, args.days)
    if not t:
        print("近期没有落在 %d 天窗口内的记录。" % args.days)
        return 0
    print("近 %d 天训练趋势：" % t["window_days"])
    print("  记录次数：%d（约每周 %.1f 次）" % (t["nights"], t["weekly_freq"]))
    print("  训练压力分合计：%.1f（单次均值 %.1f）" % (t["total_load"], t["total_load"] / max(1, t["nights"])))
    print("  平均时长：%.0f 分钟 | 平均 RPE：%.1f" % (t["avg_duration"], t["avg_rpe"]))
    if t["total_tonnage"]:
        print("  总吨位：%.0f kg·次" % t["total_tonnage"])
    print("  急性:慢性负荷比 ACWR：%.2f（%s）" % (t["acwr"], acwr_label(t["acwr"])))
    print("  单调性：%.2f | 紧张度：%.1f" % (t["monotony"], t["strain"]))
    if t["part_share"]:
        top = max(t["part_share"].items(), key=lambda kv: kv[1])
        print("  最常练部位：%s（占 %.0f%%）" % (top[0], top[1] * 100))
    if t["avg_sleep_prev"] is not None:
        print("  前夜睡眠评分均值：%.1f / 10" % t["avg_sleep_prev"])
    if t["avg_sore"] is not None:
        print("  酸痛均值：%.1f / 10" % t["avg_sore"])
    return 0


def cmd_recover(args, data):
    recs = [derive(r) for r in load_events(data)]
    if not recs:
        print("还没有记录，无法评估恢复。先记几次训练与前夜睡眠。")
        return 0
    t = compute_trend(recs, args.days)
    if not t:
        print("近期没有落在 %d 天窗口内的记录。" % args.days)
        return 0
    signals = []
    score = 100
    if t["acwr"] > ACWR_HIGH:
        score -= 35
        signals.append("负荷突增，身体来不及适应")
    elif t["acwr"] < ACWR_LOW:
        score -= 10
        signals.append("负荷偏低，恢复压力小但可能退练")
    if t["monotony"] > MONOTONY_HIGH:
        score -= 15
        signals.append("训练单一，局部易累积疲劳")
    if t["avg_sleep_prev"] is not None and t["avg_sleep_prev"] < RECOVER_POOR_SLEEP:
        score -= 25
        signals.append("前夜睡眠差，恢复受限")
    if t["avg_sore"] is not None and t["avg_sore"] > RECOVER_POOR_SORE:
        score -= 20
        signals.append("酸痛偏重，可能未恢复")
    score = max(0, min(100, score))
    print("恢复评分（估算，0-100）：%d" % score)
    if signals:
        print("  主要拖累：" + "；".join(signals))
    else:
        print("  恢复信号良好，可正常训练。")
    if score < 60:
        print("  ⚠ 恢复偏紧，本周建议加 1-2 个恢复/低强度日，或降总量 10-20%。")
    return 0


def cmd_risk(args, data):
    recs = [derive(r) for r in load_events(data)]
    if not recs:
        print("还没有记录，无法评估伤痛风险。先累计 2-3 周训练。")
        return 0
    t = compute_trend(recs, args.days)
    if not t:
        print("近期没有落在 %d 天窗口内的记录。" % args.days)
        return 0
    spots = weak_spots(t, recs, data)
    print("伤痛风险与弱项扫描（近 %d 天）：" % t["window_days"])
    print("  ACWR %.2f → %s" % (t["acwr"], acwr_label(t["acwr"])))
    print("  单调性 %.2f（>%.1f 偏单一）" % (t["monotony"], MONOTONY_HIGH))
    if t["part_share"]:
        for p, s in sorted(t["part_share"].items(), key=lambda kv: -kv[1])[:5]:
            print("  部位 %s：%.0f%%" % (p, s * 100))
    if not spots:
        print("  未发现明显风险点，保持当前节奏即可。")
        return 0
    for sev, txt in spots:
        print("  [%s] %s" % (sev, txt))
    return 1 if any(s == "高" for s in [x[0] for x in spots]) else 0


def cmd_plan(args, data):
    recs = [derive(r) for r in load_events(data)]
    if not recs:
        print("还没有记录，先累计 2-3 周再让 Agent 给计划。现在可从每周 3 次、全身分化起步。")
        return 0
    t = compute_trend(recs, args.days)
    if not t:
        print("近期没有落在 %d 天窗口内的记录。" % args.days)
        return 0
    spots = weak_spots(t, recs, data)
    print("下周最值得做的一个改变：")
    if not spots:
        # 安全甜区 → 渐进超负荷
        print("  当前 ACWR %.2f 处于安全甜区，本周可小幅渐进加量：在主要动作上把总吨位提高约 2-5%%（多 1 组 / 加重 2.5kg / 多 1-2 次），同时保住每周 %.0f 次频次。" % (t["acwr"], t["weekly_freq"]))
        return 0
    # 按严重度排：高 > 中 > 低
    order = {"高": 0, "中": 1, "低": 2}
    spots.sort(key=lambda x: order.get(x[0], 9))
    sev, txt = spots[0]
    print("  [%s] %s" % (sev, txt))
    if t["acwr"] > ACWR_HIGH:
        print("  → 行动：本周降总量 20-30%%，增加 1-2 个恢复日，待 ACWR 回到 0.8-1.3 再恢复加量。")
    elif t["acwr"] < ACWR_LOW:
        print("  → 行动：本周在现有动作上加 1 组或加 2.5-5%% 重量，循序把周频次拉到 3 次以上。")
    elif t["monotony"] > MONOTONY_HIGH:
        print("  → 行动：把其中 1-2 次换成不同动作模式（如加入划船/臀推/单车），打破单一刺激。")
    elif t["weekly_freq"] < DEFAULT_TARGET_FREQ:
        print("  → 行动：先保频次——把训练拆成更短但更频繁（如 3×30 分钟优于 1×90 分钟）。")
    else:
        print("  → 行动：优先安排 1 个恢复/柔韧日，并确认前夜睡眠与酸痛在改善。")
    return 0


def cmd_report(args, data):
    recs = [derive(r) for r in load_events(data)]
    if not recs:
        print("还没有训练记录，先记几次再出报告。")
        return 0
    t = compute_trend(recs, args.days)
    if not t:
        print("近期没有落在 %d 天窗口内的记录。" % args.days)
        return 0
    lines = []
    lines.append("# 训练负荷与恢复报告（%s）" % now_iso())
    lines.append("")
    lines.append("- 窗口：近 %d 天，记录 %d 次（约每周 %.1f 次）" % (t["window_days"], t["nights"], t["weekly_freq"]))
    lines.append("- 训练压力分合计：%.1f；平均 RPE %.1f；平均时长 %.0f 分钟" % (t["total_load"], t["avg_rpe"], t["avg_duration"]))
    if t["total_tonnage"]:
        lines.append("- 总吨位：%.0f kg·次" % t["total_tonnage"])
    lines.append("- ACWR（急性:慢性）：%.2f → %s" % (t["acwr"], acwr_label(t["acwr"])))
    lines.append("- 单调性 %.2f；紧张度 %.1f" % (t["monotony"], t["strain"]))
    if t["part_share"]:
        top = max(t["part_share"].items(), key=lambda kv: kv[1])
        lines.append("- 最常练部位：%s（%.0f%%）" % (top[0], top[1] * 100))
    if t["avg_sleep_prev"] is not None:
        lines.append("- 前夜睡眠评分均值：%.1f / 10" % t["avg_sleep_prev"])
    if t["avg_sore"] is not None:
        lines.append("- 酸痛均值：%.1f / 10" % t["avg_sore"])
    spots = weak_spots(t, recs, data)
    lines.append("")
    if spots:
        lines.append("## 弱项 / 风险预警")
        for sev, txt in spots:
            lines.append("- [%s] %s" % (sev, txt))
    else:
        lines.append("## 弱项 / 风险预警")
        lines.append("- 未发现明显风险点。")
    report = "\n".join(lines) + "\n"
    print(report)
    # 落盘
    fname = "fitness-%s.md" % date.today().isoformat()
    with open(os.path.join(data, "reports", fname), "w", encoding="utf-8") as f:
        f.write(report)
    print("报告已存：reports/%s" % fname)
    # 仅中/高严重度算"需关注"（退出码 1）；低严重度只是温和提醒
    sev_need = [s for s in [x[0] for x in spots] if s in ("高", "中")]
    return 1 if sev_need else 0


# ------------------------- CLI -------------------------
def build_parser():
    import argparse as _ap
    p = _ap.ArgumentParser(prog="fitness.py", description="self-fitness-agent 训练负荷与恢复引擎")
    p.add_argument("--data", default="./my_fit", help="数据目录（events.jsonl + profile.json + reports/）")
    p.add_argument("--version", action="store_true", help="打印引擎版本")
    sub = p.add_subparsers(dest="cmd")

    a = sub.add_parser("log", help="记录一次训练")
    a.add_argument("--date", default=date.today().isoformat())
    a.add_argument("--type_sub", required=True, choices=["strength", "cardio", "mobility", "sport"], help="训练类型")
    a.add_argument("--duration", type=float, default=0, help="时长（分钟）")
    a.add_argument("--intensity", default="")
    a.add_argument("--zone", type=float, default=0, help="心率区间 1-5（可选）")
    a.add_argument("--rpe", type=float, default=0, help="主观用力 1-10")
    a.add_argument("--sets", type=float, default=0)
    a.add_argument("--reps", type=float, default=0)
    a.add_argument("--weight", type=float, default=0, help="重量 kg（力量训练）")
    a.add_argument("--parts", default="", help="部位，逗号分隔，如 胸,三头")
    a.add_argument("--sleep_prev", type=float, default=0, help="前夜睡眠评分 1-10（可选）")
    a.add_argument("--sore", type=float, default=0, help="训练后酸痛 1-10（可选）")
    a.add_argument("--note", default="")

    a = sub.add_parser("trend", help="训练负荷/频次/强度趋势")
    a.add_argument("--days", type=int, default=28)

    a = sub.add_parser("recover", help="恢复评分")
    a.add_argument("--days", type=int, default=14)

    a = sub.add_parser("risk", help="伤痛风险与弱项扫描")
    a.add_argument("--days", type=int, default=28)

    a = sub.add_parser("plan", help="下周最值得做的一个改变")
    a.add_argument("--days", type=int, default=28)

    a = sub.add_parser("report", help="完整报告（弱项退出码 1）")
    a.add_argument("--days", type=int, default=28)

    a = sub.add_parser("set", help="设置个人目标（target_freq 等）")
    a.add_argument("--target_freq", type=int, default=DEFAULT_TARGET_FREQ)

    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        print(ENGINE_VERSION)
        return 0
    if not args.cmd:
        parser.print_help()
        return 0
    cmd_map = {
        "log": cmd_log,
        "trend": cmd_trend,
        "recover": cmd_recover,
        "risk": cmd_risk,
        "plan": cmd_plan,
        "report": cmd_report,
        "set": lambda a, d: (save_profile(d, {"target_freq": a.target_freq}) or print("已设置目标周频次：%d" % a.target_freq)) or 0,
    }
    fn = cmd_map.get(args.cmd)
    if not fn:
        die("未知子命令：%s" % args.cmd, 2)
    return fn(args, args.data)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        die("引擎异常：%s" % e, 4)
