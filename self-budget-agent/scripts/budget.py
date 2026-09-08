#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
self-budget-agent 真引擎
==========================

记账、量化储蓄率与财务风险、按 50/30/20 看预算执行、给出本周最该改的一个。
服务对象是「用 AI 的人」本人——那个钱不知道花哪了、存不下、月底心慌的你。

设计原则（与 self 系列一致）：
- 纯标准库，确定性、可重跑；
- 留实物证据：events.jsonl（按 type+id 幂等覆盖，修正不重复计数）+ profile.json + reports/budget-<日期>.md；
- 退出码：0 正常 / 1 需关注（中或高严重度弱项）/ 2 用法错误 / 4 参数或数据不可用。

注意：这是「前哨」工具，不做投资建议，不做税务/法律意见。
"""

import os
import sys
import json
import argparse
from datetime import datetime, date, timedelta

ENGINE_VERSION = "2.0.0"

DEFAULT_TARGET_SAVE = 20.0     # 目标储蓄率 %
DEFAULT_EMERGENCY_MONTHS = 3.0  # 应急金目标覆盖月数
WEAK_SAVE_RATE = 10.0          # 储蓄率低于此=中
WEAK_FIXED_SHARE = 50.0        # 固定支出占比高于此=中
WEAK_OVER_BUDGET = 20.0        # 单分类超预算百分比
WEAK_VOLATILITY = 0.8          # 日支出变异系数

# 固定支出类别（用于固定支出占比）
FIXED_CATS = {"房租", "房贷", "物业", "水电", "燃气", "保险", "贷款", "学费", "通讯", "订阅"}
# 必需 / 想要（用于 50/30/20）。两个集合必须互斥，否则 need+want 会超过 100%。
# 订阅归「想要」（娱乐/购物类居多），但仍在 FIXED_CATS 里计入固定支出。
NEED_CATS = {"房租", "房贷", "物业", "水电", "燃气", "保险", "医疗", "教育", "交通", "餐饮", "日用品", "通讯"}
WANT_CATS = {"娱乐", "购物", "旅行", "美妆", "游戏", "外食", "烟酒", "数码", "订阅", "礼物"}
assert not (NEED_CATS & WANT_CATS), "NEED_CATS 与 WANT_CATS 必须互斥"


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
    return [r for r in _load_all(data) if r.get("type") == "budget"]


def append_event(data, ev):
    """按 type+id 幂等覆盖：同 id 重记只保留最新（用于修正错账，不重复计数）。"""
    ensure_dirs(data)
    ev["ts"] = now_iso()
    rows = _load_all(data)
    key = (ev.get("type"), ev.get("id"))
    kept = [r for r in rows if (r.get("type"), r.get("id")) != key]
    kept.append(ev)
    kept.sort(key=lambda r: (r.get("date", ""), r.get("id", "")))
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
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def recent(recs, days):
    if days <= 0:
        return recs
    # 严格大于：窗口 [今天-days, 今天] 若用 >= 会多含一天，与 n_days 折算不一致
    cut = (date.today() - timedelta(days=days)).isoformat()
    return [r for r in recs if r.get("date", "") > cut]


def die(msg, code=4):
    print("错误：" + msg, file=sys.stderr)
    sys.exit(code)


# ------------------------- 统计 -------------------------
def compute_stats(recs, days, prof):
    if not recs:
        return None
    win = recent(recs, days)
    if not win:
        return None
    income = sum(float(r.get("amount") or 0) for r in win if r.get("kind") == "in")
    expense = sum(float(r.get("amount") or 0) for r in win if r.get("kind") == "out")

    # 分类支出
    cat = {}
    for r in win:
        if r.get("kind") != "out":
            continue
        c = r.get("category") or "其他"
        cat[c] = cat.get(c, 0.0) + float(r.get("amount") or 0)

    # 固定支出
    fixed = sum(v for k, v in cat.items() if k in FIXED_CATS)
    # 必需/想要
    need = sum(v for k, v in cat.items() if k in NEED_CATS)
    want = sum(v for k, v in cat.items() if k in WANT_CATS)
    other = expense - need - want
    need += other if other > 0 else 0  # 未归类默认计入必需（保守）

    n_days = max(1, days)
    monthly_expense = expense / (n_days / 30.0)
    save_rate = round((income - expense) / income * 100, 2) if income > 0 else None

    # 日支出波动（变异系数）
    daily = {}
    for r in win:
        if r.get("kind") != "out":
            continue
        d = r.get("date", "")
        daily[d] = daily.get(d, 0.0) + float(r.get("amount") or 0)
    vals = list(daily.values())
    if len(vals) >= 2:
        mean = sum(vals) / len(vals)
        var = sum((x - mean) ** 2 for x in vals) / len(vals)
        sd = var ** 0.5
        volatility = round(sd / mean, 2) if mean > 0 else 0.0
    else:
        volatility = 0.0

    # 应急金覆盖
    ef = prof.get("emergency_fund")
    cover = round(float(ef) / monthly_expense, 2) if (ef and monthly_expense > 0) else None

    # 分类预算执行
    budget_map = prof.get("cat_budget") or {}
    # 预算按窗口折算（budget_map 视为月度预算）
    months = n_days / 30.0
    over = {}
    for c, b in budget_map.items():
        b_m = float(b) * months
        act = cat.get(c, 0.0)
        if b_m > 0:
            over[c] = round(act / b_m * 100 - 100, 1)  # 正数=超支%

    cat_share = {k: round(v / expense * 100, 1) for k, v in cat.items()} if expense > 0 else {}

    return {
        "window_days": days,
        "n_records": len(win),
        "spend_days": len(vals),
        "cat": {k: round(v, 2) for k, v in cat.items()},
        "income": round(income, 2),
        "expense": round(expense, 2),
        "net": round(income - expense, 2),
        "save_rate": save_rate,
        "monthly_expense": round(monthly_expense, 2),
        "cat_share": cat_share,
        "fixed_share": round(fixed / expense * 100, 1) if expense > 0 else 0.0,
        "need_share": round(need / expense * 100, 1) if expense > 0 else 0.0,
        "want_share": round(want / expense * 100, 1) if expense > 0 else 0.0,
        "volatility": volatility,
        "emergency_cover": cover,
        "over_budget": over,
        "top_cats": sorted(cat.items(), key=lambda kv: -kv[1])[:5],
    }


def weak_spots(s, prof):
    """返回 [(严重度, 文案, 行动建议)]。

    行动与弱项必须同源——早期版本 plan 按另一条优先级链选行动，
    会出现「提示应急金不足、建议去降房租」这种自相矛盾的输出。
    """
    if not s:
        return []
    spots = []
    target_save = prof.get("target_save_rate", DEFAULT_TARGET_SAVE)
    target_months = prof.get("emergency_months", DEFAULT_EMERGENCY_MONTHS)
    top_cat = s["top_cats"][0][0] if s["top_cats"] else "最大分类"

    if s["net"] < 0:
        spots.append(("高", "窗口内净结余为负（%.2f），处于透支状态" % s["net"],
                      "本周先止血：把最大的两个「想要」类支出砍半，并把结余改成发薪日自动转出"))

    if s["emergency_cover"] is None:
        spots.append(("中", "还没设置应急金，无法评估抗风险能力",
                      "用 set --emergency_fund <金额> 登记你的现金储备，之后才能算覆盖月数"))
    elif s["emergency_cover"] < 1:
        spots.append(("高", "应急金只够 %.1f 个月开支（<1），一次意外就得借债" % s["emergency_cover"],
                      "本月先把应急金补到 1 个月开支，金额小也要先建起来（心理安全垫比收益率重要）"))
    elif s["emergency_cover"] < target_months:
        spots.append(("中", "应急金覆盖 %.1f 个月（目标 %.0f 个月）" % (s["emergency_cover"], target_months),
                      "设发薪日自动转出固定金额补齐应急金，别靠每月手动决定存多少"))

    if s["save_rate"] is None:
        spots.append(("低", "窗口内没有收入记录，储蓄率无法计算",
                      "补记收入（log --kind in），否则所有比例指标都不可信"))
    elif s["save_rate"] < WEAK_SAVE_RATE:
        spots.append(("中", "储蓄率仅 %.1f%%（<%.0f%%），几乎没存下钱" % (s["save_rate"], WEAK_SAVE_RATE),
                      "只盯「%s」这一个分类，本周给它设一个明确上限并写下来" % top_cat))
    elif s["save_rate"] < target_save:
        spots.append(("低", "储蓄率 %.1f%% 低于目标 %.0f%%，还有提升空间" % (s["save_rate"], target_save),
                      "把结余设置成发薪日自动转出，用制度代替意志力"))

    if s["fixed_share"] > WEAK_FIXED_SHARE:
        spots.append(("中", "固定支出占 %.1f%%（>%.0f%%），支出结构偏刚性" % (s["fixed_share"], WEAK_FIXED_SHARE),
                      "逐项过一遍固定支出：能否换更低房租、重谈贷款、取消不再用的订阅"))

    for c, pct in s["over_budget"].items():
        if pct > WEAK_OVER_BUDGET:
            spots.append(("中", "分类「%s」超预算 %.1f%%（>%.0f%%），是最直接的漏钱口" % (c, pct, WEAK_OVER_BUDGET),
                          "给「%s」设 24 小时冷静期，超预算的部分下周补回来" % c))

    if s["volatility"] > WEAK_VOLATILITY:
        spots.append(("低", "日支出波动大（变异系数 %.2f），说明有大额冲动消费" % s["volatility"],
                      "先连续记 30 天不做判断——恢复觉知比立刻省钱更有效"))
    return spots


# ------------------------- 子命令 -------------------------
def cmd_set(args, data):
    prof = load_profile(data)
    if args.income is not None:
        prof["income"] = args.income
    if args.target_save_rate is not None:
        prof["target_save_rate"] = args.target_save_rate
    if args.emergency_fund is not None:
        prof["emergency_fund"] = args.emergency_fund
    if args.emergency_months is not None:
        prof["emergency_months"] = args.emergency_months
    if args.cat_budget:
        bm = {}
        for seg in args.cat_budget.split(","):
            seg = seg.strip()
            if not seg:
                continue
            if "=" in seg:
                k, v = seg.split("=", 1)
            elif "：" in seg:
                k, v = seg.split("：", 1)
            else:
                # 不允许静默跳过：格式错会让人以为预算设上了，实际什么都没设
                die("预算格式错误：%s（应为 分类=金额，例如 餐饮=1500）" % seg, 4)
            try:
                bm[k.strip()] = float(v.strip())
            except ValueError:
                die("预算金额不是数字：%s（应为 分类=金额，例如 餐饮=1500）" % seg, 4)
        if not bm:
            die("预算为空，请按 分类=金额,分类=金额 填写（例如 餐饮=1500,交通=500）", 4)
        prof["cat_budget"] = bm
    if not prof:
        print("没有需要更新的字段。可用：--income --target_save_rate --emergency_fund --emergency_months --cat_budget")
        return 0
    save_profile(data, prof)
    print("已更新个人财务设置：%s" % json.dumps(prof, ensure_ascii=False))
    return 0


def cmd_log(args, data):
    if not args.date:
        die("log 需要 --date", 4)
    if args.amount is None or float(args.amount) <= 0:
        die("log 需要 --amount 且必须为正数", 4)
    recs = load_events(data)
    if args.id:
        rid = args.id
    else:
        same_day = [r for r in recs if r.get("date") == args.date]
        rid = "%s#%d" % (args.date, len(same_day) + 1)
    rec = {
        "type": "budget",
        "id": rid,
        "date": args.date,
        "kind": args.kind,
        "amount": float(args.amount),
        "category": args.category or "其他",
        "note": args.note or "",
    }
    append_event(data, rec)
    print("已记录 %s %s %.2f（%s）id=%s" % (args.date, "收入" if args.kind == "in" else "支出",
                                            float(args.amount), args.category or "其他", rid))
    return 0


def cmd_trend(args, data):
    recs = load_events(data)
    if not recs:
        print("还没有记账。先记一笔：")
        print('  python scripts/budget.py --data ./my_money log --date 2026-09-01 --kind out --amount 38 --category 餐饮')
        return 0
    prof = load_profile(data)
    s = compute_stats(recs, args.days, prof)
    if not s:
        print("近期没有落在 %d 天窗口内的记录。" % args.days)
        return 0
    print("近 %d 天收支概览（%d 条记录）：" % (s["window_days"], s["n_records"]))
    print("  收入 %.2f | 支出 %.2f | 净结余 %.2f" % (s["income"], s["expense"], s["net"]))
    if s["save_rate"] is not None:
        print("  储蓄率：%.1f%%" % s["save_rate"])
    print("  折算月支出：%.2f" % s["monthly_expense"])
    print("  必需 %.1f%% / 想要 %.1f%% | 固定支出占比 %.1f%%" % (s["need_share"], s["want_share"], s["fixed_share"]))
    if s["emergency_cover"] is not None:
        print("  应急金覆盖：%.1f 个月" % s["emergency_cover"])
    if s["top_cats"]:
        print("  支出前几名：" + "，".join("%s %.2f(%.1f%%)" % (c, v, s["cat_share"].get(c, 0))
                                          for c, v in s["top_cats"]))
    print("  日支出波动（变异系数）：%.2f（有支出的 %d 天）" % (s["volatility"], s["spend_days"]))
    return 0


def cmd_budget(args, data):
    recs = load_events(data)
    if not recs:
        print("还没有记账，无法评估预算执行。")
        return 0
    prof = load_profile(data)
    s = compute_stats(recs, args.days, prof)
    if not s:
        print("近期没有落在 %d 天窗口内的记录。" % args.days)
        return 0
    print("预算执行（近 %d 天，50/30/20 参照）：" % s["window_days"])
    print("  必需 %.1f%%（参照 50%%） | 想要 %.1f%%（参照 30%%） | 可存 %.1f%%（参照 20%%）"
          % (s["need_share"], s["want_share"], max(0.0, 100 - s["need_share"] - s["want_share"])))
    bm = prof.get("cat_budget") or {}
    if not bm:
        print("  还没设分类预算。可用 set --cat_budget 餐饮=1500,交通=500 设置（月度）。")
        return 0
    months = args.days / 30.0
    for c, b in bm.items():
        b_m = float(b) * months
        # 必须用完整 cat：top_cats 只取前 5 名，预算分类不在前 5 时会误报 0
        actual = s["cat"].get(c, 0.0)
        pct = (actual / b_m * 100) if b_m > 0 else 0
        flag = "超支" if pct > 100 else "正常"
        print("  %s：预算 %.0f / 实际 %.2f（%.0f%%）→ %s" % (c, b_m, actual, pct, flag))
    return 0


def cmd_risk(args, data):
    recs = load_events(data)
    if not recs:
        print("还没有记账，无法评估财务风险。先累计 1 个月以上。")
        return 0
    prof = load_profile(data)
    s = compute_stats(recs, args.days, prof)
    if not s:
        print("近期没有落在 %d 天窗口内的记录。" % args.days)
        return 0
    spots = weak_spots(s, prof)
    print("财务风险与弱项扫描（近 %d 天）：" % s["window_days"])
    print("  储蓄率 %s | 应急金覆盖 %s | 固定支出占比 %.1f%%"
          % (("%.1f%%" % s["save_rate"]) if s["save_rate"] is not None else "—",
             ("%.1f 月" % s["emergency_cover"]) if s["emergency_cover"] is not None else "—",
             s["fixed_share"]))
    if not spots:
        print("  未发现明显风险点，保持当前节奏即可。")
        return 0
    for sev, txt, act in spots:
        print("  [%s] %s" % (sev, txt))
    top = [x for x in spots if x[0] in ("高", "中")]
    if top:
        print("  优先行动：%s" % top[0][2])
    return 1 if top else 0


def cmd_plan(args, data):
    recs = load_events(data)
    if not recs:
        print("还没有记账。先从「连续记 30 天」开始——不判断、不批评，只记录。")
        return 0
    prof = load_profile(data)
    s = compute_stats(recs, args.days, prof)
    if not s:
        print("近期没有落在 %d 天窗口内的记录。" % args.days)
        return 0
    spots = weak_spots(s, prof)
    print("本周最值得做的一个改变：")
    if not spots:
        print("  财务结构健康。下一步可把结余自动转出（Save More Tomorrow 思路：涨薪/发奖金时自动提高储蓄）。")
        return 0
    order = {"高": 0, "中": 1, "低": 2}
    spots.sort(key=lambda x: order.get(x[0], 9))
    sev, txt, act = spots[0]
    print("  [%s] %s" % (sev, txt))
    print("  → 行动：%s。" % act)
    if len(spots) > 1:
        print("  （另有 %d 项次要问题，跑 risk 看全部）" % (len(spots) - 1))
    return 0


def cmd_report(args, data):
    recs = load_events(data)
    if not recs:
        print("还没有记账，先记几笔再出报告。")
        return 0
    prof = load_profile(data)
    s = compute_stats(recs, args.days, prof)
    if not s:
        print("近期没有落在 %d 天窗口内的记录。" % args.days)
        return 0
    lines = []
    lines.append("# 个人财务报告（%s）" % now_iso())
    lines.append("")
    lines.append("- 窗口：近 %d 天，%d 条记录" % (s["window_days"], s["n_records"]))
    lines.append("- 收入 %.2f | 支出 %.2f | 净结余 %.2f" % (s["income"], s["expense"], s["net"]))
    if s["save_rate"] is not None:
        lines.append("- 储蓄率：%.1f%%" % s["save_rate"])
    lines.append("- 折算月支出：%.2f" % s["monthly_expense"])
    lines.append("- 必需 %.1f%% / 想要 %.1f%% / 固定支出 %.1f%%" % (s["need_share"], s["want_share"], s["fixed_share"]))
    if s["emergency_cover"] is not None:
        lines.append("- 应急金覆盖：%.1f 个月" % s["emergency_cover"])
    if s["top_cats"]:
        lines.append("- 支出前几名：" + "，".join("%s %.2f" % (c, v) for c, v in s["top_cats"]))
    lines.append("- 日支出波动（变异系数）：%.2f" % s["volatility"])
    spots = weak_spots(s, prof)
    lines.append("")
    lines.append("## 弱项 / 风险预警")
    if spots:
        for sev, txt, act in spots:
            lines.append("- [%s] %s" % (sev, txt))
            lines.append("  - 行动：%s" % act)
    else:
        lines.append("- 未发现明显风险点。")
    report = "\n".join(lines) + "\n"
    print(report)
    fname = "budget-%s.md" % date.today().isoformat()
    with open(os.path.join(data, "reports", fname), "w", encoding="utf-8") as f:
        f.write(report)
    print("报告已存：reports/%s" % fname)
    return 1 if any(x[0] in ("高", "中") for x in spots) else 0


# ------------------------- CLI -------------------------
def build_parser():
    p = argparse.ArgumentParser(prog="budget.py", description="self-budget-agent 个人财务引擎")
    p.add_argument("--data", default="./my_money", help="数据目录")
    p.add_argument("--version", action="store_true")
    sub = p.add_subparsers(dest="cmd")

    a = sub.add_parser("set", help="设置收入/目标储蓄率/应急金/分类预算")
    a.add_argument("--income", type=float, default=None)
    a.add_argument("--target_save_rate", type=float, default=None)
    a.add_argument("--emergency_fund", type=float, default=None)
    a.add_argument("--emergency_months", type=float, default=None)
    a.add_argument("--cat_budget", default="")

    a = sub.add_parser("log", help="记一笔（kind=in/out）")
    a.add_argument("--date", default=date.today().isoformat())
    a.add_argument("--kind", choices=["in", "out"], default="out")
    a.add_argument("--amount", type=float, default=None)
    a.add_argument("--category", default="其他")
    a.add_argument("--note", default="")
    a.add_argument("--id", default="", help="显式指定 id 可覆盖修正该笔")

    for name, help_txt in (("trend", "收支趋势"), ("budget", "预算执行与 50/30/20"),
                           ("risk", "财务风险与弱项扫描"), ("plan", "本周最该改的一个"),
                           ("report", "完整报告")):
        s = sub.add_parser(name, help=help_txt)
        s.add_argument("--days", type=int, default=30)
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
    cmd_map = {"set": cmd_set, "log": cmd_log, "trend": cmd_trend,
               "budget": cmd_budget, "risk": cmd_risk, "plan": cmd_plan, "report": cmd_report}
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
