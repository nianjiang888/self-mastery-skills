#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
self-communicate-agent 真引擎
================================

把「话说错了」这件模糊的懊恼，拆成可记录、可计算、可复核的指标：
记录每次重要对话 → 量化达成率/防御率/情绪代价/关系账户 → 复盘卡在哪一层
（事实层/情绪层/身份层）→ 识别反复模式 → 给下次该怎么说。

服务对象是「用 AI 的人」本人——那个话说出口就后悔、跟最亲的人反而吵得最凶
、每次都想着重来一次我该怎么说的你。

设计原则（与 self 系列一致）：
- 纯标准库，确定性、可重跑；
- 留实物证据：events.jsonl（按 type+id 幂等覆盖）+ profile.json + reports/comm-<日期>.md；
- 退出码：0 正常 / 1 需关注（中或高严重度）/ 2 用法错误 / 4 参数或数据不可用。

注意：这是「前哨」工具，不做心理治疗、不做临床诊断。
"""

import os
import sys
import json
import argparse
from datetime import datetime, date, timedelta

ENGINE_VERSION = "2.0.0"

DEFAULT_WINDOW = 30

# 严重度阈值
WEAK_DEFENSE_RATE = 40.0    # 场景防御率高于此 = 中
WEAK_EMOTION_COST = -1.0    # 情绪代价低于此 = 中（高情绪明显拖累结果）
WEAK_LISTENED = 2.5         # 倾听分低于此 = 中
WEAK_SCENE_OUTCOME = 2.5    # 最弱场景达成低于此 = 中
WEAK_IDENTITY_RATE = 40.0   # 身份层占比高于此 = 高
WEAK_CONFRONT_RATE = 20.0   # 对抗率高于此 = 高
WEAK_SCRIPT_RATE = 30.0     # 话术沉淀率低于此 = 低
MIN_RECORDS_FOR_PATTERN = 5 # 少于此条不做模式判定（样本不足）
MIN_SCENE_N = 2             # 场景样本下限

SCENES = ["谈判", "汇报", "请求", "反馈", "冲突", "日常", "亲密"]
COUNTERPARTS = ["上级", "客户", "同事", "家人", "朋友", "陌生人"]
GOALS = ["达成", "关系", "信息", "情绪"]
REACTIONS = ["合作", "中立", "防御", "对抗"]
LAYERS = ["事实", "情绪", "身份"]

HIGH_TONE = 7   # 情绪强度分界


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
    return [r for r in _load_all(data) if r.get("type") == "comm"]


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
def infer_layer(rec):
    """推断这次对话卡在三层里的哪一层。

    Stone/Patton/Heen《困难对话》：绝大多数谈不拢不是因为事实没说清，
    而是情绪没被接住，或者身份（面子/自我形象）受到了威胁。
    优先级：身份 > 情绪 > 事实。
    """
    if rec.get("layer"):
        return rec["layer"]
    aftermath = float(rec.get("aftermath") or 0)
    outcome = float(rec.get("outcome") or 3)
    tone = float(rec.get("tone") or 1)
    if aftermath <= -1 and outcome <= 2:
        return "身份"
    if tone >= HIGH_TONE:
        return "情绪"
    return "事实"


def _mean(vals):
    return sum(vals) / len(vals) if vals else 0.0


def _rate(part, total):
    return round(part / total * 100, 1) if total else 0.0


def _group_stats(recs, key):
    """按字段分组统计：次数 / 平均达成 / 防御率 / 平均关系变化。"""
    groups = {}
    for r in recs:
        k = r.get(key) or "未填"
        groups.setdefault(k, []).append(r)
    out = []
    for k, rs in groups.items():
        outs = [float(x.get("outcome") or 3) for x in rs]
        defe = len([x for x in rs if x.get("reaction") in ("防御", "对抗")])
        aft = [float(x.get("aftermath") or 0) for x in rs]
        out.append({
            "key": k,
            "n": len(rs),
            "outcome": round(_mean(outs), 2),
            "defense_rate": _rate(defe, len(rs)),
            "aftermath": round(_mean(aft), 2),
        })
    out.sort(key=lambda x: x["outcome"])
    return out


def compute_stats(recs, days):
    if not recs:
        return None
    win = recent(recs, days)
    if not win:
        return None
    n = len(win)
    outs = [float(r.get("outcome") or 3) for r in win]
    tones = [float(r.get("tone") or 1) for r in win]
    listens = [float(r.get("listened") or 3) for r in win]
    afters = [float(r.get("aftermath") or 0) for r in win]

    defense = len([r for r in win if r.get("reaction") in ("防御", "对抗")])
    confront = len([r for r in win if r.get("reaction") == "对抗"])
    high_tone = len([r for r in win if float(r.get("tone") or 1) >= HIGH_TONE])

    layers = [infer_layer(r) for r in win]
    identity = len([x for x in layers if x == "身份"])

    # 情绪代价：高情绪组平均达成 - 低情绪组平均达成（负=情绪拖累）
    hi = [float(r.get("outcome") or 3) for r in win if float(r.get("tone") or 1) >= HIGH_TONE]
    lo = [float(r.get("outcome") or 3) for r in win if float(r.get("tone") or 1) < HIGH_TONE]
    if len(hi) >= 1 and len(lo) >= 1:
        emotion_cost = round(_mean(hi) - _mean(lo), 2)
    else:
        emotion_cost = None

    scripted = len([r for r in win if (r.get("better") or "").strip()])

    scene_stats = _group_stats(win, "scene")
    relation_stats = _group_stats(win, "counterpart")
    weakest = [x for x in scene_stats if x["n"] >= MIN_SCENE_N]
    weakest_scene = weakest[0] if weakest else None
    worst_relation = relation_stats[0] if relation_stats else None

    return {
        "window_days": days,
        "n_records": n,
        "avg_outcome": round(_mean(outs), 2),
        "defense_rate": _rate(defense, n),
        "confront_rate": _rate(confront, n),
        "avg_tone": round(_mean(tones), 2),
        "high_tone_rate": _rate(high_tone, n),
        "avg_listened": round(_mean(listens), 2),
        "avg_aftermath": round(_mean(afters), 2),
        "identity_rate": _rate(identity, n),
        "emotion_cost": emotion_cost,
        "script_rate": _rate(scripted, n),
        "scene_stats": scene_stats,
        "relation_stats": relation_stats,
        "weakest_scene": weakest_scene,
        "worst_relation": worst_relation,
    }


def weak_spots(s):
    """返回 [(严重度, 文案, 行动建议)]。行动与弱项强制同源。"""
    if not s:
        return []
    spots = []
    n = s["n_records"]
    thin = n < MIN_RECORDS_FOR_PATTERN

    if s["avg_aftermath"] < 0:
        spots.append(("高", "关系账户平均 %.2f（负），对话在持续消耗关系" % s["avg_aftermath"],
                      "接下来一周只做一件事：任何对话结束后加一句关系修复（先认可对方这个人，再谈事）"))

    if s["confront_rate"] >= WEAK_CONFRONT_RATE:
        spots.append(("高", "对抗率 %.1f%%（≥%.0f%%），四分之一的对话把对方推到了对立面" % (s["confront_rate"], WEAK_CONFRONT_RATE),
                      "冲突前先做三步降温：说事实不带评判、承认对方情绪、把立场换成利益再谈"))

    if s["identity_rate"] >= WEAK_IDENTITY_RATE and not thin:
        spots.append(("高", "身份层冲突占 %.1f%%（≥%.0f%%），多数谈崩不是事没说清，是面子被碰了" % (s["identity_rate"], WEAK_IDENTITY_RATE),
                      "说话前先问自己：这句话会让对方觉得自己被否定吗？把「你不对」换成「我的理解是」"))

    if s["emotion_cost"] is not None and s["emotion_cost"] <= WEAK_EMOTION_COST:
        spots.append(("中", "情绪代价 %.2f 分：情绪上头时达成率明显更低" % s["emotion_cost"],
                      "给自己定一条硬规则：情绪强度到 7 就暂停，改约时间，不在上头时谈重要的事"))

    if s["avg_listened"] < WEAK_LISTENED:
        spots.append(("中", "倾听分 %.2f（<%.1f），说得多、听得少" % (s["avg_listened"], WEAK_LISTENED),
                      "练一个动作：对方说完先复述一遍他的意思，确认对了再表达自己"))

    if s["defense_rate"] >= WEAK_DEFENSE_RATE and not thin:
        spots.append(("中", "整体防御率 %.1f%%（≥%.0f%%），对方经常进入防御状态" % (s["defense_rate"], WEAK_DEFENSE_RATE),
                      "把陈述句改成问句，把「我认为」改成「你怎么看」，降低威胁感（SCARF 模型）"))

    ws = s["weakest_scene"]
    if ws and ws["outcome"] <= WEAK_SCENE_OUTCOME:
        spots.append(("中", "最弱场景是「%s」：%d 次平均达成仅 %.2f" % (ws["key"], ws["n"], ws["outcome"]),
                      "针对「%s」单独准备话术模板，跑 script --scene %s 拿结构化的说法" % (ws["key"], ws["key"])))

    wr = s["worst_relation"]
    if wr and wr["n"] >= MIN_SCENE_N and wr["aftermath"] < 0:
        spots.append(("中", "和「%s」的对话后关系平均 %.2f（负），这段关系在被消耗" % (wr["key"], wr["aftermath"]),
                      "下一次和「%s」的对话，目标只设成为「关系」而不是「达成」，先修复再谈事" % wr["key"]))

    if thin:
        spots.append(("低", "只有 %d 条记录（<%d），模式判定暂不可靠" % (n, MIN_RECORDS_FOR_PATTERN),
                      "继续记录到 %d 条以上，模式识别才有统计意义" % MIN_RECORDS_FOR_PATTERN))
    elif s["script_rate"] < WEAK_SCRIPT_RATE:
        spots.append(("低", "话术沉淀率 %.1f%%（<%.0f%%），复盘了但没留下下次怎么说" % (s["script_rate"], WEAK_SCRIPT_RATE),
                      "每次复盘至少写一句「下次我想这么说」，攒成你自己的话术库"))

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
    if args.focus_scene is not None:
        prof["focus_scene"] = args.focus_scene
    if args.focus_relation is not None:
        prof["focus_relation"] = args.focus_relation
    if args.target_outcome is not None:
        prof["target_outcome"] = args.target_outcome
    if args.note:
        prof["note"] = args.note
    if not prof:
        print("没有需要更新的字段。可用：--focus_scene --focus_relation --target_outcome --note")
        return 0
    save_profile(data, prof)
    print("已更新沟通档案：%s" % json.dumps(prof, ensure_ascii=False))
    return 0


def cmd_log(args, data):
    if not args.date:
        die("log 需要 --date", 4)
    if args.outcome is None:
        die("log 需要 --outcome（结果满意度 1-5）", 4)
    try:
        outcome = float(args.outcome)
    except (TypeError, ValueError):
        die("outcome 必须是 1-5 的数字", 4)
    if not (1 <= outcome <= 5):
        die("outcome 必须在 1-5 之间（1=很糟 5=很好）", 4)
    if args.tone is not None and not (1 <= float(args.tone) <= 10):
        die("tone 必须在 1-10 之间", 4)
    if args.listened is not None and not (1 <= float(args.listened) <= 5):
        die("listened 必须在 1-5 之间", 4)
    if args.aftermath is not None and not (-2 <= float(args.aftermath) <= 2):
        die("aftermath 必须在 -2 到 2 之间（-2=关系明显变差 2=明显变好）", 4)

    recs = load_events(data)
    if args.id:
        rid = args.id
    else:
        same_day = [r for r in recs if r.get("date") == args.date]
        rid = "%s#%d" % (args.date, len(same_day) + 1)
    rec = {
        "type": "comm",
        "id": rid,
        "date": args.date,
        "scene": args.scene,
        "counterpart": args.counterpart,
        "goal": args.goal,
        "tone": float(args.tone) if args.tone is not None else 1.0,
        "listened": float(args.listened) if args.listened is not None else 3.0,
        "reaction": args.reaction,
        "outcome": outcome,
        "aftermath": float(args.aftermath) if args.aftermath is not None else 0.0,
        "layer": args.layer or "",
        "words": args.words or "",
        "better": args.better or "",
    }
    append_event(data, rec)
    layer = infer_layer(rec)
    print("已记录 %s [%s/%s] 达成 %.0f 对方%s 关系%+d → 卡在「%s」层 id=%s"
          % (args.date, args.scene, args.counterpart, outcome, args.reaction,
             int(rec["aftermath"]), layer, rid))
    if layer == "身份":
        print("  提示：这一层最难谈。问题不在事情本身，在面子/自我形象。")
    elif layer == "情绪":
        print("  提示：情绪强度 %d，属于上头状态。当时谈重要的事，达成率通常偏低。" % int(rec["tone"]))
    return 0


def cmd_trend(args, data):
    recs = load_events(data)
    if not recs:
        print("还没有对话记录。先记一次：")
        print('  python scripts/comm.py --data ./my_comm log --scene 冲突 --counterpart 家人 --outcome 2 --reaction 防御 --tone 8')
        return 0
    s = compute_stats(recs, args.days)
    if not s:
        print("近期没有落在 %d 天窗口内的记录。" % args.days)
        return 0
    print("近 %d 天沟通概览（%d 条记录）：" % (s["window_days"], s["n_records"]))
    print("  平均达成 %.2f / 5 | 防御率 %.1f%% | 对抗率 %.1f%%"
          % (s["avg_outcome"], s["defense_rate"], s["confront_rate"]))
    print("  情绪强度均值 %.2f / 10（高强度占比 %.1f%%） | 倾听分 %.2f / 5"
          % (s["avg_tone"], s["high_tone_rate"], s["avg_listened"]))
    print("  关系账户 %+.2f（-2 最差 +2 最好）| 身份层冲突占比 %.1f%%"
          % (s["avg_aftermath"], s["identity_rate"]))
    if s["emotion_cost"] is not None:
        tag = "情绪拖累结果" if s["emotion_cost"] < 0 else ("情绪无拖累" if s["emotion_cost"] == 0 else "高情绪反而更好")
        print("  情绪代价 %+.2f 分（高情绪组达成 − 低情绪组达成）：%s" % (s["emotion_cost"], tag))
    if s["scene_stats"]:
        print("  分场景达成：" + "，".join("%s %.2f(%d次)" % (x["key"], x["outcome"], x["n"])
                                          for x in s["scene_stats"]))
    if s["relation_stats"]:
        print("  分对象关系：" + "，".join("%s %+.2f(%d次)" % (x["key"], x["aftermath"], x["n"])
                                          for x in s["relation_stats"]))
    return 0


def cmd_review(args, data):
    """单条复盘：拆三层 + 给替换说法。"""
    recs = load_events(data)
    if not recs:
        print("还没有对话记录，先用 log 记一次。")
        return 0
    if args.id:
        hit = [r for r in recs if r.get("id") == args.id]
        if not hit:
            die("找不到 id=%s 的记录" % args.id, 4)
        rec = hit[-1]
    else:
        rec = recs[-1]
    layer = infer_layer(rec)
    print("复盘 %s  [%s × %s]" % (rec.get("id"), rec.get("scene"), rec.get("counterpart")))
    print("  目标：%s | 结果满意度 %.0f/5 | 对方反应：%s" % (rec.get("goal"), float(rec.get("outcome") or 3), rec.get("reaction")))
    print("  我当时情绪 %d/10 | 倾听 %d/5 | 事后关系 %+d" % (
        int(float(rec.get("tone") or 1)), int(float(rec.get("listened") or 3)), int(float(rec.get("aftermath") or 0))))
    if rec.get("words"):
        print("  原话：%s" % rec["words"])
    print("")
    print("  卡在哪一层：%s" % layer)
    if layer == "身份":
        print("    → 这是最硬的一层。对方不是不同意你的事实，而是觉得「我这个人被否定了」。")
        print("    → 换法：把「你不对」换成「我的理解是…你看是不是这样」；先肯定对方的出发点，再谈分歧。")
    elif layer == "情绪":
        print("    → 情绪劫持了理性。事实其实没那么复杂，是当时的火气把对话带偏了。")
        print("    → 换法：先给情绪命名（「我看你现在挺着急的」），情绪被接住了才谈得下去。")
    else:
        print("    → 事实层问题，相对好解决。多半是信息不对称或方案没说清。")
        print("    → 换法：把结论前置，先说要什么，再给理由；补一个具体的时间/数字。")
    if rec.get("better"):
        print("  你当时想到的更好说法：%s" % rec["better"])
    else:
        print("  还没写下「下次怎么说」。补一句：")
        print('    python scripts/comm.py --data <目录> log --id %s --date %s --scene %s --counterpart %s '
              '--outcome %s --reaction %s --better "下次我想这么说：..."'
              % (rec.get("id"), rec.get("date"), rec.get("scene"), rec.get("counterpart"),
                 rec.get("outcome"), rec.get("reaction")))
    return 0


def cmd_script(args, data):
    """按场景 + 目标给结构化话术。确定性查表，不生成自由文本。"""
    res = load_resource("communication-scripts.json")
    if not res:
        die("话术库缺失：resources/communication-scripts.json", 4)
    scene = args.scene
    goal = args.goal
    frames = res.get("frames", [])
    hit = [f for f in frames if scene in f.get("scenes", []) and goal in f.get("goals", [])]
    if not hit:
        hit = [f for f in frames if scene in f.get("scenes", [])]
    if not hit:
        hit = [f for f in frames if "通用" in f.get("scenes", [])]
    if not hit:
        die("话术库里没有适配场景「%s」的模板" % scene, 4)

    # 命中过多会让人无从下手：按 priority 排序后最多给 3 套
    hit.sort(key=lambda f: f.get("priority", 99))
    TOPN = 3
    shown = hit[:TOPN]
    print("场景「%s」× 目标「%s」的话术模板（共命中 %d 套，取最适的 %d 套）："
          % (scene, goal, len(hit), len(shown)))
    for f in shown:
        print("")
        print("【%s】%s" % (f.get("name", ""), f.get("source", "")))
        for i, step in enumerate(f.get("steps", []), 1):
            print("  %d. %s" % (i, step))
        if f.get("sample"):
            print("  示例：%s" % f["sample"])
        if f.get("avoid"):
            print("  避免：%s" % f["avoid"])
    return 0


def cmd_risk(args, data):
    recs = load_events(data)
    if not recs:
        print("还没有对话记录，无法扫描模式。先累计 5 次以上。")
        return 0
    s = compute_stats(recs, args.days)
    if not s:
        print("近期没有落在 %d 天窗口内的记录。" % args.days)
        return 0
    spots = weak_spots(s)
    print("沟通风险与模式扫描（近 %d 天，%d 条）：" % (s["window_days"], s["n_records"]))
    print("  平均达成 %.2f | 防御率 %.1f%% | 关系账户 %+.2f | 倾听 %.2f"
          % (s["avg_outcome"], s["defense_rate"], s["avg_aftermath"], s["avg_listened"]))
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
    recs = load_events(data)
    if not recs:
        print("还没有对话记录。先记 5 次重要对话——包括谈崩的那些，它们信息量最大。")
        return 0
    s = compute_stats(recs, args.days)
    if not s:
        print("近期没有落在 %d 天窗口内的记录。" % args.days)
        return 0
    spots = weak_spots(s)
    print("本周最值得练的一个：")
    if not spots:
        print("  沟通结构健康。下一步可以把已经验证有效的话术固定下来，攒成你自己的话术库。")
        return 0
    order = {"高": 0, "中": 1, "低": 2}
    spots.sort(key=lambda x: order.get(x[0], 9))
    sev, txt, act = spots[0]
    print("  [%s] %s" % (sev, txt))
    print("  → 行动：%s。" % act)
    if len(spots) > 1:
        print("  （另有 %d 项次要模式，跑 risk 看全部）" % (len(spots) - 1))
    ws = s["weakest_scene"]
    if ws and sev in ("高", "中"):
        print("  配套：跑 script --scene %s --goal 关系 拿结构化说法" % ws["key"])
    return 0


def cmd_report(args, data):
    recs = load_events(data)
    if not recs:
        print("还没有对话记录，先记几笔再出报告。")
        return 0
    s = compute_stats(recs, args.days)
    if not s:
        print("近期没有落在 %d 天窗口内的记录。" % args.days)
        return 0
    L = []
    L.append("# 沟通复盘报告（%s）" % now_iso())
    L.append("")
    L.append("- 窗口：近 %d 天，%d 条记录" % (s["window_days"], s["n_records"]))
    L.append("- 平均达成 %.2f / 5 | 防御率 %.1f%% | 对抗率 %.1f%%"
             % (s["avg_outcome"], s["defense_rate"], s["confront_rate"]))
    L.append("- 情绪强度均值 %.2f / 10（高强度占比 %.1f%%） | 倾听分 %.2f / 5"
             % (s["avg_tone"], s["high_tone_rate"], s["avg_listened"]))
    L.append("- 关系账户 %+.2f | 身份层冲突占比 %.1f%%" % (s["avg_aftermath"], s["identity_rate"]))
    if s["emotion_cost"] is not None:
        L.append("- 情绪代价 %+.2f 分（高情绪组达成 − 低情绪组达成）" % s["emotion_cost"])
    if s["scene_stats"]:
        L.append("- 分场景达成：" + "，".join("%s %.2f(%d次)" % (x["key"], x["outcome"], x["n"])
                                             for x in s["scene_stats"]))
    if s["relation_stats"]:
        L.append("- 分对象关系：" + "，".join("%s %+.2f(%d次)" % (x["key"], x["aftermath"], x["n"])
                                              for x in s["relation_stats"]))
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
    L.append("## 逐条记录")
    for r in recs:
        L.append("- %s [%s × %s] 达成%s 对方%s 关系%+d 层=%s %s"
                 % (r.get("date"), r.get("scene"), r.get("counterpart"),
                    r.get("outcome"), r.get("reaction"), int(float(r.get("aftermath") or 0)),
                    infer_layer(r), ("| " + r.get("better")) if r.get("better") else ""))
    body = "\n".join(L) + "\n"
    print(body)
    fname = "comm-%s.md" % date.today().isoformat()
    with open(os.path.join(data, "reports", fname), "w", encoding="utf-8") as f:
        f.write(body)
    print("报告已存：reports/%s" % fname)
    return 1 if any(x[0] in ("高", "中") for x in spots) else 0


# ------------------------- CLI -------------------------
def build_parser():
    p = argparse.ArgumentParser(prog="comm.py", description="self-communicate-agent 沟通引擎")
    p.add_argument("--data", default="./my_comm", help="数据目录")
    p.add_argument("--version", action="store_true")
    sub = p.add_subparsers(dest="cmd")

    a = sub.add_parser("set", help="设置沟通档案")
    a.add_argument("--focus_scene", default=None)
    a.add_argument("--focus_relation", default=None)
    a.add_argument("--target_outcome", type=float, default=None)
    a.add_argument("--note", default="")

    a = sub.add_parser("log", help="记一次重要对话")
    a.add_argument("--date", default=date.today().isoformat())
    a.add_argument("--scene", default="日常", choices=SCENES)
    a.add_argument("--counterpart", default="同事", choices=COUNTERPARTS)
    a.add_argument("--goal", default="达成", choices=GOALS)
    a.add_argument("--tone", type=float, default=None, help="我的情绪强度 1-10")
    a.add_argument("--listened", type=float, default=None, help="我的倾听程度 1-5")
    a.add_argument("--reaction", default="中立", choices=REACTIONS)
    a.add_argument("--outcome", default=None, help="结果满意度 1-5（必填）")
    a.add_argument("--aftermath", type=float, default=None, help="事后关系变化 -2..2")
    a.add_argument("--layer", default="", choices=[""] + LAYERS, help="留空由引擎推断")
    a.add_argument("--words", default="", help="我当时说了什么")
    a.add_argument("--better", default="", help="下次我想怎么说")
    a.add_argument("--id", default="", help="指定 id 可覆盖修正该条")

    for name, help_txt in (("trend", "沟通全景"), ("risk", "模式与风险扫描"),
                           ("plan", "本周最值得练的一个"), ("report", "完整报告")):
        sp = sub.add_parser(name, help=help_txt)
        sp.add_argument("--days", type=int, default=DEFAULT_WINDOW)

    a = sub.add_parser("review", help="单条复盘（拆三层）")
    a.add_argument("--id", default="", help="留空复盘最近一条")

    a = sub.add_parser("script", help="按场景拿结构化话术")
    a.add_argument("--scene", default="日常", choices=SCENES)
    a.add_argument("--goal", default="达成", choices=GOALS)
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
               "review": cmd_review, "script": cmd_script,
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
