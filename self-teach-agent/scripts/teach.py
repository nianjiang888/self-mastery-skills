#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""self-teach-agent 主编排引擎：摄入 → 结构化 → 自测覆盖 → 晋升/回滚/汇报。

设计取向：把"自己教自己"做成可检验的闭环。脚本不替你理解，只负责
把读到的材料拆成知识单元、检查每个单元是否"真掌握"、并在覆盖达标时
才允许晋升为可复用本领（否则物理拦下，返回非零退出码）。

全中文输出；错误用中文说明；退出码：0=成功/达标，1=门禁未过/用法错误。
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime

LOG_FILE = "teach_log.jsonl"
REQUIRED_FIELDS = ["concept", "definition", "why", "example"]  # 真掌握的四要素
PROMOTE_COVERAGE = 1.0  # 覆盖必须 100% 才晋升
GRADE_PASS = 4          # 自测回忆评分门槛(0-5)


class PreflightError(Exception):
    pass


def _log_path():
    return os.path.join(os.getcwd(), LOG_FILE)


def _append(rec):
    rec["ts"] = datetime.now().isoformat(timespec="seconds")
    with open(_log_path(), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _load():
    if not os.path.exists(_log_path()):
        return []
    out = []
    with open(_log_path(), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out


def _rewrite(rows):
    with open(_log_path(), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _read_material(path):
    if path == "-":
        return sys.stdin.read()
    if not os.path.exists(path):
        raise PreflightError("材料文件不存在：%s" % path)
    return open(path, encoding="utf-8-sig").read()


def _chunk(text):
    """把材料切成候选知识单元：按空行/标题切分，过滤过短片段。"""
    parts = re.split(r"\n\s*\n|(?=^#{1,6}\s)", text, flags=re.MULTILINE)
    units = []
    for p in parts:
        p = p.strip()
        if len(p) < 20:   # 太短不算一个单元
            continue
        # 取首句当概念候选，去掉 # 号
        first = re.sub(r"^#{1,6}\s*", "", p.splitlines()[0]).strip()
        units.append({"raw": p, "concept_hint": first[:40]})
    return units


def cmd_ingest(args):
    text = _read_material(args.material)
    chunks = _chunk(text)
    if not chunks:
        raise PreflightError("材料未切出任何知识单元，可能太短或格式为空。")
    # 构建结构化单元脚手架
    units = []
    for i, c in enumerate(chunks, 1):
        units.append({
            "idx": i,
            "concept": c["concept_hint"],
            "definition": "",
            "why": "",
            "example": "",
            "related": "",
            "source": args.topic,
            "mastered": False,
            "recall": None,
        })
    _append({"action": "ingest", "topic": args.topic, "units": units,
             "unit_count": len(units)})
    print("已摄入主题《%s》，拆出 %d 个知识单元脚手架。" % (args.topic, len(units)))
    print("下一步：为每个单元补全 definition / why / example（可用你的笔记工具填写）。")
    print("完成后跑 --quiz 检查覆盖，再 --promote 晋升为可复用本领。")


def _coverage(rows):
    """返回 (主题->单元列表) 以及覆盖统计。"""
    by_topic = {}
    for r in rows:
        if r.get("action") == "ingest":
            by_topic[r["topic"]] = r["units"]
    return by_topic


def _unit_complete(u):
    return all(u.get(f, "").strip() for f in REQUIRED_FIELDS)


def cmd_quiz(args):
    rows = _load()
    by_topic = _coverage(rows)
    if not by_topic:
        raise PreflightError("还没有摄入任何材料，先跑 --ingest。")
    grades = {}
    if args.grades:
        if not os.path.exists(args.grades):
            raise PreflightError("评分文件不存在：%s" % args.grades)
        grades = json.load(open(args.grades, encoding="utf-8"))
    print("===== 自测覆盖检查 =====")
    total = 0
    complete = 0
    for topic, units in by_topic.items():
        comp = sum(1 for u in units if _unit_complete(u))
        total += len(units)
        complete += comp
        print("\n主题《%s》 覆盖 %d/%d" % (topic, comp, len(units)))
        for u in units:
            ok = _unit_complete(u)
            tag = "✓" if ok else "✗ 缺:" + ",".join(
                f for f in REQUIRED_FIELDS if not u.get(f, "").strip())
            grade = grades.get(u["concept"], u.get("recall"))
            if grade is not None:
                tag += " 回忆评分=%s" % grade
            print("  [%s] %s" % (tag, u["concept"]))
    cov = (complete / total) if total else 0
    print("\n总覆盖：%d/%d = %.0f%%" % (complete, total, cov * 100))
    # 把覆盖结果记下来
    _append({"action": "quiz", "coverage": round(cov, 3),
             "complete": complete, "total": total})
    return cov


def cmd_promote(args):
    rows = _load()
    by_topic = _coverage(rows)
    if not by_topic:
        raise PreflightError("还没有摄入任何材料，先跑 --ingest。")
    grades = {}
    if args.grades:
        grades = json.load(open(args.grades, encoding="utf-8"))
    # 检查覆盖 + 评分
    total = 0
    complete = 0
    low_grade = []
    for topic, units in by_topic.items():
        for u in units:
            total += 1
            if _unit_complete(u):
                complete += 1
            g = grades.get(u["concept"], u.get("recall"))
            if g is not None and int(g) < GRADE_PASS:
                low_grade.append((topic, u["concept"], g))
    cov = complete / total if total else 0
    if cov < PROMOTE_COVERAGE:
        print("✗ 晋升被拦下：覆盖 %.0f%% < 100%%，还有单元未补全四要素。" % (cov * 100))
        print("  先补全 definition / why / example 再试。")
        return 1
    if low_grade:
        print("✗ 晋升被拦下：以下单元自测回忆评分 < %d（未真掌握）：" % GRADE_PASS)
        for t, c, g in low_grade:
            print("  - 《%s》%s 评分=%s" % (t, c, g))
        return 1
    # 全部达标 → 晋升为可复用本领
    skills = []
    for topic, units in by_topic.items():
        skills.append({"skill": topic, "units": len(units),
                       "promoted_at": datetime.now().isoformat(timespec="seconds")})
    _append({"action": "promote", "skills": skills,
             "coverage": round(cov, 3)})
    print("✓ 晋升成功！以下主题已固化为可复用本领：")
    for s in skills:
        print("  - 《%s》（%d 个知识单元）" % (s["skill"], s["units"]))
    print("建议：把本领同步进 self-improvement-agent 的永久记忆，或抽成独立技能。")
    return 0


def cmd_rollback(args):
    rows = _load()
    # 找到最后一条 promote 删掉
    idx = None
    for i in range(len(rows) - 1, -1, -1):
        if rows[i].get("action") == "promote":
            idx = i
            break
    if idx is None:
        raise PreflightError("没有可回滚的晋升记录。")
    removed = rows[idx]
    rows = rows[:idx]
    _rewrite(rows)
    names = "、".join(s["skill"] for s in removed.get("skills", []))
    print("已回滚晋升：%s" % names)


def cmd_report(args):
    rows = _load()
    ingests = [r for r in rows if r.get("action") == "ingest"]
    quizzes = [r for r in rows if r.get("action") == "quiz"]
    promotes = [r for r in rows if r.get("action") == "promote"]
    print("===== 学习进度汇报 =====")
    print("摄入主题数：%d" % len(ingests))
    print("知识单元总数：%d" % sum(r["unit_count"] for r in ingests))
    if quizzes:
        last = quizzes[-1]
        print("最近一次自测覆盖：%.0f%%（%d/%d）" % (
            last["coverage"] * 100, last["complete"], last["total"]))
    print("已晋升本领数：%d" % sum(len(r.get("skills", [])) for r in promotes))


def cmd_record(args):
    _append({"action": "record", "note": args.note})
    print("已记录学习事件：%s" % args.note)


def build_parser():
    p = argparse.ArgumentParser(description="self-teach 自我教学编排引擎")
    p.add_argument("--ingest", action="store_true", help="摄入材料并拆成知识单元")
    p.add_argument("--topic", default="未命名主题", help="材料所属主题名")
    p.add_argument("--material", help="材料路径，或 - 读标准输入")
    p.add_argument("--quiz", action="store_true", help="自测覆盖检查")
    p.add_argument("--grades", help="可选：单元->回忆评分(0-5) 的 json 文件")
    p.add_argument("--promote", action="store_true", help="覆盖达标才晋升本领")
    p.add_argument("--rollback", action="store_true", help="回滚最近一次晋升")
    p.add_argument("--report", action="store_true", help="学习进度汇报")
    p.add_argument("--record", help="记录一条学习事件")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.ingest:
            if not args.material:
                raise PreflightError("--ingest 必须配合 --material 指定材料。")
            return cmd_ingest(args)
        if args.quiz:
            cmd_quiz(args)
            return 0
        if args.promote:
            return cmd_promote(args)
        if args.rollback:
            cmd_rollback(args)
            return 0
        if args.report:
            cmd_report(args)
            return 0
        if args.record:
            cmd_record(args)
            return 0
        parser.print_help()
        return 0
    except PreflightError as e:
        print("用法错误：%s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
