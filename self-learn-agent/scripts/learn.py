#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
self-learn-agent 真引擎
=====================================================================
定位：知识消化 + 抗遗忘间隔重复。把书/课吃透成你的私有库。

能力（子命令）：
  ingest      消化一条知识源（书/课），拆成原子知识点，落库并生成消化笔记。
  review      间隔复习调度（SM-2 + Leitner 盒），列出今日待复习或记录一次复习。
  quiz        主动回忆测试（测试效应），抽题并记录回忆成绩。
  elaborate   精细质询（为什么/如何/与什么相关），写 elaboration。
  interleave  交错练习，按日期确定性混排不同主题生成练习序列。
  report      掌握度报告，统计掌握度、遗忘风险、间隔分布，产出 markdown 报表。

设计原则（4.8 基准）：
  - 纯标准库，无第三方依赖。
  - 确定性逻辑：相同输入 + 相同日期种子 => 相同调度/交错结果，可重跑复核。
  - 实物证据：knowledge.jsonl（知识库）、events.jsonl（追加式事件日志）、
    notes/（消化笔记 markdown）、reports/（掌握度报表 markdown）。
  - 中文报错；退出码 0 正常 / 1 需关注（存在高风险遗忘点）/ 4 系统性警报。

版本：EVENT_VERSION 与 resources 的 version、SKILL.md 的 version 三处一致。
"""

import argparse
import hashlib
import json
import os
import random
import re
import sys
from datetime import date, datetime, timedelta

# ============================================================
# 版本常量（三处一致之一）
# ============================================================
EVENT_VERSION = "2.0.0"

# 退出码
EXIT_OK = 0          # 正常
EXIT_ATTENTION = 1   # 需关注（存在高风险遗忘知识点）
EXIT_FATAL = 4       # 系统性警报（读写/配置损坏）

# Leitner 盒间隔（天）。盒越高间隔越长。
LEITNER_INTERVALS = [1, 2, 4, 7, 15, 30, 60]

# 主动回忆成绩分级
GRADE_PASS = 3       # grade >= 3 视为通过本次复习

DATA_DIR_DEFAULT = "self_learn_data"


# ============================================================
# 通用工具
# ============================================================
def die(msg, code=EXIT_FATAL):
    """中文报错并退出。"""
    print(f"[错误] {msg}", file=sys.stderr)
    sys.exit(code)


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def today_str():
    return date.today().isoformat()


def parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        die(f"日期格式错误：{s!r}，应为 YYYY-MM-DD")


def ensure_data_dir(data_dir):
    """确保数据目录与子结构存在。"""
    for sub in ("", "notes", "reports"):
        p = os.path.join(data_dir, sub)
        if not os.path.isdir(p):
            try:
                os.makedirs(p, exist_ok=True)
            except Exception as e:
                die(f"无法创建数据目录 {p}：{e}")
    know_path = os.path.join(data_dir, "knowledge.jsonl")
    ev_path = os.path.join(data_dir, "events.jsonl")
    for p in (know_path, ev_path):
        if not os.path.exists(p):
            try:
                open(p, "a", encoding="utf-8").close()
            except Exception as e:
                die(f"无法初始化数据文件 {p}：{e}")


def load_knowledge(data_dir):
    """读取知识库，返回列表。损坏行跳过并告警，但整库不可读则致命。"""
    path = os.path.join(data_dir, "knowledge.jsonl")
    items = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for ln, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    items.append(json.loads(line))
                except Exception:
                    print(f"[警告] knowledge.jsonl 第 {ln} 行解析失败，已跳过",
                          file=sys.stderr)
    except FileNotFoundError:
        die(f"知识库不存在：{path}，请先运行 init 或 ingest")
    except Exception as e:
        die(f"读取知识库失败：{e}")
    return items


def save_knowledge(data_dir, items):
    path = os.path.join(data_dir, "knowledge.jsonl")
    try:
        with open(path, "w", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
    except Exception as e:
        die(f"写入知识库失败：{e}")


def append_event(data_dir, event):
    path = os.path.join(data_dir, "events.jsonl")
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception as e:
        die(f"写入事件日志失败：{e}")


def load_events(data_dir):
    path = os.path.join(data_dir, "events.jsonl")
    evs = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    evs.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        return []
    return evs


def make_id(seed):
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]


def find_item(items, ident):
    """按 id 或序号（#N）查找。"""
    if ident.startswith("#"):
        try:
            idx = int(ident[1:]) - 1
            if 0 <= idx < len(items):
                return items[idx], idx
        except Exception:
            pass
    for it in items:
        if it.get("id") == ident:
            return it, items.index(it)
    return None, -1


def fmt_mastery(v):
    return f"{round(float(v) * 100)}%"


# ============================================================
# 子命令实现
# ============================================================
def cmd_ingest(args):
    """消化一条知识源，落库并生成消化笔记 markdown。"""
    data_dir = args.data
    ensure_data_dir(data_dir)
    items = load_knowledge(data_dir)

    source = args.source.strip()
    title = (args.title or "").strip()
    concept = args.concept.strip()
    note = (args.note or "").strip()
    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]

    if not concept:
        die("concept（核心概念）不能为空")

    kid = make_id(f"{source}|{title}|{concept}|{EVENT_VERSION}")
    # 若已存在同 id，则累加版本而非重复
    exist, _ = find_item(items, kid)
    if exist:
        exist["updated_at"] = now_iso()
        exist["note"] = note or exist.get("note", "")
        if tags:
            exist["tags"] = sorted(set(exist.get("tags", []) + tags))
        save_knowledge(data_dir, items)
        append_event(data_dir, {
            "ts": now_iso(), "version": EVENT_VERSION, "type": "ingest_update",
            "item_id": kid, "source": source, "concept": concept,
        })
        print(f"[OK] 已更新知识块 {kid}（已存在，未重复落库）")
        return EXIT_OK

    item = {
        "id": kid,
        "source": source,
        "title": title,
        "concept": concept,
        "note": note,
        "tags": tags,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "bucket": 1,                 # Leitner 盒，从 1 开始
        "interval_days": 1,          # 当前间隔（天）
        "ease": 2.5,                 # SM-2 难度因子
        "repetitions": 0,            # 连续通过次数
        "due_date": today_str(),     # 首次复习：今天
        "last_review": None,
        "mastery": 0.05,             # 初始掌握度
        "recall_history": [],        # 测试效应成绩序列
        "elaborations": [],         # 精细质询记录
        "forgotten_count": 0,       # 失败复习次数
    }
    items.append(item)
    save_knowledge(data_dir, items)

    # 生成消化笔记 markdown
    note_path = os.path.join(data_dir, "notes", f"{kid}.md")
    try:
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(_digest_note_md(item))
    except Exception as e:
        print(f"[警告] 消化笔记写入失败：{e}", file=sys.stderr)

    append_event(data_dir, {
        "ts": now_iso(), "version": EVENT_VERSION, "type": "ingest",
        "item_id": kid, "source": source, "concept": concept,
    })
    print(f"[OK] 已消化知识块 {kid}")
    print(f"     来源：{source}｜概念：{concept}")
    print(f"     笔记：{note_path}")
    return EXIT_OK


def _digest_note_md(item):
    return (
        f"# 消化笔记：{item['concept']}\n\n"
        f"- 知识块 ID：`{item['id']}`\n"
        f"- 来源：{item['source']}\n"
        f"- 章节/标题：{item['title'] or '（未填）'}\n"
        f"- 标签：{', '.join(item['tags']) or '（无）'}\n"
        f"- 创建：{item['created_at']}\n"
        f"- 初始掌握度：{fmt_mastery(item['mastery'])}\n\n"
        f"## 我的消化\n\n{item['note'] or '（待补充）'}\n\n"
        f"## 复习轨迹\n\n"
        f"- 当前 Leitner 盒：{item['bucket']}\n"
        f"- 当前间隔：{item['interval_days']} 天\n"
        f"- 下次复习：{item['due_date']}\n"
    )


def cmd_review(args):
    """间隔复习调度。无 --id 时列出今日待复习；有 --id 时记录一次复习。"""
    data_dir = args.data
    ensure_data_dir(data_dir)
    items = load_knowledge(data_dir)
    if not items:
        print("[提示] 知识库为空，先用 ingest 消化知识。")
        return EXIT_OK

    # 记录一次复习
    if args.id is not None and args.grade is not None:
        return _review_record(data_dir, items, args.id, args.grade, args.date)

    # 否则列出待复习
    d = parse_date(args.date) if args.date else date.today()
    due = [it for it in items if it.get("due_date", "") <= d.isoformat()]
    due.sort(key=lambda x: x.get("due_date", ""))
    if not due:
        print(f"[OK] {d.isoformat()} 没有待复习项，保持节奏。")
        return EXIT_OK
    print(f"=== {d.isoformat()} 待复习（共 {len(due)} 项）===")
    for i, it in enumerate(due, 1):
        print(f"  #{i} [{it['id']}] {it['concept']} "
              f"（盒{it['bucket']}｜间隔{it['interval_days']}d｜"
              f"掌握{fmt_mastery(it['mastery'])}）来源：{it['source']}")
    high_risk = [it for it in due if it.get("mastery", 1) < 0.4
                 or it.get("forgotten_count", 0) >= 2]
    if high_risk:
        print(f"\n[需关注] {len(high_risk)} 项处于高风险遗忘区，优先复习。")
        return EXIT_ATTENTION
    return EXIT_OK


def _review_record(data_dir, items, ident, grade, date_str):
    it, idx = find_item(items, ident)
    if it is None:
        die(f"未找到知识块：{ident}")
    try:
        grade = int(grade)
    except Exception:
        die("grade 必须为整数 0-5")
    if not (0 <= grade <= 5):
        die("grade 必须落在 0-5 区间")

    d = parse_date(date_str) if date_str else date.today()
    passed = grade >= GRADE_PASS

    # Leitner 盒推进
    if passed:
        it["bucket"] = min(it["bucket"] + 1, len(LEITNER_INTERVALS))
        it["repetitions"] = it["repetitions"] + 1
        it["forgotten_count"] = 0
    else:
        it["bucket"] = max(1, it["bucket"] - 1)
        it["repetitions"] = 0
        it["forgotten_count"] = it.get("forgotten_count", 0) + 1

    # SM-2 难度因子
    ef = float(it.get("ease", 2.5))
    ef = ef + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02))
    it["ease"] = max(1.3, round(ef, 3))

    # 间隔计算（Leitner 为主，SM-2 为辅取较大值）
    lei = LEITNER_INTERVALS[it["bucket"] - 1]
    sm2 = max(1, round(it["interval_days"] * it["ease"])) if passed else 1
    it["interval_days"] = max(lei, sm2) if passed else 1
    it["due_date"] = (d + timedelta(days=it["interval_days"])).isoformat()
    it["last_review"] = d.isoformat()

    # 掌握度：通过则上浮，失败则回落
    m = float(it.get("mastery", 0.05))
    if passed:
        m = min(1.0, m + 0.12 + 0.02 * grade)
    else:
        m = max(0.0, m - 0.15)
    it["mastery"] = round(m, 3)

    it["updated_at"] = now_iso()
    save_knowledge(data_dir, items)
    append_event(data_dir, {
        "ts": now_iso(), "version": EVENT_VERSION, "type": "review",
        "item_id": it["id"], "grade": grade, "passed": passed,
        "bucket": it["bucket"], "interval_days": it["interval_days"],
        "due_date": it["due_date"], "mastery": it["mastery"],
    })
    print(f"[OK] 已记录复习 {it['id']}（grade={grade}，"
          f"{'通过' if passed else '未通过'}）")
    print(f"     下次复习：{it['due_date']}｜掌握度：{fmt_mastery(it['mastery'])}")
    if not passed:
        return EXIT_ATTENTION
    return EXIT_OK


def cmd_quiz(args):
    """主动回忆测试（测试效应）。抽题并记录回忆成绩。"""
    data_dir = args.data
    ensure_data_dir(data_dir)
    items = load_knowledge(data_dir)
    if not items:
        print("[提示] 知识库为空，先用 ingest 消化知识。")
        return EXIT_OK

    d = parse_date(args.date) if args.date else date.today()
    # 确定性抽题：以日期为种子，优先抽 overdue 与低掌握度
    pool = sorted(items, key=lambda x: (x.get("due_date", "") <= d.isoformat(),
                                        x.get("mastery", 1)))
    if args.id:
        target, _ = find_item(items, args.id)
        if target is None:
            die(f"未找到知识块：{args.id}")
        pool = [target]
    n = min(args.count, len(pool))
    chosen = pool[:n]

    if args.recall is not None:
        # 记录一次回忆成绩
        if not args.id:
            die("记录回忆成绩时必须用 --id 指定知识块")
        it, _ = find_item(items, args.id)
        if it is None:
            die(f"未找到知识块：{args.id}")
        try:
            r = float(args.recall)
        except Exception:
            die("recall 必须为 0-1 之间的小数")
        if not (0.0 <= r <= 1.0):
            die("recall 必须落在 0.0-1.0 区间")
        it.setdefault("recall_history", []).append({
            "date": d.isoformat(), "recall": round(r, 3)})
        # 回忆成绩计入掌握度
        m = float(it.get("mastery", 0.05))
        m = min(1.0, max(0.0, m * 0.6 + r * 0.4))
        it["mastery"] = round(m, 3)
        it["updated_at"] = now_iso()
        save_knowledge(data_dir, items)
        append_event(data_dir, {
            "ts": now_iso(), "version": EVENT_VERSION, "type": "quiz",
            "item_id": it["id"], "recall": round(r, 3),
            "mastery": it["mastery"],
        })
        print(f"[OK] 已记录主动回忆 {it['id']}（recall={round(r,3)}，"
              f"掌握度={fmt_mastery(it['mastery'])}）")
        return EXIT_OK

    # 列出抽题
    print(f"=== 主动回忆抽题（{d.isoformat()}，共 {len(chosen)} 题）===")
    for i, it in enumerate(chosen, 1):
        print(f"  #{i} [{it['id']}] {it['concept']}")
        print(f"      来源：{it['source']}｜当前掌握：{fmt_mastery(it['mastery'])}")
        print(f"      合上资料，凭回忆复述后执行：")
        print(f"      learn.py quiz --id {it['id']} --recall 0.8")
    return EXIT_OK


def cmd_elaborate(args):
    """精细质询：对知识块写 elaboration（为什么/如何/与什么相关）。"""
    data_dir = args.data
    ensure_data_dir(data_dir)
    items = load_knowledge(data_dir)
    if not args.id:
        die("elaborate 必须用 --id 指定知识块")
    it, _ = find_item(items, args.id)
    if it is None:
        die(f"未找到知识块：{args.id}")

    why = (args.why or "").strip()
    how = (args.how or "").strip()
    relate = (args.relate or "").strip()
    if not (why or how or relate):
        die("why/how/relate 至少填一项")

    elab = {"ts": now_iso(), "why": why, "how": how, "relate": relate}
    it.setdefault("elaborations", []).append(elab)
    # 精细质询提升掌握度（理解加深）
    m = float(it.get("mastery", 0.05))
    it["mastery"] = round(min(1.0, m + 0.05), 3)
    it["updated_at"] = now_iso()
    save_knowledge(data_dir, items)

    # 更新消化笔记
    note_path = os.path.join(data_dir, "notes", f"{it['id']}.md")
    try:
        if os.path.exists(note_path):
            with open(note_path, "r", encoding="utf-8") as f:
                content = f.read()
            block = "\n## 精细质询\n\n"
            block += (f"- 为什么：{why}\n" if why else "")
            block += (f"- 如何：{how}\n" if how else "")
            block += (f"- 与什么相关：{relate}\n" if relate else "")
            if "## 精细质询" in content:
                content = content.rstrip() + "\n" + block.lstrip("\n")
            else:
                content = content.rstrip() + "\n" + block
            with open(note_path, "w", encoding="utf-8") as f:
                f.write(content)
    except Exception as e:
        print(f"[警告] 笔记更新失败：{e}", file=sys.stderr)

    append_event(data_dir, {
        "ts": now_iso(), "version": EVENT_VERSION, "type": "elaborate",
        "item_id": it["id"], "has_why": bool(why), "has_how": bool(how),
        "has_relate": bool(relate), "mastery": it["mastery"],
    })
    print(f"[OK] 已为 {it['id']} 添加精细质询，掌握度={fmt_mastery(it['mastery'])}")
    return EXIT_OK


def cmd_interleave(args):
    """交错练习：按日期确定性混排不同主题生成练习序列。"""
    data_dir = args.data
    ensure_data_dir(data_dir)
    items = load_knowledge(data_dir)
    if not items:
        print("[提示] 知识库为空，先用 ingest 消化知识。")
        return EXIT_OK

    d = parse_date(args.date) if args.date else date.today()
    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
    pool = items
    if tags:
        pool = [it for it in items
                if set(it.get("tags", [])) & set(tags)]
    if not pool:
        print("[提示] 按标签筛选后无可用知识块。")
        return EXIT_OK

    n = min(args.count, len(pool))
    # 确定性交错：以日期为随机种子，round-robin 不同主题（按 source/concept 首字分组）
    rng = random.Random(d.isoformat() + "|interleave")
    shuffled = pool[:]
    rng.shuffle(shuffled)
    # 按来源分组，round-robin 交错输出，避免同类连排
    groups = {}
    for it in shuffled:
        groups.setdefault(it.get("source", "未知"), []).append(it)
    order = []
    keys = list(groups.keys())
    while len(order) < n and any(groups[k] for k in keys):
        for k in keys:
            if groups[k]:
                order.append(groups[k].pop(0))
                if len(order) >= n:
                    break

    print(f"=== 交错练习序列（{d.isoformat()}，{len(order)} 题）===")
    for i, it in enumerate(order, 1):
        print(f"  {i}. [{it['id']}] {it['concept']}（来源：{it['source']}）")
    print("\n提示：交错练习比集中练习更能提升长期迁移，"
          "按此顺序逐题主动回忆。")
    append_event(data_dir, {
        "ts": now_iso(), "version": EVENT_VERSION, "type": "interleave",
        "date": d.isoformat(), "count": len(order),
        "items": [it["id"] for it in order],
    })
    return EXIT_OK


def cmd_report(args):
    """掌握度报告：统计掌握度、遗忘风险、间隔分布，产出 markdown 报表。"""
    data_dir = args.data
    ensure_data_dir(data_dir)
    items = load_knowledge(data_dir)
    evs = load_events(data_dir)
    d = parse_date(args.date) if args.date else date.today()

    total = len(items)
    if total == 0:
        print("[提示] 知识库为空，先用 ingest 消化知识。")
        return EXIT_OK

    mastered = [it for it in items if it.get("mastery", 0) >= 0.8]
    learning = [it for it in items if 0.4 <= it.get("mastery", 0) < 0.8]
    weak = [it for it in items if it.get("mastery", 0) < 0.4]
    overdue = [it for it in items if it.get("due_date", "") <= d.isoformat()]
    high_risk = [it for it in items
                 if it.get("forgotten_count", 0) >= 2
                 or it.get("mastery", 1) < 0.3]

    avg_mastery = round(sum(it.get("mastery", 0) for it in items) / total, 3)
    avg_ease = round(sum(it.get("ease", 2.5) for it in items) / total, 3)
    review_events = [e for e in evs if e.get("type") == "review"]
    quiz_events = [e for e in evs if e.get("type") == "quiz"]

    md = _report_md(items, d, total, mastered, learning, weak, overdue,
                    high_risk, avg_mastery, avg_ease,
                    len(review_events), len(quiz_events))

    out = args.out
    if out:
        try:
            with open(out, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"[OK] 报表已写出：{out}")
        except Exception as e:
            die(f"报表写出失败：{e}")
    else:
        # 默认落到 reports/ 目录，按日期命名
        out = os.path.join(data_dir, "reports",
                           f"mastery-{d.isoformat()}.md")
        try:
            with open(out, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"[OK] 报表已写出：{out}")
        except Exception as e:
            die(f"报表写出失败：{e}")

    print(f"\n总知识块 {total}｜平均掌握 {fmt_mastery(avg_mastery)}｜"
          f"待复习 {len(overdue)}｜高风险 {len(high_risk)}")
    if high_risk or weak:
        return EXIT_ATTENTION
    return EXIT_OK


def _report_md(items, d, total, mastered, learning, weak, overdue,
               high_risk, avg_mastery, avg_ease, n_review, n_quiz):
    lines = []
    lines.append(f"# 掌握度报告（{d.isoformat()}）\n")
    lines.append(f"- 生成版本：{EVENT_VERSION}")
    lines.append(f"- 知识块总数：**{total}**")
    lines.append(f"- 平均掌握度：**{fmt_mastery(avg_mastery)}**")
    lines.append(f"- 平均难度因子（SM-2 ease）：{avg_ease}")
    lines.append(f"- 复习事件累计：{n_review}｜主动回忆事件累计：{n_quiz}\n")

    lines.append("## 掌握度分布\n")
    lines.append(f"- 已掌握（≥80%）：{len(mastered)}")
    lines.append(f"- 学习中（40%–80%）：{len(learning)}")
    lines.append(f"- 薄弱（<40%）：{len(weak)}\n")

    lines.append("## 遗忘风险\n")
    lines.append(f"- 今日待复习：{len(overdue)}")
    lines.append(f"- 高风险（多次遗忘或掌握<30%）：{len(high_risk)}\n")

    if high_risk:
        lines.append("### 优先处理的高风险知识块\n")
        for it in sorted(high_risk, key=lambda x: x.get("mastery", 1)):
            lines.append(
                f"- [{it['id']}] {it['concept']}｜掌握"
                f"{fmt_mastery(it['mastery'])}｜遗忘次数"
                f"{it.get('forgotten_count',0)}｜来源 {it['source']}")
        lines.append("")

    lines.append("## 全部知识块清单\n")
    lines.append("| # | 概念 | 来源 | 盒 | 间隔(d) | 掌握 | 下次复习 |")
    lines.append("|---|------|------|----|---------|------|----------|")
    for i, it in enumerate(sorted(items,
                                  key=lambda x: x.get("mastery", 1)), 1):
        lines.append(
            f"| {i} | {it['concept']} | {it['source']} | {it['bucket']} | "
            f"{it['interval_days']} | {fmt_mastery(it['mastery'])} | "
            f"{it.get('due_date','')} |")
    lines.append("")
    lines.append("> 报告由 self-learn-agent 真引擎生成，数据来源于 "
                 "knowledge.jsonl 与 events.jsonl，可逐条复核。")
    return "\n".join(lines) + "\n"


# ============================================================
# CLI
# ============================================================
def build_parser():
    p = argparse.ArgumentParser(
        description="self-learn-agent：知识消化 + 抗遗忘间隔重复真引擎")
    p.add_argument("--data", default=DATA_DIR_DEFAULT,
                   help=f"数据目录（默认 {DATA_DIR_DEFAULT}）")
    sub = p.add_subparsers(dest="command", required=True)

    pi = sub.add_parser("ingest", help="消化一条知识源")
    pi.add_argument("--source", required=True, help="来源（书名/课程名）")
    pi.add_argument("--title", help="章节/标题")
    pi.add_argument("--concept", required=True, help="核心概念（原子知识点）")
    pi.add_argument("--note", help="你的消化笔记")
    pi.add_argument("--tags", help="标签，逗号分隔")

    pr = sub.add_parser("review", help="间隔复习调度")
    pr.add_argument("--id", help="知识块 id 或 #序号")
    pr.add_argument("--grade", help="复习成绩 0-5（与 --id 同用记录一次复习）")
    pr.add_argument("--date", help="日期 YYYY-MM-DD，默认今天")

    pq = sub.add_parser("quiz", help="主动回忆测试")
    pq.add_argument("--id", help="指定知识块")
    pq.add_argument("--count", type=int, default=5, help="抽题数量")
    pq.add_argument("--recall", help="回忆成绩 0.0-1.0（记录用）")
    pq.add_argument("--date", help="日期 YYYY-MM-DD，默认今天")

    pe = sub.add_parser("elaborate", help="精细质询")
    pe.add_argument("--id", required=True, help="知识块 id 或 #序号")
    pe.add_argument("--why", help="为什么成立")
    pe.add_argument("--how", help="如何应用")
    pe.add_argument("--relate", help="与什么相关")

    pl = sub.add_parser("interleave", help="交错练习序列")
    pl.add_argument("--count", type=int, default=6, help="序列长度")
    pl.add_argument("--tags", help="按标签筛选，逗号分隔")
    pl.add_argument("--date", help="日期 YYYY-MM-DD，默认今天")

    pp = sub.add_parser("report", help="掌握度报告")
    pp.add_argument("--out", help="报表输出路径（默认 reports/ 下按日期）")
    pp.add_argument("--date", help="日期 YYYY-MM-DD，默认今天")

    return p


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        # argparse 自行报错（英文 usage），这里转为中文提示
        print("[错误] 参数解析失败，请用 -h 查看用法。", file=sys.stderr)
        return EXIT_FATAL

    try:
        if args.command == "ingest":
            return cmd_ingest(args)
        elif args.command == "review":
            return cmd_review(args)
        elif args.command == "quiz":
            return cmd_quiz(args)
        elif args.command == "elaborate":
            return cmd_elaborate(args)
        elif args.command == "interleave":
            return cmd_interleave(args)
        elif args.command == "report":
            return cmd_report(args)
        else:
            print("[错误] 未知子命令", file=sys.stderr)
            return EXIT_FATAL
    except SystemExit:
        raise
    except Exception as e:  # 兜底：任何未捕获异常都致命但不崩溃
        die(f"引擎异常：{e}")


if __name__ == "__main__":
    sys.exit(main())
