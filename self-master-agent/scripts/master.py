#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""self-master-agent 真引擎：技能登顶阶梯 + 实战检验。

把"想精通一门技能"变成可复核的爬坡记录：
  - add      登记一门要精通的技能（目标层级、当前层级）
  - ladder   设定/查看该技能的"登顶阶梯"各层判据
  - drill    记录一次真实世界实战（task/结果/证据/自信度），驱动升级
  - measure  自评当前层级得分，校准"以为自己会"
  - report   输出全部技能的掌握度报告 + 登顶曲线 + 弱项预警
  - plan     针对某技能给出"下一步该练什么"的缺口清单

退出码：0 正常 / 1 需关注（存在未达标的弱项）/ 4 系统性警报（参数或数据错误）。
纯标准库实现，确定性逻辑、可重跑、留实物证据（jsonl 日志 + markdown 产物）。
"""
import argparse
import json
import os
import sys
from datetime import datetime, date

ENGINE_VERSION = "2.0.0"
DEFAULT_TARGET = 5
DRILLS_NEEDED = 3          # 升到下一级所需的"下一级难度实战成功"次数
WEAK_DRILL_GAP_DAYS = 14   # 超过这么多天没实战即判弱项

LEVEL_NAMES = {1: "入门", 2: "胜任", 3: "熟练", 4: "精通", 5: "登顶"}


def die(msg, code=4):
    sys.stderr.write("错误：" + msg + "\n")
    sys.exit(code)


def now_iso():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def today_str():
    return date.today().strftime("%Y-%m-%d")


def ensure_dirs(data):
    for sub in ("skills", "notes", "reports"):
        os.makedirs(os.path.join(data, sub), exist_ok=True)


def events_path(data):
    return os.path.join(data, "events.jsonl")


def append_event(data, ev):
    ensure_dirs(data)
    ev["ts"] = now_iso()
    with open(events_path(data), "a", encoding="utf-8") as f:
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
    return out


def skill_path(data, sid):
    return os.path.join(data, "skills", sid + ".json")


def load_skill(data, sid):
    p = skill_path(data, sid)
    if not os.path.exists(p):
        die("找不到技能 " + sid + "，请先用 add 登记", 4)
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_skill(data, sid, obj):
    ensure_dirs(data)
    with open(skill_path(data, sid), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def gen_id(data):
    ensure_dirs(data)
    d = os.path.join(data, "skills")
    n = 0
    for fn in os.listdir(d):
        if fn.endswith(".json"):
            n += 1
    return "#" + str(n + 1)


def list_skills(data):
    d = os.path.join(data, "skills")
    if not os.path.isdir(d):
        return []
    out = []
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".json"):
            with open(os.path.join(d, fn), encoding="utf-8") as f:
                out.append(json.load(f))
    return out


def default_ladder(target):
    return [
        {"level": i, "name": LEVEL_NAMES.get(i, "L" + str(i)),
         "criteria": "（未设定，请用 ladder 命令定义第 %d 层判据）" % i}
        for i in range(1, target + 1)
    ]


def recompute_level(skill):
    """依据实战与自评，从当前层逐级向上尝试晋升。"""
    target = skill["target"]
    drills = skill.get("drills", [])
    measures = skill.get("measures", [])
    cur = skill.get("level", 1)
    promotions = []
    while cur < target:
        next_lvl = cur + 1
        succ = [d for d in drills
                if d.get("difficulty", 0) >= next_lvl and d.get("result") == "success"]
        has_measure = any(m.get("score", 0) >= next_lvl for m in measures)
        if len(succ) >= DRILLS_NEEDED and has_measure:
            cur = next_lvl
            promotions.append(cur)
        else:
            break
    skill["level"] = cur
    if promotions:
        skill.setdefault("promotions", [])
        for lv in promotions:
            skill["promotions"].append({"level": lv, "ts": now_iso()})
    return promotions


def mastery_pct(skill):
    target = skill["target"]
    cur = skill["level"]
    if target <= 1:
        return 100
    base = (cur - 1) / (target - 1)
    within = 0.0
    if cur < target:
        drills = skill.get("drills", [])
        succ_next = [d for d in drills
                    if d.get("difficulty", 0) >= cur + 1 and d.get("result") == "success"]
        drill_prog = min(len(succ_next) / DRILLS_NEEDED, 1.0)
        measures = skill.get("measures", [])
        meas_prog = 0.0
        if measures:
            latest = max(measures, key=lambda m: m.get("ts", ""))
            meas_prog = min(max(latest.get("score", 0) - cur, 0) / 1.0, 1.0)
        within = 0.5 * drill_prog + 0.5 * meas_prog
    return round(base * 100 + within * (100.0 / (target - 1)), 1)


def write_skill_note(data, skill):
    sid = skill["id"]
    p = os.path.join(data, "notes", sid + ".md")
    lines = []
    lines.append("# 技能档案 " + sid + " " + skill["name"])
    lines.append("")
    lines.append("- 目标：%s（共 %d 级）" % (skill.get("goal", "—"), skill["target"]))
    lines.append("- 当前层级：L%d %s（掌握度 %s%%）" % (
        skill["level"], LEVEL_NAMES.get(skill["level"], ""), mastery_pct(skill)))
    lines.append("")
    lines.append("## 登顶阶梯")
    lines.append("")
    for lv in skill.get("ladder", []):
        lines.append("- **L%d %s**：%s" % (lv["level"], lv["name"], lv["criteria"]))
    lines.append("")
    lines.append("## 实战记录（drill）")
    lines.append("")
    if skill.get("drills"):
        lines.append("| 时间 | 任务 | 难度 | 结果 | 自信 | 证据 |")
        lines.append("|---|---|---|---|---|---|")
        for d in skill["drills"]:
            lines.append("| %s | %s | L%d | %s | %s | %s |" % (
                d.get("ts", "")[:10], d.get("task", ""), d.get("difficulty", 0),
                d.get("result", ""), d.get("confidence", ""), d.get("evidence", "")))
    else:
        lines.append("（暂无实战记录）")
    lines.append("")
    lines.append("## 自评记录（measure）")
    lines.append("")
    if skill.get("measures"):
        lines.append("| 时间 | 得分(1-5) | 备注 |")
        lines.append("|---|---|---|")
        for m in skill["measures"]:
            lines.append("| %s | %s | %s |" % (
                m.get("ts", "")[:10], m.get("score", ""), m.get("note", "")))
    else:
        lines.append("（暂无自评记录）")
    lines.append("")
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def is_weak(skill):
    if skill["level"] >= skill["target"]:
        return False
    measures = skill.get("measures", [])
    drills = skill.get("drills", [])
    # 自评低于当前层 -> 虚高
    if measures:
        latest = max(measures, key=lambda m: m.get("ts", ""))
        if latest.get("score", 0) < skill["level"]:
            return True
    # 长期无实战
    if drills:
        last = max(d.get("ts", "") for d in drills)
        try:
            last_d = datetime.strptime(last[:10], "%Y-%m-%d")
            gap = (datetime.now() - last_d).days
            if gap > WEAK_DRILL_GAP_DAYS:
                return True
        except ValueError:
            pass
    else:
        return True  # 从未实战，直接弱项
    # 下一级实战成功数不足
    succ_next = [d for d in drills
                if d.get("difficulty", 0) >= skill["level"] + 1
                and d.get("result") == "success"]
    if len(succ_next) < DRILLS_NEEDED:
        return True
    return False


# ---- 子命令 ----

def cmd_add(args, data):
    name = args.name
    if not name:
        die("缺少 --name 技能名称", 4)
    target = args.target or DEFAULT_TARGET
    if target < 1 or target > 9:
        die("--target 必须在 1..9 之间", 4)
    sid = gen_id(data)
    skill = {
        "id": sid,
        "name": name,
        "goal": args.goal or "",
        "target": target,
        "level": args.level or 1,
        "ladder": default_ladder(target),
        "drills": [],
        "measures": [],
        "promotions": [],
        "created": now_iso(),
    }
    if skill["level"] > target:
        die("初始 --level 不能超过 --target", 4)
    save_skill(data, sid, skill)
    append_event(data, {"type": "skill_add", "id": sid, "name": name,
                        "target": target, "level": skill["level"]})
    write_skill_note(data, skill)
    print("已登记技能 %s %s（目标 L%d，当前 L%d）" % (
        sid, name, target, skill["level"]))
    return 0


def cmd_ladder(args, data):
    sid = args.id
    skill = load_skill(data, sid)
    if args.define:
        # 格式：L1:判据;L2:判据;...
        parts = args.define.split(";")
        ladder = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if ":" not in part:
                die("ladder 定义格式应为 'L1:判据;L2:判据'，缺少冒号：" + part, 4)
            key, crit = part.split(":", 1)
            key = key.strip().upper().lstrip("L")
            if not key.isdigit():
                die("层级标识非法：" + key, 4)
            lv = int(key)
            if lv < 1 or lv > skill["target"]:
                die("层级 %d 超出 1..%d 范围" % (lv, skill["target"]), 4)
            ladder.append({"level": lv,
                           "name": LEVEL_NAMES.get(lv, "L" + str(lv)),
                           "criteria": crit.strip()})
        ladder.sort(key=lambda x: x["level"])
        skill["ladder"] = ladder
        save_skill(data, sid, skill)
        append_event(data, {"type": "ladder_set", "id": sid, "levels": len(ladder)})
        write_skill_note(data, skill)
        print("已更新 %s 的登顶阶梯（%d 层）" % (sid, len(ladder)))
        return 0
    # 查看
    print("技能 %s %s 的登顶阶梯：" % (sid, skill["name"]))
    for lv in skill.get("ladder", []):
        mark = " ✓当前" if lv["level"] == skill["level"] else ""
        print("  L%d %s：%s%s" % (lv["level"], lv["name"], lv["criteria"], mark))
    return 0


def cmd_drill(args, data):
    sid = args.id
    skill = load_skill(data, sid)
    if not args.task:
        die("缺少 --task 实战任务描述", 4)
    diff = args.difficulty
    if diff < 1 or diff > skill["target"]:
        die("--difficulty 必须在 1..%d 之间" % skill["target"], 4)
    if args.result not in ("success", "partial", "fail"):
        die("--result 必须是 success/partial/fail 之一", 4)
    conf = args.confidence or 0
    if conf and (conf < 1 or conf > 5):
        die("--confidence 必须在 1..5 之间", 4)
    drill = {
        "ts": now_iso(),
        "task": args.task,
        "difficulty": diff,
        "result": args.result,
        "confidence": conf,
        "evidence": args.evidence or "",
    }
    skill.setdefault("drills", []).append(drill)
    promo = recompute_level(skill)
    save_skill(data, sid, skill)
    append_event(data, {"type": "drill", "id": sid, "difficulty": diff,
                        "result": args.result})
    for lv in promo:
        append_event(data, {"type": "promote", "id": sid, "level": lv})
    write_skill_note(data, skill)
    if promo:
        print("实战已记录。恭喜晋升至 L%d %s！" % (
            skill["level"], LEVEL_NAMES.get(skill["level"], "")))
    else:
        print("实战已记录。当前 L%d %s（掌握度 %s%%）" % (
            skill["level"], LEVEL_NAMES.get(skill["level"], ""), mastery_pct(skill)))
    return 0


def cmd_measure(args, data):
    sid = args.id
    skill = load_skill(data, sid)
    score = args.score
    if score < 1 or score > 5:
        die("--score 必须在 1..5 之间", 4)
    meas = {"ts": now_iso(), "score": score, "note": args.note or ""}
    skill.setdefault("measures", []).append(meas)
    promo = recompute_level(skill)
    save_skill(data, sid, skill)
    append_event(data, {"type": "measure", "id": sid, "score": score})
    for lv in promo:
        append_event(data, {"type": "promote", "id": sid, "level": lv})
    write_skill_note(data, skill)
    print("自评已记录（得分 %d/5）。当前 L%d（掌握度 %s%%）" % (
        score, skill["level"], mastery_pct(skill)))
    return 0


def cmd_report(args, data):
    skills = list_skills(data)
    if not skills:
        print("暂无技能，先用 add 登记。")
        return 0
    lines = []
    lines.append("# 技能掌握度报告 " + today_str())
    lines.append("")
    lines.append("| 技能 | 当前层 | 掌握度 | 目标 | 状态 |")
    lines.append("|---|---|---|---|---|")
    weak = []
    for s in skills:
        status = "已登顶" if s["level"] >= s["target"] else "爬坡中"
        lines.append("| %s %s | L%d %s | %s%% | L%d | %s |" % (
            s["id"], s["name"], s["level"], LEVEL_NAMES.get(s["level"], ""),
            mastery_pct(s), s["target"], status))
        if is_weak(s):
            weak.append(s)
    lines.append("")
    lines.append("## 登顶曲线")
    lines.append("")
    for s in skills:
        curve = " ".join("#" * s["level"] + "-" * (s["target"] - s["level"]))
        lines.append("- %s %s `%s`" % (s["id"], s["name"], curve))
    lines.append("")
    if weak:
        lines.append("## 弱项预警（需关注）")
        lines.append("")
        for s in weak:
            reasons = []
            measures = s.get("measures", [])
            drills = s.get("drills", [])
            if measures:
                latest = max(measures, key=lambda m: m.get("ts", ""))
                if latest.get("score", 0) < s["level"]:
                    reasons.append("自评(%d)低于当前层(%d)，疑似虚高" % (
                        latest.get("score", 0), s["level"]))
            if not drills:
                reasons.append("从未实战")
            else:
                succ_next = [d for d in drills
                            if d.get("difficulty", 0) >= s["level"] + 1
                            and d.get("result") == "success"]
                if len(succ_next) < DRILLS_NEEDED:
                    reasons.append("下一级实战成功仅 %d/%d 次" % (
                        len(succ_next), DRILLS_NEEDED))
            lines.append("- %s %s：%s" % (s["id"], s["name"], "；".join(reasons)))
        lines.append("")
    rep_path = os.path.join(data, "reports", "mastery-" + today_str() + ".md")
    with open(rep_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))
    print("\n报告已落盘：" + rep_path)
    return 1 if weak else 0


def cmd_plan(args, data):
    sid = args.id
    skill = load_skill(data, sid)
    if skill["level"] >= skill["target"]:
        print("%s %s 已登顶，无需继续规划。" % (sid, skill["name"]))
        return 0
    next_lvl = skill["level"] + 1
    drills = skill.get("drills", [])
    measures = skill.get("measures", [])
    succ_next = [d for d in drills
                if d.get("difficulty", 0) >= next_lvl and d.get("result") == "success"]
    need_drills = max(DRILLS_NEEDED - len(succ_next), 0)
    has_measure = any(m.get("score", 0) >= next_lvl for m in measures)
    print("下一步冲刺 L%d %s 的缺口：" % (next_lvl, LEVEL_NAMES.get(next_lvl, "")))
    if need_drills > 0:
        print("  - 还需 %d 次『L%d 难度』实战成功（真实场景，非模拟）" % (need_drills, next_lvl))
    else:
        print("  - 下一级实战次数已达标 ✓")
    if not has_measure:
        print("  - 还需一次自评得分 >= %d，确认你真的达到了" % next_lvl)
    else:
        print("  - 自评已达标 ✓")
    crit = ""
    for lv in skill.get("ladder", []):
        if lv["level"] == next_lvl:
            crit = lv["criteria"]
    if crit:
        print("  - L%d 判据：" % next_lvl + crit)
    return 0


def build_parser():
    p = argparse.ArgumentParser(
        description="self-master-agent 引擎 v" + ENGINE_VERSION +
                    "：技能登顶阶梯 + 实战检验（AI Agent 引擎）")
    p.add_argument("--data", required=True, help="数据目录（存放 jsonl 与产物）")
    p.add_argument("--version", action="version",
                   version="self-master-agent " + ENGINE_VERSION)
    sub = p.add_subparsers(dest="cmd")

    a = sub.add_parser("add", help="登记一门要精通的技能")
    a.add_argument("--name", required=True)
    a.add_argument("--goal", default="")
    a.add_argument("--target", type=int, default=DEFAULT_TARGET)
    a.add_argument("--level", type=int, default=1)

    b = sub.add_parser("ladder", help="设定/查看登顶阶梯判据")
    b.add_argument("--id", required=True)
    b.add_argument("--define", default="")

    c = sub.add_parser("drill", help="记录一次真实世界实战")
    c.add_argument("--id", required=True)
    c.add_argument("--task", required=True)
    c.add_argument("--difficulty", type=int, required=True)
    c.add_argument("--result", required=True)
    c.add_argument("--confidence", type=int, default=0)
    c.add_argument("--evidence", default="")

    d = sub.add_parser("measure", help="自评当前层级得分")
    d.add_argument("--id", required=True)
    d.add_argument("--score", type=int, required=True)
    d.add_argument("--note", default="")

    e = sub.add_parser("report", help="输出掌握度报告 + 登顶曲线")
    f = sub.add_parser("plan", help="给出下一步冲刺缺口")
    f.add_argument("--id", required=True)
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
        "add": cmd_add, "ladder": cmd_ladder, "drill": cmd_drill,
        "measure": cmd_measure, "report": cmd_report, "plan": cmd_plan,
    }
    if args.cmd not in handlers:
        die("未知子命令：" + args.cmd, 4)
    sys.exit(handlers[args.cmd](args, data))


if __name__ == "__main__":
    main()
