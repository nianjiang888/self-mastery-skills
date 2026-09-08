#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
self-create-agent 真引擎
================================

把「想创作却卡住、产出时断时续、越写越没底」这件模糊的焦虑，拆成可记录、
可计算、可复核的指标：
捕获灵感 → 记录作品 → 量化产出频率 / 质量趋势 / 灵感兑现率 / 卡在哪一环
（灵感→启动 / 启动→完成 / 完成→打磨 / 打磨→发布）→ 识别反复模式 → 给本周唯一行动。

服务对象是「用 AI 的人」本人——那个点子很多却很少落地、开了头收不了尾、
打磨完不敢发、发了又不知道下一步该练什么的你。

设计原则（与 self 系列一致）：
- 纯标准库，确定性、可重跑；
- 留实物证据：events.jsonl（按 type+id 幂等覆盖）+ profile.json + reports/create-<日期>.md；
- 退出码：0 正常 / 1 需关注（中或高严重度）/ 2 用法错误 / 4 参数或数据不可用。

注意：这是「创作教练」工具，不做原创性判定、不替代你的审美与判断。
"""

import os
import sys
import json
import argparse
from datetime import datetime, date, timedelta

ENGINE_VERSION = "2.0.0"

DEFAULT_WINDOW = 30

# 严重度阈值
WEAK_IDEA_REDEEM = 30.0   # 灵感兑现率低于此 = 高（灵感囤积不流动）
WEAK_SHIP_RATE = 50.0     # 发布率低于此 = 中
WEAK_FINISH_RATE = 50.0   # 完成率低于此 = 中
WEAK_QUALITY = 3.0        # 平均质量低于此 = 中
WEAK_GAP_DAYS = 14        # 产出断档超过此天数 = 高
WEAK_FREQ_WEEK = 0.8      # 每周产出低于此件 = 中（长不出 1 件/周）
MIN_RECORDS_FOR_PATTERN = 5  # 少于此条不做模式判定（样本不足）

# 创作闭环阶段（数字=到达深度）
STAGES = ["灵感", "启动", "完成", "打磨", "发布"]
STAGE_ORDER = {"启动": 1, "完成": 2, "打磨": 3, "发布": 4}
IDEA_STATUS = ["灵感", "已启动", "已转化"]

# 瓶颈 → 突破剧本 key（与 resources/create-scripts.json 对应）
KEYS = {
    "idea-to-work": "灵感变作品",
    "start-to-finish": "启动到完成",
    "finish-to-polish": "完成到打磨",
    "polish-to-ship": "打磨到发布",
    "raise-quality": "质量提升",
    "keep-output": "持续产出",
    "focus-range": "聚焦与跨度",
    "healthy": "登顶健康",
}


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


def load_ideas(data):
    return [r for r in _load_all(data) if r.get("type") == "idea"]


def load_works(data):
    return [r for r in _load_all(data) if r.get("type") == "work"]


def append_event(data, ev):
    """按 type+id 幂等覆盖：同 id 重记只保留最新（用于修正，不重复计数）。"""
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
    # 严格大于：窗口 [今天-days, 今天]，与折算口径一致
    cut = (date.today() - timedelta(days=days)).isoformat()
    return [r for r in recs if r.get("date", "") > cut]


def die(msg, code=4):
    print("错误：" + msg, file=sys.stderr)
    sys.exit(code)


# ------------------------- 推断与统计 -------------------------
def _mean(vals):
    return sum(vals) / len(vals) if vals else 0.0


def _rate(part, total):
    return round(part / total * 100, 1) if total else 0.0


def _days_between(a, b):
    da = datetime.strptime(a, "%Y-%m-%d").date()
    db = datetime.strptime(b, "%Y-%m-%d").date()
    return (db - da).days


def _max_gap(dates, days):
    """窗口内最长无产出天数（含首尾）。"""
    if not dates:
        return days
    cut = (date.today() - timedelta(days=days)).isoformat()
    today = date.today().isoformat()
    gaps = [_days_between(cut, dates[0])]
    for i in range(1, len(dates)):
        gaps.append(_days_between(dates[i - 1], dates[i]))
    gaps.append(_days_between(dates[-1], today))
    return max(g for g in gaps if g >= 0)


def infer_bottleneck(s):
    """推断创作闭环卡在哪一环——本包的原创量化点（类比沟通的三层推断）。

    优先级：上游灵感变现 > 聚焦失衡 > 阶段滞留 > 质量 > 频率 > 健康。
    """
    if s is None or s["n_works"] < MIN_RECORDS_FOR_PATTERN:
        return "样本不足"
    n = s["n_works"]
    if s["idea_redeem"] is not None and s["idea_redeem"] < WEAK_IDEA_REDEEM:
        return "idea-to-work"
    if s["distinct_themes"] == 1 and n >= MIN_RECORDS_FOR_PATTERN:
        return "focus-range"
    if s["max_theme_share"] < 0.25 and n >= MIN_RECORDS_FOR_PATTERN:
        return "focus-range"
    dist = s["stage_dist"]
    stuck_start = dist.get("启动", 0)
    stuck_finish = dist.get("完成", 0)
    stuck_polish = dist.get("打磨", 0)
    ship = dist.get("发布", 0)
    if ship >= n * 0.6 and s["quality_trend"] != "下降" and s["avg_quality"] >= WEAK_QUALITY:
        return "healthy"
    cand = [("start-to-finish", stuck_start),
            ("finish-to-polish", stuck_finish),
            ("polish-to-ship", stuck_polish)]
    cand.sort(key=lambda x: -x[1])
    if cand[0][1] > 0 and cand[0][1] >= n * 0.3:
        return cand[0][0]
    if s["avg_quality"] < WEAK_QUALITY:
        return "raise-quality"
    if s["freq_week"] < WEAK_FREQ_WEEK:
        return "keep-output"
    return "healthy"


def compute_stats(ideas, works, days):
    if not works:
        return None
    win = recent(works, days)
    if not win:
        return None
    n = len(win)
    qualities = [float(w.get("quality") or 3) for w in win]
    avg_quality = round(_mean(qualities), 2)
    reached = [STAGE_ORDER.get(w.get("stage"), 1) for w in win]
    finish_rate = _rate(len([r for r in reached if r >= 2]), n)
    polish_rate = _rate(len([r for r in reached if r >= 3]), n)
    ship_rate = _rate(len([r for r in reached if r >= 4]), n)

    # 灵感兑现率（窗口内灵感转化比例）
    win_ideas = recent(ideas, days)
    if win_ideas:
        redeemed = len([i for i in win_ideas if i.get("status") == "已转化"])
        idea_redeem = _rate(redeemed, len(win_ideas))
    else:
        idea_redeem = None

    # 质量趋势：前半 vs 后半（仅在作品落在 ≥2 个不同日期时有意义，
    # 同日批量记录会误报「下降」）
    wdates_distinct = sorted(set(w.get("date", "") for w in win))
    if len(wdates_distinct) < 2:
        trend = "平稳"
    else:
        sw = sorted(win, key=lambda w: w.get("date", ""))
        half = n // 2
        early = qualities[:half] if half > 0 else qualities
        late = qualities[half:] if half > 0 else qualities
        early_q = _mean(early)
        late_q = _mean(late)
        if late_q - early_q > 0.2:
            trend = "上升"
        elif early_q - late_q > 0.2:
            trend = "下降"
        else:
            trend = "平稳"

    # 频率（件/周）
    freq_week = round(n / (days / 7.0), 2)

    # 断档
    wdates = sorted(set(w.get("date", "") for w in win))
    gap = _max_gap(wdates, days)

    # 聚焦度
    themes = [w.get("theme") or "未分类" for w in win]
    tcount = {}
    for t in themes:
        tcount[t] = tcount.get(t, 0) + 1
    distinct = len(tcount)
    max_share = max(tcount.values()) / n if tcount else 0.0

    # 外部反馈均值（可选）
    fb = [float(w.get("feedback")) for w in win if w.get("feedback") not in (None, "")]
    avg_feedback = round(_mean(fb), 2) if fb else None

    stage_dist = {}
    for st in STAGES[1:]:  # 启动/完成/打磨/发布
        stage_dist[st] = len([w for w in win if w.get("stage") == st])

    s = {
        "window_days": days,
        "n_works": n,
        "n_ideas": len(win_ideas),
        "avg_quality": avg_quality,
        "quality_trend": trend,
        "finish_rate": finish_rate,
        "polish_rate": polish_rate,
        "ship_rate": ship_rate,
        "idea_redeem": idea_redeem,
        "freq_week": freq_week,
        "max_gap": gap,
        "distinct_themes": distinct,
        "max_theme_share": round(max_share, 2),
        "avg_feedback": avg_feedback,
        "stage_dist": stage_dist,
    }
    s["bottleneck"] = infer_bottleneck(s)
    return s


def weak_spots(s):
    """返回 [(严重度, 文案, 行动建议)]。行动与弱项强制同源。"""
    if not s:
        return []
    spots = []
    n = s["n_works"]
    thin = n < MIN_RECORDS_FOR_PATTERN

    if s["idea_redeem"] is not None and s["idea_redeem"] < WEAK_IDEA_REDEEM:
        spots.append(("高", "灵感兑现率仅 %.1f%%（<%d%%）：抓了一堆点子却很少落地，灵感库在囤积而不是流动" % (s["idea_redeem"], WEAK_IDEA_REDEEM),
                      "每周固定挑 1 条灵感，用「最小可行版本」逼自己当天开个头（标题+三句话大纲就算启动）"))

    if s["max_gap"] > WEAK_GAP_DAYS:
        spots.append(("高", "最长断档 %d 天（>%d）：产出一停，手感和热度都掉得快" % (s["max_gap"], WEAK_GAP_DAYS),
                      "设一条「不间断链条」：哪怕只产 1 件微作品，也别让任意 14 天完全空窗"))

    if s["quality_trend"] == "下降":
        spots.append(("高", "质量趋势在下降（后半段平均低于前半段）：越赶越糙，或者开始凑数",
                      "先降量保质：把频率砍一半，但每件都过一遍质量自检清单再发"))

    if not thin and s["ship_rate"] < WEAK_SHIP_RATE:
        spots.append(("中", "发布率 %.1f%%（<%d%%）：不少作品打磨完却压在抽屉里没发" % (s["ship_rate"], WEAK_SHIP_RATE),
                      "把「发布」从一次性大事改成日常动作：定一个最小发布格式，写完就发，别等完美"))

    if not thin and s["finish_rate"] < WEAK_FINISH_RATE:
        spots.append(("中", "完成率 %.1f%%（<%d%%）：开了头经常收不了尾" % (s["finish_rate"], WEAK_FINISH_RATE),
                      "给每件作品设「完成线」而非「完美线」：先出能看的初稿，精修放第二轮"))

    if s["freq_week"] < WEAK_FREQ_WEEK:
        spots.append(("中", "产出频率仅 %.2f 件/周（<%.1f）：手感靠的是密度，不是单次爆发" % (s["freq_week"], WEAK_FREQ_WEEK),
                      "把创作塞进固定时段（如每天清晨 30 分钟），用习惯叠加而不是靠状态"))

    if s["distinct_themes"] == 1 and not thin:
        spots.append(("中", "主题始终只有 1 个：没有跨度，难形成复利式积累与新的连接",
                      "在主线之外设一个「实验田」主题，每月至少试 1 件不同品类的作品"))
    elif s["max_theme_share"] < 0.25 and not thin:
        spots.append(("中", "主题过于分散（最集中主题占比仅 %.0f%%）：样样都碰、样样不深" % (s["max_theme_share"] * 100),
                      "收敛到 2-3 个主线主题，让作品之间能互相加成"))

    if s["avg_quality"] < WEAK_QUALITY:
        spots.append(("中", "平均质量 %.2f（<%d）：发出去的作品自己都不满意" % (s["avg_quality"], WEAK_QUALITY),
                      "每次产出后用「共识评估」思路请一个懂行的人给分，针对性练最弱的那一项"))

    if thin:
        spots.append(("低", "只有 %d 件作品（<%d），模式判定暂不可靠" % (n, MIN_RECORDS_FOR_PATTERN),
                      "继续记录到 %d 件以上，瓶颈识别才有统计意义" % MIN_RECORDS_FOR_PATTERN))

    return spots


# ------------------------- 资源加载 -------------------------
def load_resource(name):
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "resources", name)
    if not os.path.exists(p):
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# ------------------------- 子命令 -------------------------
def cmd_set(args, data):
    prof = load_profile(data)
    if args.name is not None:
        prof["name"] = args.name
    if args.domain is not None:
        prof["domain"] = args.domain
    if args.focus is not None:
        prof["focus"] = args.focus
    if args.goal is not None:
        prof["goal"] = args.goal
    if args.note:
        prof["note"] = args.note
    if not prof:
        print("没有需要更新的字段。可用：--name --domain --focus --goal --note")
        return 0
    save_profile(data, prof)
    print("已更新创作档案：%s" % json.dumps(prof, ensure_ascii=False))
    return 0


def cmd_idea(args, data):
    if not args.content:
        die("idea 需要 --content（灵感内容）", 4)
    if args.status not in IDEA_STATUS:
        die("status 必须是 %s" % "/".join(IDEA_STATUS), 4)
    ideas = load_ideas(data)
    if args.id:
        rid = args.id
    else:
        rid = "idea-%s#%d" % (args.date, len([i for i in ideas if i.get("date") == args.date]) + 1)
    rec = {
        "type": "idea",
        "id": rid,
        "date": args.date,
        "content": args.content,
        "theme": args.theme,
        "source": args.source or "",
        "status": args.status,
    }
    append_event(data, rec)
    print("已捕获灵感 %s [%s] 状态=%s%s" % (
        rid, args.theme, args.status, (" 来源=%s" % args.source) if args.source else ""))
    return 0


def cmd_work(args, data):
    if not args.title:
        die("work 需要 --title（作品名）", 4)
    if args.stage not in STAGE_ORDER:
        die("stage 必须是 %s" % "/".join(STAGE_ORDER.keys()), 4)
    try:
        quality = float(args.quality)
    except (TypeError, ValueError):
        die("quality 必须是 1-5 的数字", 4)
    if not (1 <= quality <= 5):
        die("quality 必须在 1-5 之间（1=很糙 5=很满意）", 4)
    if args.hours is not None and float(args.hours) <= 0:
        die("hours 必须是正数", 4)
    if args.feedback is not None and not (1 <= float(args.feedback) <= 5):
        die("feedback 必须在 1-5 之间", 4)

    works = load_works(data)
    if args.id:
        rid = args.id
    else:
        rid = "work-%s#%d" % (args.date, len([w for w in works if w.get("date") == args.date]) + 1)
    rec = {
        "type": "work",
        "id": rid,
        "date": args.date,
        "title": args.title,
        "theme": args.theme,
        "stage": args.stage,
        "quality": quality,
        "hours": float(args.hours) if args.hours is not None else None,
        "source": args.source or "",
        "feedback": float(args.feedback) if args.feedback is not None else None,
    }
    append_event(data, rec)
    print("已记录作品 %s [%s] 阶段=%s 质量%.0f 主题=%s%s"
          % (rid, args.title, args.stage, quality, args.theme,
             (" 灵感来源=%s" % args.source) if args.source else ""))
    return 0


def cmd_trend(args, data):
    works = load_works(data)
    ideas = load_ideas(data)
    if not works:
        print("还没有作品记录。先记一件：")
        print('  python scripts/create.py --data ./my_create work --title "我的第一篇" --theme 写作 --stage 发布 --quality 3')
        return 0
    s = compute_stats(ideas, works, args.days)
    if not s:
        print("近期没有落在 %d 天窗口内的作品。" % args.days)
        return 0
    print("近 %d 天创作概览（%d 件作品 / %d 条灵感）：" % (s["window_days"], s["n_works"], s["n_ideas"]))
    print("  平均质量 %.2f / 5（趋势：%s） | 频率 %.2f 件/周 | 最长断档 %d 天"
          % (s["avg_quality"], s["quality_trend"], s["freq_week"], s["max_gap"]))
    print("  完成率 %.1f%% | 打磨率 %.1f%% | 发布率 %.1f%%"
          % (s["finish_rate"], s["polish_rate"], s["ship_rate"]))
    if s["idea_redeem"] is not None:
        print("  灵感兑现率 %.1f%%（窗口内灵感转化为作品的比例）" % s["idea_redeem"])
    print("  主题跨度 %d 个（最集中占比 %.0f%%）" % (s["distinct_themes"], s["max_theme_share"] * 100))
    print("  创作闭环卡点：%s" % KEYS.get(s["bottleneck"], s["bottleneck"]))
    return 0


def cmd_review(args, data):
    """单条复盘：拆阶段 + 给对应突破剧本。"""
    works = load_works(data)
    ideas = load_ideas(data)
    if not (works or ideas):
        print("还没有作品或灵感，先用 work / idea 记一笔。")
        return 0
    # 给了 id 但找不到 → 明确报错（不悄悄复盘别的）
    if args.id:
        hit = [r for r in works if r.get("id") == args.id]
        if not hit:
            hit = [r for r in ideas if r.get("id") == args.id]
        if not hit:
            die("找不到 id=%s 的记录" % args.id, 4)
        rec = hit[-1]
    else:
        # 没给 id：复盘最近一件作品（优先作品，其次灵感）
        if works:
            rec = sorted(works, key=lambda r: r.get("date", ""))[-1]
        else:
            rec = sorted(ideas, key=lambda r: r.get("date", ""))[-1]

    if rec.get("type") == "work":
        print("复盘作品 %s  [%s]" % (rec.get("id"), rec.get("title")))
        print("  主题：%s | 阶段：%s | 质量 %.0f/5 | 投入 %s 小时"
              % (rec.get("theme"), rec.get("stage"), float(rec.get("quality") or 3),
                 ("%.1f" % rec["hours"]) if rec.get("hours") else "未记"))
        if rec.get("feedback"):
            print("  外部反馈 %.0f/5" % float(rec["feedback"]))
        print("")
        print("  它停在「%s」阶段。下一步看对应剧本："
              % rec.get("stage"))
        print("    python scripts/create.py --data <目录> script --key %s"
              % _stage_to_key(rec.get("stage")))
    else:
        print("复盘灵感 %s  [%s]" % (rec.get("id"), rec.get("theme")))
        print("  内容：%s" % rec.get("content"))
        print("  状态：%s | 来源：%s" % (rec.get("status"), rec.get("source") or "未记"))
        if rec.get("status") != "已转化":
            print("  它还没变成作品。跑 script --key idea-to-work 看怎么逼自己开个头。")
    return 0


def _stage_to_key(stage):
    return {
        "启动": "start-to-finish",
        "完成": "finish-to-polish",
        "打磨": "polish-to-ship",
        "发布": "raise-quality",
    }.get(stage, "keep-output")


def cmd_script(args, data):
    """按瓶颈 key 给突破剧本。确定性查表，不生成自由文本。"""
    res = load_resource("create-scripts.json")
    if not res:
        die("剧本库缺失：resources/create-scripts.json", 4)
    frames = res.get("frames", [])
    key = args.key
    hit = [f for f in frames if f.get("key") == key]
    if not hit:
        hit = [f for f in frames if key in (f.get("label", ""))]
    if not hit:
        die("剧本库里没有 key=%s 的模板（可用：%s）" % (key, "/".join(KEYS.keys())), 4)
    f = hit[0]
    print("瓶颈突破剧本【%s】%s" % (f.get("label", ""), f.get("source", "")))
    for i, step in enumerate(f.get("steps", []), 1):
        print("  %d. %s" % (i, step))
    if f.get("sample"):
        print("  示例：%s" % f["sample"])
    if f.get("avoid"):
        print("  避免：%s" % f["avoid"])
    return 0


def cmd_risk(args, data):
    works = load_works(data)
    ideas = load_ideas(data)
    if not works:
        print("还没有作品记录，无法扫描模式。先累计 5 件以上（包括没写完的）。")
        return 0
    s = compute_stats(ideas, works, args.days)
    if not s:
        print("近期没有落在 %d 天窗口内的作品。" % args.days)
        return 0
    spots = weak_spots(s)
    print("创作风险与模式扫描（近 %d 天，%d 件作品）：" % (s["window_days"], s["n_works"]))
    print("  平均质量 %.2f | 发布率 %.1f%% | 频率 %.2f 件/周 | 断档 %d 天"
          % (s["avg_quality"], s["ship_rate"], s["freq_week"], s["max_gap"]))
    print("  创作闭环卡点：%s" % KEYS.get(s["bottleneck"], s["bottleneck"]))
    if not spots:
        print("  未发现明显模式，保持当前节奏即可。")
        return 0
    for sev, txt, act in spots:
        print("  [%s] %s" % (sev, txt))
    top = [x for x in spots if x[0] in ("高", "中")]
    if top:
        print("  优先行动：%s" % top[0][2])
    return 1 if top else 0


def cmd_plan(args, data):
    works = load_works(data)
    ideas = load_ideas(data)
    if not works:
        print("还没有作品。先记 5 件——包括开了头没收尾的那些，它们最说明问题。")
        return 0
    s = compute_stats(ideas, works, args.days)
    if not s:
        print("近期没有落在 %d 天窗口内的作品。" % args.days)
        return 0
    spots = weak_spots(s)
    print("本周最值得练的一个：")
    if not spots:
        print("  创作结构健康。下一步可以把已经验证有效的动作固定成你的「产出仪式」。")
        return 0
    order = {"高": 0, "中": 1, "低": 2}
    spots.sort(key=lambda x: order.get(x[0], 9))
    sev, txt, act = spots[0]
    print("  [%s] %s" % (sev, txt))
    print("  → 行动：%s。" % act)
    if len(spots) > 1:
        print("  （另有 %d 项次要模式，跑 risk 看全部）" % (len(spots) - 1))
    if s["bottleneck"] not in ("healthy", "样本不足"):
        print("  配套剧本：跑 script --key %s" % s["bottleneck"])
    return 0


def cmd_report(args, data):
    works = load_works(data)
    ideas = load_ideas(data)
    if not works:
        print("还没有作品记录，先记几笔再出报告。")
        return 0
    s = compute_stats(ideas, works, args.days)
    if not s:
        print("近期没有落在 %d 天窗口内的作品。" % args.days)
        return 0
    L = []
    L.append("# 创作复盘报告（%s）" % now_iso())
    L.append("")
    L.append("- 窗口：近 %d 天，%d 件作品 / %d 条灵感" % (s["window_days"], s["n_works"], s["n_ideas"]))
    L.append("- 平均质量 %.2f / 5（趋势：%s） | 频率 %.2f 件/周 | 最长断档 %d 天"
             % (s["avg_quality"], s["quality_trend"], s["freq_week"], s["max_gap"]))
    L.append("- 完成率 %.1f%% | 打磨率 %.1f%% | 发布率 %.1f%%"
             % (s["finish_rate"], s["polish_rate"], s["ship_rate"]))
    if s["idea_redeem"] is not None:
        L.append("- 灵感兑现率 %.1f%%" % s["idea_redeem"])
    L.append("- 主题跨度 %d 个（最集中占比 %.0f%%）" % (s["distinct_themes"], s["max_theme_share"] * 100))
    if s["avg_feedback"] is not None:
        L.append("- 外部反馈均值 %.2f / 5" % s["avg_feedback"])
    L.append("- 创作闭环卡点：%s" % KEYS.get(s["bottleneck"], s["bottleneck"]))
    L.append("")
    L.append("## 模式与风险")
    spots = weak_spots(s)
    if spots:
        for sev, txt, act in spots:
            L.append("- [%s] %s" % (sev, txt))
            L.append("  - 行动：%s" % act)
    else:
        L.append("- 未发现明显模式。")
    L.append("")
    L.append("## 作品清单")
    for w in sorted(works, key=lambda r: r.get("date", "")):
        L.append("- %s [%s] 主题=%s 阶段=%s 质量%s%s"
                 % (w.get("date"), w.get("title"), w.get("theme"), w.get("stage"),
                    w.get("quality"),
                    (" 灵感=%s" % w.get("source")) if w.get("source") else ""))
    L.append("")
    L.append("## 灵感库")
    for i in sorted(ideas, key=lambda r: r.get("date", "")):
        L.append("- %s [%s] %s 状态=%s" % (i.get("date"), i.get("theme"), i.get("content"), i.get("status")))
    body = "\n".join(L) + "\n"
    print(body)
    fname = "create-%s.md" % date.today().isoformat()
    with open(os.path.join(data, "reports", fname), "w", encoding="utf-8") as f:
        f.write(body)
    print("报告已存：reports/%s" % fname)
    return 1 if any(x[0] in ("高", "中") for x in spots) else 0


# ------------------------- CLI -------------------------
def build_parser():
    p = argparse.ArgumentParser(prog="create.py", description="self-create-agent 创作引擎")
    p.add_argument("--data", default="./my_create", help="数据目录")
    p.add_argument("--version", action="store_true")
    sub = p.add_subparsers(dest="cmd")

    a = sub.add_parser("set", help="设置创作档案")
    a.add_argument("--name", default=None)
    a.add_argument("--domain", default=None, help="创作领域")
    a.add_argument("--focus", default=None, help="主攻方向")
    a.add_argument("--goal", default=None, help="阶段目标")
    a.add_argument("--note", default="")

    a = sub.add_parser("idea", help="捕获一条灵感")
    a.add_argument("--date", default=date.today().isoformat())
    a.add_argument("--content", default="", help="灵感内容（必填）")
    a.add_argument("--theme", default="未分类")
    a.add_argument("--source", default="", help="灵感来源（散步/阅读/梦…）")
    a.add_argument("--status", default="灵感", choices=IDEA_STATUS)
    a.add_argument("--id", default="", help="指定 id 可覆盖修正该条")

    a = sub.add_parser("work", help="记录一件作品")
    a.add_argument("--date", default=date.today().isoformat())
    a.add_argument("--title", default="", help="作品名（必填）")
    a.add_argument("--theme", default="未分类")
    a.add_argument("--stage", default="完成", choices=list(STAGE_ORDER.keys()))
    a.add_argument("--quality", default=None, help="自评质量 1-5（必填）")
    a.add_argument("--hours", default=None, help="投入时长（小时，可选）")
    a.add_argument("--source", default="", help="源自哪条灵感 id（可选）")
    a.add_argument("--feedback", default=None, help="外部反馈 1-5（可选）")
    a.add_argument("--id", default="", help="指定 id 可覆盖修正该条")

    for name, help_txt in (("trend", "创作全景"), ("risk", "模式与风险扫描"),
                           ("plan", "本周最值得练的一个"), ("report", "完整报告")):
        sp = sub.add_parser(name, help=help_txt)
        sp.add_argument("--days", type=int, default=DEFAULT_WINDOW)

    a = sub.add_parser("review", help="单条复盘（拆阶段）")
    a.add_argument("--id", default="", help="留空复盘最近一件作品")

    a = sub.add_parser("script", help="按瓶颈拿突破剧本")
    a.add_argument("--key", default="keep-output", help="瓶颈 key：" + "/".join(KEYS.keys()))
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
    cmd_map = {"set": cmd_set, "idea": cmd_idea, "work": cmd_work,
               "trend": cmd_trend, "review": cmd_review, "script": cmd_script,
               "risk": cmd_risk, "plan": cmd_plan, "report": cmd_report}
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
