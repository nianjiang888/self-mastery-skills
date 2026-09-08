#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
self-reflect-agent · 反省引擎 v2.0.0

日三省：把每一次"发生了什么 / 我怎么反应 / 结果如何"沉淀成可重跑的日志，
再跨时间识别「思维惯性」与「言行盲点」，用双环学习把改进行动推到根因层。

子命令
  log        记录一条反省条目（情境/反应/结果/情绪），自动抽标签、打时间戳
  pattern    跨时间模式识别：哪些标签/情绪反复出现 -> 思维惯性
  blindspot  言行盲点：对照你"自称重视"的事，日志里是否真的出现（言行 gap）
  aar        对单条事件做美国陆军式四问复盘（本该/实际/差异/下次）
  claim      登记你"自称重视"的价值或"想改掉"的行为，供 blindspot 比对
  report     生成周期性反省报告（markdown，含模式热力与双环学习建议）

退出码
  0  正常
  1  发现需关注的反复模式（如破坏性惯性、长期言行 gap）
  4  触发双环学习警报（根因级盲点：自称与实践系统性背离）
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta

DEFAULT_STORE = ".self-reflect"
EVENT_VERSION = "2.0.0"

EMOTION_LEXICON = {
    "焦虑": ["焦虑", "紧张", "慌", "不安", "担心", "害怕", "压力", "慌张", "着急", "坐不住"],
    "愤怒": ["愤怒", "生气", "发火", "发飙", "恼火", "火大", "憋屈", "烦躁", "恨", "怒"],
    "低落": ["低落", "沮丧", "难过", "失落", "抑郁", "空虚", "无力", "丧", "心累"],
    "平静": ["平静", "安心", "放松", "坦然", "从容", "稳", "舒坦"],
    "兴奋": ["兴奋", "激动", "开心", "高兴", "雀跃", "期待", "爽"],
    "羞耻": ["羞耻", "丢脸", "尴尬", "愧疚", "自责", "后悔", "悔", "惭愧"],
}

# 中文精选词库：覆盖自我管理常见域，命中即作为干净标签（避免按字切分的噪声）
CURATED_CN = [
    "拖延", "熬夜", "焦虑", "发火", "愤怒", "逃避", "甩锅", "内耗", "比较", "完美主义",
    "社恐", "冲动消费", "暴食", "暴饮", "专注", "分心", "健身", "跑步", "读书", "写作",
    "储蓄", "消费", "记账", "沟通", "倾听", "表达", "情绪", "自律", "习惯", "决策",
    "学习", "睡眠", "创作", "安抚", "复盘", "计划", "拖延症", "摸鱼", "躺平", "加班",
]

DESTRUCTIVE_HINTS = ["发火", "摔", "骂", "逃避", "拖延", "熬夜", "暴食", "暴饮", "冲动消费", "quit", "放弃", "甩锅", "摸鱼", "躺平"]


# ----------------------------------------------------------------------------
# 存储与 IO
# ----------------------------------------------------------------------------
def store_path(store):
    return store


def log_file(store):
    return os.path.join(store, "reflect-log.jsonl")


def claims_file(store):
    return os.path.join(store, "claims.json")


def ensure_store(store):
    os.makedirs(store, exist_ok=True)


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_log(store):
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
    path = log_file(store)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_claims(store):
    path = claims_file(store)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_claims(store, claims):
    ensure_store(store)
    with open(claims_file(store), "w", encoding="utf-8") as f:
        json.dump(claims, f, ensure_ascii=False, indent=2)


# ----------------------------------------------------------------------------
# 标签抽取（无外部依赖，CJK 二元组 + 拉丁词）
# ----------------------------------------------------------------------------
def extract_tags(text, explicit=None):
    tags = []
    if explicit:
        tags.extend([t.strip() for t in explicit if t.strip()])
    # 中文精选词库命中（干净标签，避免按字切分的噪声）
    for phrase in CURATED_CN:
        if phrase in text:
            tags.append(phrase)
    # 拉丁词
    latin = re.findall(r"[A-Za-z]{2,}", text.lower())
    tags.extend(latin)
    # 去重保序
    seen = set()
    out = []
    for t in tags:
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def detect_emotion(text):
    found = []
    for emo, lex in EMOTION_LEXICON.items():
        if any(w in text for w in lex):
            found.append(emo)
    return found or ["未标注"]


# ----------------------------------------------------------------------------
# 子命令：log
# ----------------------------------------------------------------------------
def cmd_log(args):
    situation = (args.situation or "").strip()
    reaction = (args.reaction or "").strip()
    outcome = (args.outcome or "").strip()
    emotion_input = (args.emotion or "").strip()
    if not situation and not reaction:
        print("错误：至少提供 --situation 或 --reaction 之一", file=sys.stderr)
        return 2

    full_text = " ".join([situation, reaction, outcome])
    tags = extract_tags(full_text, args.tags)
    emotion = [e.strip() for e in emotion_input.split(",")] if emotion_input else detect_emotion(full_text)

    entry = {
        "ts": now_iso(),
        "id": "r%d" % (len(load_log(args.store)) + 1),
        "situation": situation,
        "reaction": reaction,
        "outcome": outcome,
        "emotion": emotion,
        "tags": tags[:12],
        "version": EVENT_VERSION,
    }
    append_entry(args.store, entry)
    print("已记录反省条目 %s，抽取标签：%s" % (entry["id"], "、".join(entry["tags"][:8]) or "（无）"))
    print("检测到情绪：%s" % "、".join(emotion))
    return 0


# ----------------------------------------------------------------------------
# 子命令：pattern（跨时间模式识别）
# ----------------------------------------------------------------------------
def cmd_pattern(args):
    entries = load_log(args.store)
    if len(entries) < 2:
        print("日志条目不足（需≥2），暂无法识别模式。先多用 `log` 记录。")
        return 0

    # 按天聚合标签与情绪
    day_tags = defaultdict(set)
    tag_total = Counter()
    emo_total = Counter()
    destructive_hits = 0
    for e in entries:
        day = e["ts"][:10]
        for t in e.get("tags", []):
            day_tags[day].add(t)
            tag_total[t] += 1
        for emo in e.get("emotion", []):
            emo_total[emo] += 1
        blob = (e.get("reaction", "") + e.get("situation", "")).lower()
        if any(h in blob for h in DESTRUCTIVE_HINTS):
            destructive_hits += 1

    distinct_days = len(day_tags)
    threshold = max(2, args.min_days)
    # 惯性：出现在 >= threshold 个不同日期的标签
    inertia = []
    for tag, cnt in tag_total.items():
        days_seen = sum(1 for d in day_tags if tag in day_tags[d])
        if days_seen >= threshold:
            inertia.append((tag, days_seen, cnt))
    inertia.sort(key=lambda x: (-x[1], -x[2]))

    top_emo = emo_total.most_common(3)

    lines = []
    lines.append("# 思维惯性模式报告")
    lines.append("")
    lines.append("- 生成时间：%s" % now_iso())
    lines.append("- 分析样本：%d 条反省，覆盖 %d 个不同日期" % (len(entries), distinct_days))
    lines.append("- 识别阈值：同一标签出现在 ≥ %d 天即记为「惯性」" % threshold)
    lines.append("")
    lines.append("## 一、反复出现的思维/行为惯性")
    if inertia:
        for tag, days, cnt in inertia:
            lines.append("- **%s**：出现在 %d 天，累计 %d 次" % (tag, days, cnt))
    else:
        lines.append("- 暂未发现跨天惯性模式。")
    lines.append("")
    lines.append("## 二、情绪基调分布")
    if top_emo:
        for emo, c in top_emo:
            lines.append("- %s：%d 次" % (emo, c))
    lines.append("")
    lines.append("## 三、破坏性惯性预警")
    if destructive_hits > 0:
        lines.append("- 检测到 %d 条含破坏性线索（发火/逃避/拖延/冲动等），建议优先做双环复盘。" % destructive_hits)
        lines.append("- 注：这通常是「单环学习」改不掉的根因信号，需要追问『我为什么总这样』而非『下次怎么忍住』。")
    else:
        lines.append("- 未检测到明显破坏性惯性。")

    report = "\n".join(lines) + "\n"
    ensure_store(args.store)
    rep_path = os.path.join(args.store, "pattern-report.md")
    with open(rep_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print("报告已写入：%s" % rep_path)

    # 退出码：存在破坏性惯性 -> 1（需关注）
    if destructive_hits > 0 and any(days >= max(threshold, 3) for _, days, _ in inertia):
        return 1
    return 0


# ----------------------------------------------------------------------------
# 子命令：claim（登记自称重视/想改）
# ----------------------------------------------------------------------------
def cmd_claim(args):
    claims = load_claims(args.store)
    text = args.text.strip()
    # 去重：同 kind + 同 text 不重复登记
    if any(c["kind"] == args.kind and c["text"] == text for c in claims):
        print("已存在相同登记，跳过：%s" % text)
        return 0
    claims.append({
        "ts": now_iso(),
        "text": text,
        "kind": args.kind,  # value=重视的价值 / avoid=想改掉的行为
    })
    save_claims(args.store, claims)
    print("已登记%s：%s" % ("价值" if args.kind == "value" else "待改行为", text))
    return 0


# ----------------------------------------------------------------------------
# 子命令：blindspot（言行盲点）
# ----------------------------------------------------------------------------
def cmd_blindspot(args):
    entries = load_log(args.store)
    claims = load_claims(args.store)
    if not claims:
        print("尚未登记任何 claim。先用 `claim --kind value/avoid --text ...` 登记你自称重视/想改的事。")
        return 0
    if not entries:
        print("尚无反省日志，无法比对。")
        return 0

    # 全量文本与标签
    all_text = " ".join(
        e.get("situation", "") + e.get("reaction", "") + e.get("outcome", "")
        for e in entries
    ).lower()
    all_tags = set()
    for e in entries:
        all_tags.update(t.lower() for t in e.get("tags", []))

    gaps = []
    for c in claims:
        text = c["text"].strip()
        kind = c["kind"]
        # 命中：claim 文本中任一 2 字以上片段出现在日志
        hit = False
        for frag in re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z]{2,}", text.lower()):
            if len(frag) >= 2 and (frag in all_text or frag in all_tags):
                hit = True
                break
        if kind == "value" and not hit:
            gaps.append(("言行 gap", text, "自称重视，但日志中几乎未出现相关实践"))
        elif kind == "avoid" and hit:
            gaps.append(("反复失守", text, "想改掉，但日志中仍反复出现该行为"))

    lines = []
    lines.append("# 言行盲点报告")
    lines.append("")
    lines.append("- 生成时间：%s" % now_iso())
    lines.append("- 比对：%d 条 claim vs %d 条反省日志" % (len(claims), len(entries)))
    lines.append("")
    if gaps:
        lines.append("## 发现的盲点")
        for gtype, text, desc in gaps:
            lines.append("- **[%s] %s**：%s" % (gtype, text, desc))
        lines.append("")
        lines.append("> 盲点是双环学习的入口：它说明你的『自我叙事』与『实际行为』系统性背离，")
        lines.append("> 单靠『下次注意』无效，需要改的是背后的前提假设（为什么重视却不做 / 为什么想改却改不掉）。")
    else:
        lines.append("## 暂未发现系统性盲点")
        lines.append("已登记的价值均有实践痕迹，想改的行为也未见反复。保持记录以持续验证。")

    report = "\n".join(lines) + "\n"
    ensure_store(args.store)
    bs_path = os.path.join(args.store, "blindspot-report.md")
    with open(bs_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print("报告已写入：%s" % bs_path)

    # 退出码：存在盲点 -> 1；多条根因级盲点 -> 4（双环警报）
    if not gaps:
        return 0
    return 4 if len(gaps) >= 2 else 1


# ----------------------------------------------------------------------------
# 子命令：aar（四问复盘）
# ----------------------------------------------------------------------------
def cmd_aar(args):
    entries = load_log(args.store)
    if not entries:
        print("尚无反省日志。")
        return 0
    if args.id:
        target = next((e for e in entries if e.get("id") == args.id), None)
    else:
        target = entries[-1]
    if not target:
        print("未找到条目 %s" % args.id)
        return 2

    sit = target.get("situation", "")
    react = target.get("reaction", "")
    out = target.get("outcome", "")

    lines = []
    lines.append("# 四问复盘 · %s" % target.get("id", "?"))
    lines.append("")
    lines.append("**原始情境**：%s" % sit)
    lines.append("**我的反应**：%s" % react)
    lines.append("**实际结果**：%s" % out)
    lines.append("")
    lines.append("## 美国陆军 AAR 四问")
    lines.append("1. **本该发生什么？**（预期）")
    lines.append("   - 清空白处，写下你事前期待的结果与自己的判断前提。")
    lines.append("2. **实际发生了什么？**（事实）")
    lines.append("   - 对照上方「实际结果」，只陈述可观察事实，不辩解。")
    lines.append("3. **为什么有差异？**（根因，双环）")
    lines.append("   - 不止问『下次怎么忍住』，要问『是什么前提假设让我总这样反应』。")
    lines.append("4. **下次怎么改？**（行动）")
    lines.append("   - 给出一条具体、可立即执行、可验证的小行动。")
    report = "\n".join(lines) + "\n"

    ensure_store(args.store)
    aar_path = os.path.join(args.store, "aar-%s.md" % target.get("id", "last"))
    with open(aar_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print("复盘模板已写入：%s" % aar_path)
    return 0


# ----------------------------------------------------------------------------
# 子命令：report（周期报告）
# ----------------------------------------------------------------------------
def cmd_report(args):
    entries = load_log(args.store)
    if not entries:
        print("尚无反省日志。")
        return 0

    days = sorted({e["ts"][:10] for e in entries})
    span_days = (datetime.fromisoformat(days[-1]) - datetime.fromisoformat(days[0])).days + 1
    tag_counter = Counter()
    emo_counter = Counter()
    for e in entries:
        tag_counter.update(e.get("tags", []))
        emo_counter.update(e.get("emotion", []))

    lines = []
    lines.append("# 反省周期报告")
    lines.append("")
    lines.append("- 生成时间：%s" % now_iso())
    lines.append("- 跨度：%s ~ %s（%d 天），共 %d 条反省" % (days[0], days[-1], span_days, len(entries)))
    lines.append("")
    lines.append("## 高频标签（思维焦点）")
    for t, c in tag_counter.most_common(10):
        lines.append("- %s：%d" % (t, c))
    lines.append("")
    lines.append("## 情绪分布")
    for emo, c in emo_counter.most_common():
        lines.append("- %s：%d" % (emo, c))
    lines.append("")
    lines.append("## 下一步建议")
    lines.append("- 对反复出现的惯性标签，用 `aar` 做四问复盘，追问双环根因。")
    lines.append("- 用 `claim` 登记你真正重视的事，再用 `blindspot` 查言行 gap。")
    lines.append("- 持续记录是前提：样本越多，模式与盲点越可信。")

    report = "\n".join(lines) + "\n"
    ensure_store(args.store)
    rep_path = os.path.join(args.store, "reflect-report.md")
    with open(rep_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print("报告已写入：%s" % rep_path)
    return 0


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------
def build_parser():
    p = argparse.ArgumentParser(prog="reflect", description="self-reflect-agent 反省引擎")
    p.add_argument("--store", default=DEFAULT_STORE, help="数据目录（默认 .self-reflect）")
    sub = p.add_subparsers(dest="cmd")

    pl = sub.add_parser("log", help="记录一条反省")
    pl.add_argument("--situation", help="情境：发生了什么")
    pl.add_argument("--reaction", help="反应：我怎么应对的")
    pl.add_argument("--outcome", help="结果：最终怎样")
    pl.add_argument("--emotion", help="情绪（逗号分隔，留空自动识别）")
    pl.add_argument("--tags", nargs="*", help="显式补充标签")

    pp = sub.add_parser("pattern", help="跨时间模式识别")
    pp.add_argument("--min-days", type=int, default=2, help="同一标签出现天数阈值（默认2）")

    pc = sub.add_parser("claim", help="登记自称重视/想改")
    pc.add_argument("--kind", choices=["value", "avoid"], required=True)
    pc.add_argument("--text", required=True)

    pb = sub.add_parser("blindspot", help="言行盲点比对")

    pa = sub.add_parser("aar", help="四问复盘")
    pa.add_argument("--id", help="条目 id（默认最新）")

    pr = sub.add_parser("report", help="周期报告")
    return p


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.cmd:
        parser.print_help()
        return 0
    handlers = {
        "log": cmd_log,
        "pattern": cmd_pattern,
        "claim": cmd_claim,
        "blindspot": cmd_blindspot,
        "aar": cmd_aar,
        "report": cmd_report,
    }
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
