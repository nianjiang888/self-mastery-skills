#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
self-soothe-agent 真引擎
================================

把「情绪一来就乱、越想越糟、用错方式自我安慰反而更累」这件模糊的难受，
拆成可记录、可计算、可复核的指标：

记一次情绪事件 → 量化频率 / 平均强度 / 最常见情绪 / 最常掉进的认知扭曲 /
应对有效性（relief 均值）/ 高频触发 / 影响面（睡眠·关系） → 推断主导认知扭曲
（本包原创量化点，类比沟通的「三层卡点」、创作的「闭环卡点」）→ 识别弱项 →
给本周唯一行动 + 对应 CBT 破局剧本。

服务对象是「用 AI 的人」本人——那个被焦虑/愤怒/自我怀疑卷得睡不着、
明明想冷静却越想越乱、用了刷手机/暴食/自我攻击反而更糟的你。

设计原则（与 self 系列一致）：
- 纯标准库，确定性、可重跑；
- 留实物证据：events.jsonl（按 type+id 幂等覆盖）+ profile.json + reports/soothe-<日期>.md；
- 退出码：0 正常 / 1 需关注（中或高严重度）/ 2 用法错误 / 4 参数或数据不可用。

注意：这是「情绪调节教练」工具，不是诊断、不替代医生或咨询师。
"""

import os
import sys
import json
import argparse
from datetime import datetime, date, timedelta

ENGINE_VERSION = "2.0.0"

DEFAULT_WINDOW = 30

# 严重度阈值
WEAK_FREQ_WEEK = 3.0        # 每周情绪事件超过此 = 高（情绪过载）
WEAK_INTENSITY = 4.0        # 平均强度大于等于此 = 高
WEAK_RELIEF = 2.5          # 平均缓解低于此 = 高（应对低效）
WEAK_DISTORTION_SHARE = 0.4  # 单一扭曲占比超此 = 中（主导扭曲清晰）
WEAK_IMPACT_SHARE = 0.3    # 睡眠/关系影响占比超此 = 中
MIN_RECORDS_FOR_PATTERN = 5  # 少于此条不做模式判定（样本不足）

# 情绪类型（开放，但给常见集做归一提示）
EMOTIONS = ["焦虑", "愤怒", "悲伤", "恐惧", "羞耻", "内疚", "孤独", "烦躁", "嫉妒", "麻木", "无力", "其他"]

# 影响面（一次情绪波及的范围）
IMPACTS = ["无", "睡眠", "关系", "工作", "身体", "专注"]

# 认知扭曲 → 中文标签（Burns《好情绪坏习惯》10 类；读心/预言拆开便于定位）
DISTORTIONS = {
    "all-or-nothing": "非黑即白",
    "overgeneralization": "以偏概全",
    "mental-filter": "心理过滤",
    "disqualify-positive": "否定积极",
    "mind-reading": "读心",
    "fortune-telling": "灾难预言",
    "magnification": "放大灾难",
    "emotional-reasoning": "情绪化推理",
    "should": "应该句式",
    "labeling": "贴标签",
    "personalization": "个人化",
}

# 调节状态 key → 中文（头条展示用）
PATTERNS = {
    "emotional-overload": "情绪过载",
    "high-intensity": "高强波动",
    "ineffective-coping": "应对低效",
    "balanced": "扭曲均衡",
    "healthy": "调节健康",
    "样本不足": "样本不足",
}
# 扭曲 key 也进入 headline（与 PATTERNS 合并展示）
for _k, _v in DISTORTIONS.items():
    PATTERNS[_k] = _v


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


def load_emotions(data):
    return [r for r in _load_all(data) if r.get("type") == "emotion"]


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
    """窗口内最长无情绪记录天数（含首尾）——衡量情绪是否长期在线持续。"""
    if not dates:
        return days
    cut = (date.today() - timedelta(days=days)).isoformat()
    today = date.today().isoformat()
    gaps = [_days_between(cut, dates[0])]
    for i in range(1, len(dates)):
        gaps.append(_days_between(dates[i - 1], dates[i]))
    gaps.append(_days_between(dates[-1], today))
    return max(g for g in gaps if g >= 0)


def _mode(items):
    """返回 (mode_value, share)。items 为空返回 (None, 0.0)。"""
    if not items:
        return (None, 0.0)
    cnt = {}
    for it in items:
        cnt[it] = cnt.get(it, 0) + 1
    best = max(cnt.items(), key=lambda x: x[1])
    return (best[0], best[1] / len(items))


def infer_distortion(s):
    """推断主导认知扭曲——本包原创量化点（类比沟通三层 / 创作闭环卡点）。

    优先级：情绪过载 > 高强波动 > 应对低效 > 主导扭曲清晰 > 均衡 > 健康。
    主导扭曲取自窗口内出现最多的扭曲 tag；占比达阈值才算「清晰模式」。
    """
    if s is None or s["n"] < MIN_RECORDS_FOR_PATTERN:
        return "样本不足"
    if s["freq_week"] > WEAK_FREQ_WEEK:
        return "emotional-overload"
    if s["avg_intensity"] >= WEAK_INTENSITY:
        return "high-intensity"
    if s["avg_relief"] is not None and s["avg_relief"] < WEAK_RELIEF:
        return "ineffective-coping"
    if s["distortion_mode"] is not None and s["distortion_share"] >= WEAK_DISTORTION_SHARE:
        return s["distortion_mode"]
    if s["distortion_mode"] is not None:
        return "balanced"
    return "healthy"


def compute_stats(events, days):
    if not events:
        return None
    win = recent(events, days)
    if not win:
        return None
    n = len(win)
    intensities = [float(e.get("intensity") or 3) for e in win]
    avg_intensity = round(_mean(intensities), 2)

    # 强度趋势：前半 vs 后半（仅当落在 ≥2 个不同日期时有意义）
    edates_distinct = sorted(set(e.get("date", "") for e in win))
    if len(edates_distinct) < 2:
        trend = "平稳"
    else:
        se = sorted(win, key=lambda e: e.get("date", ""))
        half = n // 2
        early = intensities[:half] if half > 0 else intensities
        late = intensities[half:] if half > 0 else intensities
        early_i = _mean(early)
        late_i = _mean(late)
        if late_i - early_i > 0.2:
            trend = "上升"
        elif early_i - late_i > 0.2:
            trend = "下降"
        else:
            trend = "平稳"

    # 频率（件/周）
    freq_week = round(n / (days / 7.0), 2)

    # 最常见情绪
    emoji = _mode([e.get("emotion") or "其他" for e in win])
    top_emotion = emoji[0]

    # 认知扭曲分布与主导
    dist_list = [e.get("distortion") for e in win if e.get("distortion")]
    dmode, dshare = _mode(dist_list)
    distortion_mode = dmode
    distortion_share = round(dshare, 2)

    # 应对有效性
    rel = [float(e["relief"]) for e in win if e.get("relief") not in (None, "")]
    avg_relief = round(_mean(rel), 2) if rel else None
    relief_low = len([r for r in rel if r < WEAK_RELIEF])

    # 影响面分布
    impacts = [e.get("impact") or "无" for e in win]
    impact_dist = {}
    for im in impacts:
        impact_dist[im] = impact_dist.get(im, 0) + 1
    sleep_share = round(impact_dist.get("睡眠", 0) / n, 2)
    relation_share = round(impact_dist.get("关系", 0) / n, 2)

    # 触发 Top（按出现次数）
    trig = [e.get("trigger") or "未记" for e in win]
    tcount = {}
    for t in trig:
        tcount[t] = tcount.get(t, 0) + 1
    top_triggers = sorted(tcount.items(), key=lambda x: -x[1])[:3]

    # 断档
    edates = sorted(set(e.get("date", "") for e in win))
    gap = _max_gap(edates, days)

    s = {
        "window_days": days,
        "n": n,
        "avg_intensity": avg_intensity,
        "intensity_trend": trend,
        "freq_week": freq_week,
        "top_emotion": top_emotion,
        "distortion_mode": distortion_mode,
        "distortion_share": distortion_share,
        "avg_relief": avg_relief,
        "relief_low": relief_low,
        "impact_dist": impact_dist,
        "sleep_share": sleep_share,
        "relation_share": relation_share,
        "top_triggers": top_triggers,
        "max_gap": gap,
    }
    s["pattern"] = infer_distortion(s)
    return s


def weak_spots(s):
    """返回 [(严重度, 文案, 行动建议)]。行动与弱项强制同源。"""
    if not s:
        return []
    spots = []
    n = s["n"]
    thin = n < MIN_RECORDS_FOR_PATTERN

    if s["freq_week"] > WEAK_FREQ_WEEK:
        spots.append(("高", "情绪事件频率 %.2f 件/周（>%.1f）：情绪密度过高，像一直在「接飞刀」" % (s["freq_week"], WEAK_FREQ_WEEK),
                      "先做「情绪减量」：把高频触发列出来，能隔离的先隔离（如睡前不刷消息），用 script --key emotional-overlap 看做法"))

    if s["avg_intensity"] >= WEAK_INTENSITY:
        spots.append(("高", "平均强度 %.2f（≥%.1f）：每次情绪都冲得很满，缓冲被压缩" % (s["avg_intensity"], WEAK_INTENSITY),
                      "练「降级而非消灭」：强度上来先物理降温（冷水脸/慢呼吸 4-7-8），把峰值削平，再谈分析"))

    if s["avg_relief"] is not None and s["avg_relief"] < WEAK_RELIEF:
        spots.append(("高", "应对平均缓解仅 %.2f（<%.1f）：你常用的安抚方式基本没用，甚至更累" % (s["avg_relief"], WEAK_RELIEF),
                      "换一套有证据的应对：回避型（刷手机/暴食/酒精）先识别，改成交互型（表达性书写/身体活动/找人说），跑 script --key ineffective-coping"))

    if s["distortion_mode"] is not None and s["distortion_share"] >= WEAK_DISTORTION_SHARE:
        lab = DISTORTIONS.get(s["distortion_mode"], s["distortion_mode"])
        spots.append(("中", "主导认知扭曲是「%s」（占 %.0f%%）：你最近反复掉进同一个思维陷阱" % (lab, s["distortion_share"] * 100),
                      "针对性破局：跑 script --key %s，照剧本逐条反驳这条自动思维" % s["distortion_mode"]))
    elif s["distortion_mode"] is not None and s["distortion_share"] > 0:
        lab = DISTORTIONS.get(s["distortion_mode"], s["distortion_mode"])
        spots.append(("中", "最常出现的认知扭曲是「%s」（占 %.0f%%，尚未形成绝对主导）：值得留意" % (lab, s["distortion_share"] * 100),
                      "跑 script --key %s 备着，下次再掉进去能立刻反驳" % s["distortion_mode"]))

    if s["sleep_share"] >= WEAK_IMPACT_SHARE:
        spots.append(("中", "%.0f%% 的情绪波及睡眠：夜里反复想，第二天更脆" % (s["sleep_share"] * 100),
                      "设一条「睡前情绪截止线」：把盘算写进次日清单，脑子交给纸笔；睡前 1 小时不处理情绪议题"))

    if s["relation_share"] >= WEAK_IMPACT_SHARE:
        spots.append(("中", "%.0f%% 的情绪波及关系：你容易把情绪倒在最近的人身上" % (s["relation_share"] * 100),
                      "给情绪加一道「缓冲」：先对自己说一遍，再决定要不要、怎么对别人说（参考 非暴力沟通）"))

    if s["intensity_trend"] == "上升":
        spots.append(("中", "强度趋势在上升（后半段平均高于前半段）：最近情绪在加码",
                      "别等它再涨——今天就用一次「降级」动作把峰值削下来，别攒到爆发"))

    if thin:
        spots.append(("低", "只有 %d 次情绪记录（<%d），模式判定暂不可靠" % (n, MIN_RECORDS_FOR_PATTERN),
                      "继续记录到 %d 次以上，主导扭曲与应对有效性才有统计意义" % MIN_RECORDS_FOR_PATTERN))

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
    if args.focus is not None:
        prof["focus"] = args.focus
    if args.goal is not None:
        prof["goal"] = args.goal
    if args.note:
        prof["note"] = args.note
    if not prof:
        print("没有需要更新的字段。可用：--name --focus --goal --note")
        return 0
    save_profile(data, prof)
    print("已更新情绪档案：%s" % json.dumps(prof, ensure_ascii=False))
    return 0


def cmd_log(args, data):
    if not args.emotion:
        die("log 需要 --emotion（情绪类型，如 焦虑/愤怒/悲伤）", 4)
    if not args.trigger:
        die("log 需要 --trigger（这次的诱因，发生了什么）", 4)
    try:
        intensity = float(args.intensity)
    except (TypeError, ValueError):
        die("intensity 必须是 1-5 的数字", 4)
    if not (1 <= intensity <= 5):
        die("intensity 必须在 1-5 之间（1=轻微 5=失控）", 4)
    if args.distortion and args.distortion not in DISTORTIONS:
        die("distortion 必须是 %s" % "/".join(DISTORTIONS.keys()), 4)
    if args.relief is not None and not (0 <= float(args.relief) <= 5):
        die("relief 必须在 0-5 之间（0=毫无缓解 5=完全平复）", 4)
    if args.impact and args.impact not in IMPACTS:
        die("impact 必须是 %s" % "/".join(IMPACTS), 4)

    events = load_emotions(data)
    if args.id:
        rid = args.id
    else:
        rid = "emo-%s#%d" % (args.date, len([e for e in events if e.get("date") == args.date]) + 1)
    rec = {
        "type": "emotion",
        "id": rid,
        "date": args.date,
        "trigger": args.trigger,
        "emotion": args.emotion,
        "intensity": intensity,
        "thought": args.thought or "",
        "distortion": args.distortion or "",
        "action": args.action or "",
        "relief": float(args.relief) if args.relief is not None else None,
        "impact": args.impact or "无",
    }
    append_event(data, rec)
    print("已记录情绪事件 %s [%s] 强度%.0f 诱因=%s%s"
          % (rid, args.emotion, intensity, args.trigger,
             (" 扭曲=%s" % DISTORTIONS.get(args.distortion, args.distortion)) if args.distortion else ""))
    return 0


def cmd_trend(args, data):
    events = load_emotions(data)
    if not events:
        print("还没有情绪记录。先记一次：")
        print('  python scripts/soothe.py --data ./my_soothe log --emotion 焦虑 --trigger "项目又延期" --intensity 4 --distortion fortune-telling')
        return 0
    s = compute_stats(events, args.days)
    if not s:
        print("近期没有落在 %d 天窗口内的情绪记录。" % args.days)
        return 0
    print("近 %d 天情绪概览（%d 次事件）：" % (s["window_days"], s["n"]))
    print("  平均强度 %.2f / 5（趋势：%s） | 频率 %.2f 件/周 | 最长平静 %d 天"
          % (s["avg_intensity"], s["intensity_trend"], s["freq_week"], s["max_gap"]))
    print("  最常见情绪：%s" % (s["top_emotion"] or "—"))
    if s["distortion_mode"]:
        print("  最常掉进的认知扭曲：%s（占 %.0f%%）"
              % (DISTORTIONS.get(s["distortion_mode"], s["distortion_mode"]), s["distortion_share"] * 100))
    else:
        print("  暂无认知扭曲标记（log 时加 --distortion 才能识别模式）")
    if s["avg_relief"] is not None:
        print("  应对平均缓解 %.2f / 5（0=没用 5=完全平复）" % s["avg_relief"])
    if s["top_triggers"]:
        print("  高频诱因：%s" % "、".join("%s(%d)" % (t, c) for t, c in s["top_triggers"]))
    print("  调节状态：%s" % PATTERNS.get(s["pattern"], s["pattern"]))
    return 0


def cmd_review(args, data):
    """单条复盘：拆诱因→情绪→扭曲→应对，给对应破局剧本。"""
    events = load_emotions(data)
    if not events:
        print("还没有情绪记录，先用 log 记一笔。")
        return 0
    if args.id:
        hit = [e for e in events if e.get("id") == args.id]
        if not hit:
            die("找不到 id=%s 的记录" % args.id, 4)
        rec = hit[-1]
    else:
        rec = sorted(events, key=lambda r: r.get("date", ""))[-1]

    print("复盘情绪事件 %s" % rec.get("id"))
    print("  日期：%s | 诱因：%s" % (rec.get("date"), rec.get("trigger")))
    print("  情绪：%s | 强度 %.0f/5 | 影响面：%s"
          % (rec.get("emotion"), float(rec.get("intensity") or 3), rec.get("impact")))
    if rec.get("thought"):
        print("  自动思维：%s" % rec["thought"])
    if rec.get("distortion"):
        lab = DISTORTIONS.get(rec["distortion"], rec["distortion"])
        print("  认知扭曲：%s" % lab)
        print("    → 跑 script --key %s 看怎么逐条反驳" % rec["distortion"])
    if rec.get("action"):
        print("  当时应对：%s" % rec["action"])
    if rec.get("relief") is not None:
        print("  缓解程度：%.0f/5" % float(rec["relief"]))
    return 0


def cmd_script(args, data):
    """按认知扭曲 key 给破局剧本。确定性查表，不生成自由文本。"""
    res = load_resource("soothe-scripts.json")
    if not res:
        die("剧本库缺失：resources/soothe-scripts.json", 4)
    frames = res.get("frames", [])
    key = args.key
    if key not in DISTORTIONS and key != "ineffective-coping" and key != "emotional-overload":
        # 允许用中文标签反查
        rev = {v: k for k, v in DISTORTIONS.items()}
        if key in rev:
            key = rev[key]
    hit = [f for f in frames if f.get("key") == key]
    if not hit:
        hit = [f for f in frames if key in (f.get("label", ""))]
    avail = "/".join(sorted(set(list(DISTORTIONS.keys()) + ["ineffective-coping", "emotional-overlap"])))
    if not hit:
        die("剧本库里没有 key=%s 的模板（可用：%s）" % (key, avail), 4)
    f = hit[0]
    print("认知破局剧本【%s】%s" % (f.get("label", ""), f.get("source", "")))
    for i, step in enumerate(f.get("steps", []), 1):
        print("  %d. %s" % (i, step))
    if f.get("sample"):
        print("  示例：%s" % f["sample"])
    if f.get("avoid"):
        print("  避免：%s" % f["avoid"])
    return 0


def cmd_risk(args, data):
    events = load_emotions(data)
    if not events:
        print("还没有情绪记录，无法扫描模式。先累计 5 次以上。")
        return 0
    s = compute_stats(events, args.days)
    if not s:
        print("近期没有落在 %d 天窗口内的情绪记录。" % args.days)
        return 0
    spots = weak_spots(s)
    print("情绪模式与风险扫描（近 %d 天，%d 次事件）：" % (s["window_days"], s["n"]))
    print("  平均强度 %.2f | 频率 %.2f 件/周 | 应对缓解 %.2f"
          % (s["avg_intensity"], s["freq_week"], s["avg_relief"] if s["avg_relief"] is not None else 0))
    if s["distortion_mode"]:
        print("  主导认知扭曲：%s（占 %.0f%%）"
              % (DISTORTIONS.get(s["distortion_mode"], s["distortion_mode"]), s["distortion_share"] * 100))
    print("  调节状态：%s" % PATTERNS.get(s["pattern"], s["pattern"]))
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
    events = load_emotions(data)
    if not events:
        print("还没有情绪记录。先记 5 次——包括你觉得自己「处理得不好」的那些，它们最说明问题。")
        return 0
    s = compute_stats(events, args.days)
    if not s:
        print("近期没有落在 %d 天窗口内的情绪记录。" % args.days)
        return 0
    spots = weak_spots(s)
    print("本周最值得练的一个：")
    if not spots:
        print("  情绪调节结构健康。下一步可以把已经验证有效的应对固定成你的「应急清单」。")
        return 0
    order = {"高": 0, "中": 1, "低": 2}
    spots.sort(key=lambda x: order.get(x[0], 9))
    sev, txt, act = spots[0]
    print("  [%s] %s" % (sev, txt))
    print("  → 行动：%s。" % act)
    if len(spots) > 1:
        print("  （另有 %d 项次要模式，跑 risk 看全部）" % (len(spots) - 1))
    if s["pattern"] in DISTORTIONS:
        print("  配套剧本：跑 script --key %s" % s["pattern"])
    elif s["pattern"] == "ineffective-coping":
        print("  配套剧本：跑 script --key ineffective-coping")
    elif s["pattern"] == "emotional-overload":
        print("  配套剧本：跑 script --key emotional-overlap")
    return 0


def cmd_report(args, data):
    events = load_emotions(data)
    if not events:
        print("还没有情绪记录，先记几笔再出报告。")
        return 0
    s = compute_stats(events, args.days)
    if not s:
        print("近期没有落在 %d 天窗口内的情绪记录。" % args.days)
        return 0
    L = []
    L.append("# 情绪调节复盘报告（%s）" % now_iso())
    L.append("")
    L.append("- 窗口：近 %d 天，%d 次情绪事件" % (s["window_days"], s["n"]))
    L.append("- 平均强度 %.2f / 5（趋势：%s） | 频率 %.2f 件/周 | 最长平静 %d 天"
             % (s["avg_intensity"], s["intensity_trend"], s["freq_week"], s["max_gap"]))
    L.append("- 最常见情绪：%s" % (s["top_emotion"] or "—"))
    if s["distortion_mode"]:
        L.append("- 主导认知扭曲：%s（占 %.0f%%）"
                 % (DISTORTIONS.get(s["distortion_mode"], s["distortion_mode"]), s["distortion_share"] * 100))
    if s["avg_relief"] is not None:
        L.append("- 应对平均缓解 %.2f / 5" % s["avg_relief"])
    if s["top_triggers"]:
        L.append("- 高频诱因：%s" % "、".join("%s(%d)" % (t, c) for t, c in s["top_triggers"]))
    L.append("- 调节状态：%s" % PATTERNS.get(s["pattern"], s["pattern"]))
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
    L.append("## 情绪事件清单")
    for e in sorted(events, key=lambda r: r.get("date", "")):
        dlab = DISTORTIONS.get(e.get("distortion"), e.get("distortion")) if e.get("distortion") else "—"
        rel = (" 缓解%s" % e["relief"]) if e.get("relief") is not None else ""
        L.append("- %s [%s] 强度%s 诱因=%s 扭曲=%s 影响=%s%s"
                 % (e.get("date"), e.get("emotion"), e.get("intensity"), e.get("trigger"),
                    dlab, e.get("impact"), rel))
    body = "\n".join(L) + "\n"
    print(body)
    fname = "soothe-%s.md" % date.today().isoformat()
    with open(os.path.join(data, "reports", fname), "w", encoding="utf-8") as f:
        f.write(body)
    print("报告已存：reports/%s" % fname)
    return 1 if any(x[0] in ("高", "中") for x in spots) else 0


# ------------------------- CLI -------------------------
def build_parser():
    p = argparse.ArgumentParser(prog="soothe.py", description="self-soothe-agent 情绪调节引擎")
    p.add_argument("--data", default="./my_soothe", help="数据目录")
    p.add_argument("--version", action="store_true")
    sub = p.add_subparsers(dest="cmd")

    a = sub.add_parser("set", help="设置情绪档案")
    a.add_argument("--name", default=None)
    a.add_argument("--focus", default=None, help="最常困扰的领域")
    a.add_argument("--goal", default=None, help="阶段目标")
    a.add_argument("--note", default="")

    a = sub.add_parser("log", help="记录一次情绪事件")
    a.add_argument("--date", default=date.today().isoformat())
    a.add_argument("--emotion", default="", help="情绪类型（必填，如 焦虑/愤怒/悲伤）")
    a.add_argument("--trigger", default="", help="诱因（发生了什么，必填）")
    a.add_argument("--intensity", default=None, help="强度 1-5（必填，1=轻微 5=失控）")
    a.add_argument("--thought", default="", help="自动思维/当时脑子里的话")
    a.add_argument("--distortion", default="", help="认知扭曲：" + "/".join(DISTORTIONS.keys()))
    a.add_argument("--action", default="", help="当时用了什么方式应对")
    a.add_argument("--relief", default=None, help="缓解程度 0-5（0=没用 5=完全平复，可选）")
    a.add_argument("--impact", default="无", help="影响面：" + "/".join(IMPACTS))
    a.add_argument("--id", default="", help="指定 id 可覆盖修正该条")

    for name, help_txt in (("trend", "情绪全景"), ("risk", "模式与风险扫描"),
                           ("plan", "本周最值得练的一个"), ("report", "完整报告")):
        sp = sub.add_parser(name, help=help_txt)
        sp.add_argument("--days", type=int, default=DEFAULT_WINDOW)

    a = sub.add_parser("review", help="单条复盘（拆诱因→情绪→扭曲→应对）")
    a.add_argument("--id", default="", help="留空复盘最近一次情绪事件")

    a = sub.add_parser("script", help="按认知扭曲拿破局剧本")
    a.add_argument("--key", default="all-or-nothing", help="认知扭曲 key（见 DISTORTIONS）")
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
    cmd_map = {"set": cmd_set, "log": cmd_log, "trend": cmd_trend, "review": cmd_review,
               "script": cmd_script, "risk": cmd_risk, "plan": cmd_plan, "report": cmd_report}
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
