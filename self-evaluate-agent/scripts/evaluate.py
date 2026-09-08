#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""self-evaluate-agent 引擎 v2.0.0。

元认知评估与反思引擎。不是"打分记录器"——它组织一条 Reflexion 多轮闭环：
  产出 → 按 rubric 打分并引证据(submit) → 反思为何丢分(reflection) → 重写 → 重评 → 收敛(converge)。
并内置客观探针(--probe)：对目标做可计算的客观检查，标出风险点，作为你裁决的参考（不替代判决）。

分工：脚本管 结构化 / 加权 / 比对 / 收敛检测；大模型（你或 Agent）管 判断与改写。
不替你编分数。
"""
import sys, os, json, re, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUBRICS_FILE = os.path.join(ROOT, "resources", "rubrics.json")
EVAL_LOG = os.path.join(ROOT, "eval_log.jsonl")
CONVERGE_THRESHOLD = 0.3   # 相邻两轮总分差小于此值视为已收敛
MAX_ROUNDS_HINT = 5        # 超过此轮数仍未收敛则提示天花板和/或标准过严

class PreflightError(Exception):
    """preflight 错误：参数 / 文件 / 评分标准问题。退出码归我们管，不被 argparse 抢走。"""
    def __init__(self, msg, code=1):
        super().__init__(msg)
        self.code = code

# ---------- 基础工具 ----------

def _read_text(arg):
    if os.path.isfile(arg):
        with open(arg, "r", encoding="utf-8") as f:
            return f.read()
    return arg

def _now():
    return datetime.datetime.now().isoformat(timespec="seconds")

def load_rubric(name=None):
    """从 rubrics.json 取指定 rubric；name=None 取 default 标记的或第一个。"""
    if not os.path.isfile(RUBRICS_FILE):
        raise PreflightError("找不到评分标准库：%s" % RUBRICS_FILE, 2)
    try:
        store = json.load(open(RUBRICS_FILE, encoding="utf-8"))
    except Exception as e:
        raise PreflightError("评分标准库 JSON 非法：%s" % e, 2)
    rubrics = store.get("rubrics", {})
    if not rubrics:
        raise PreflightError("评分标准库为空", 2)
    if name:
        if name not in rubrics:
            raise PreflightError("评分标准 '%s' 不在库中（现有：%s）"
                                 % (name, ", ".join(rubrics.keys())), 2)
        return rubrics[name]
    # 默认：显式 default 标记，否则取第一个
    for k, v in rubrics.items():
        if v.get("default"):
            return v
    return next(iter(rubrics.values()))

def parse_scores(s):
    out = {}
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^([A-Za-z]+)\s*[:：]\s*([0-9.]+)$", part)
        if not m:
            raise PreflightError("分数格式非法：'%s'（用 维度:分数，例如 T:5）" % part, 1)
        out[m.group(1).upper()] = float(m.group(2))
    if not out:
        raise PreflightError("没有给出分数", 1)
    return out

def parse_evidence(s):
    """证据格式：'R:3-第2段未处理空输入;C:4-缺少错误提示' → {'R':'第2段未处理空输入', ...}"""
    out = {}
    if not s:
        return out
    for part in s.split(";"):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^([A-Za-z]+)\s*[:：]?\s*(.*)$", part)
        if m:
            out[m.group(1).upper()] = m.group(2).strip()
    return out

def weighted_total(scores, rubric):
    dims = rubric.get("dimensions", {})
    total_w, earned = 0.0, 0.0
    for k, v in scores.items():
        d = dims.get(k, {})
        w = d.get("weight", 1.0)
        maxv = d.get("max", 5.0)
        total_w += w
        earned += w * (v / maxv) if maxv else 0
    if total_w == 0:
        return 0.0
    return round(earned / total_w * rubric.get("out_of", 5.0), 2)

# ---------- 客观探针（可计算，仅供参考） ----------

def _probe_trace(text):
    """对 TRACE 五维做客观检查，返回 {维度: [发现,...]}。结论标 '机器预检，仅供参考'。"""
    findings = {"T": [], "R": [], "A": [], "C": [], "E": []}
    low_conf = re.findall(r"我认为|可能|大概|也许|应该|或许|估计|说不定",
                          text)
    if len(low_conf) >= 3:
        findings["T"].append("检测到 %d 处不确定词（我认为/可能/大概…），T 维度需核查是否主张过度或证据不足"
                             % len(low_conf))
    if re.search(r"一定|绝对|毫无疑问|必然", text) and "例如" not in text and "数据" not in text:
        findings["T"].append("出现绝对化断言但未见例据，T 维度需确认主张有出处")
    if re.search(r"TODO|FIXME|未实现|待补|pass\s*#|占位", text):
        findings["R"].append("发现 TODO/FIXME/占位标记，R 维度需确认可靠性与完整性")
    if re.search(r"def |function |public |void |int |string ", text):
        if not re.search(r"if\s*\(?\s*\w*\s*==\s*null|is None|为空|空输入|异常|try|catch|except", text):
            findings["R"].append("疑似代码但未见输入校验/异常分支，R 维度需核查边界与失败路径")
    if not re.search(r"场景|用户|例子|例如|适用|当.{0,4}时", text):
        findings["A"].append("未出现用户场景/例子/适用边界信号，A 维度需确认对齐真实需求")
    if re.search(r"^\s*#", text, re.M) or "##" in text:
        heads = re.findall(r"^#{1,3}\s+(.+)$", text, re.M)
        if heads and heads[0] and not re.search(r"总结|结论|下一步|行动", text):
            findings["E"].append("有结构标题但未见'结论/下一步/行动'，E 维度需确认交付可行动性")
    # 清理空维度
    return {k: v for k, v in findings.items() if v}

def _probe_generic(text):
    """非 TRACE 评分标准时的通用统计（仍映射回常见维度含义）。"""
    out = {}
    n = len(text)
    paras = [p for p in text.split("\n\n") if p.strip()]
    todos = len(re.findall(r"TODO|FIXME|未实现|占位", text))
    low = len(re.findall(r"我认为|可能|大概|也许|应该", text))
    if todos:
        out["可靠"] = ["发现 %d 处 TODO/占位标记" % todos]
    if low >= 3:
        out["可信"] = ["不确定词密度偏高（%d 处）" % low]
    if n < 200:
        out["充实度"] = ["内容偏短（%d 字），可能缺乏论证" % n]
    if not paras:
        out["结构"] = ["未识别到段落结构"]
    return out

def cmd_probe(target, rubric_name):
    text = _read_text(target)
    if not text.strip():
        raise PreflightError("目标内容为空：%s" % target, 1)
    rb = load_rubric(rubric_name)
    dims = list(rb.get("dimensions", {}).keys())
    # 仅对 TRACE（含 T/R/A/C/E 五维）用强映射，否则通用
    if set(dims) >= {"T", "R", "A", "C", "E"} and len(dims) == 5:
        res = _probe_trace(text)
    else:
        res = _probe_generic(text)
    print("【机器预检 · 仅供参考，不替代你的判决】")
    print("目标：%s （%d 字）  评分标准：%s" % (target if os.path.isfile(target) else "<内联文本>",
                                          len(text), rb.get("name", rubric_name or "default")))
    if not res:
        print("  ✓ 未触发明显客观风险点。请仍按 rubric 主观裁决。")
    else:
        for dim, items in res.items():
            print("  维度 %s：%s" % (dim, "；".join(items)))

# ---------- 多轮提交与收敛 ----------

def cmd_submit(target, scores_raw, evidence_raw, reflection, fix, round_no, rubric_name, as_json):
    rb = load_rubric(rubric_name)
    text = _read_text(target)
    if not text.strip():
        raise PreflightError("目标内容为空：%s" % target, 1)
    scores = parse_scores(scores_raw)
    for k in scores:
        if k not in rb.get("dimensions", {}):
            raise PreflightError("维度 '%s' 不在评分标准（现有：%s）"
                                 % (k, ",".join(rb.get("dimensions", {}).keys())), 1)
    evidence = parse_evidence(evidence_raw)
    # 每个低分（<4）必须有证据，否则 preflight 拦截——这是质量纪律
    missing = [k for k, v in scores.items() if v < 4.0 and not evidence.get(k)]
    if missing:
        raise PreflightError("维度 %s 分数<4 但缺证据（用 --evidence '%s:出处' 补）"
                             % (",".join(missing), missing[0]), 1)
    total = weighted_total(scores, rb)
    rec = {
        "ts": _now(),
        "target": target if os.path.isfile(target) else "<内联文本>",
        "rubric": rubric_name or rb.get("name", "default"),
        "round": int(round_no or (len(_rounds_for(target, rubric_name)) + 1)),
        "scores": scores,
        "total": total,
        "evidence": evidence,
        "reflection": reflection or "",
        "fix": fix or "",
    }
    with open(EVAL_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    if as_json:
        print(json.dumps(rec, ensure_ascii=False, indent=2))
    else:
        print("✅ 已记录第 %d 轮  总分=%.2f/%s  各维度=%s"
              % (rec["round"], total, rb.get("out_of", 5), scores))
        if rec["fix"]:
            print("   下一轮改进：%s" % rec["fix"])
        print("   日志：%s" % EVAL_LOG)

def _rounds_for(target, rubric_name):
    """返回匹配 (target, rubric) 的历史轮次（按 round 升序）。"""
    if not os.path.isfile(EVAL_LOG):
        return []
    key_target = target if os.path.isfile(target) else "<内联文本>"
    rb_name = rubric_name or load_rubric(rubric_name).get("name", "default")
    rows = [json.loads(l) for l in open(EVAL_LOG, encoding="utf-8") if l.strip()]
    rows = [r for r in rows if r.get("target") == key_target and r.get("rubric") == rb_name]
    rows.sort(key=lambda r: r.get("round", 0))
    return rows

def _reflection_quality(reflection, scores):
    """反思质量评分（0-5）：有内容、点根因、引维度、含改进意图。"""
    if not reflection or len(reflection) < 10:
        return 0.0
    q = 1.0
    if re.search(r"根因|因为|由于|导致|所以|其实|问题在", reflection):
        q += 1.5
    if re.search(r"[TRACED]|维度|[A-Z]{1,3}[:：]", reflection):
        q += 1.0
    if re.search(r"重写|改|下一轮|补|加|先写|调整|重构", reflection):
        q += 1.5
    return min(5.0, q)

def cmd_converge(target, rubric_name, as_json):
    rows = _rounds_for(target, rubric_name) if target else _all_rounds_grouped(rubric_name)
    if not rows:
        raise PreflightError("还没有评估轮次——先用 --submit 评一轮", 3)
    # 按 (target, rubric) 分组，每组独立收敛分析
    groups = {}
    for r in rows:
        g = (r.get("target"), r.get("rubric"))
        groups.setdefault(g, []).append(r)
    report = []
    for (tgt, rbname), grp in groups.items():
        grp.sort(key=lambda r: r.get("round", 0))
        dims = list(grp[0]["scores"].keys())
        # 每维序列
        series = {d: [r["scores"].get(d) for r in grp] for d in dims}
        totals = [r["total"] for r in grp]
        n = len(grp)
        # 斜率（首末差 / (n-1)）
        slope = (totals[-1] - totals[0]) / (n - 1) if n > 1 else 0.0
        # 收敛：最后两轮差 < 阈值
        converged = n >= 2 and abs(totals[-1] - totals[-2]) < CONVERGE_THRESHOLD
        # 卡住维度：均值最低
        means = {d: sum(v) / len(v) for d, v in series.items()}
        stuck = min(means, key=means.get)
        # 反思质量均值
        rq = sum(_reflection_quality(r.get("reflection", ""), r["scores"]) for r in grp) / n
        report.append({
            "target": tgt, "rubric": rbname, "rounds": n,
            "totals": totals, "final_total": totals[-1],
            "slope": round(slope, 3), "converged": converged,
            "dim_means": {k: round(v, 2) for k, v in means.items()},
            "stuck_dim": stuck, "reflection_quality": round(rq, 2),
        })
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    for r in report:
        print("=" * 60)
        print("目标：%s   评分标准：%s   轮数：%d" % (r["target"], r["rubric"], r["rounds"]))
        print("总分轨迹：%s" % " → ".join("%.2f" % t for t in r["totals"]))
        print("斜率：%+.3f /轮   最终总分：%.2f" % (r["slope"], r["final_total"]))
        print("是否收敛：%s" % ("是（相邻轮差<%s，建议停止迭代）" % CONVERGE_THRESHOLD if r["converged"]
                              else "否（仍有提升空间）"))
        print("各维均值：%s" % "  ".join("%s=%.2f" % (k, v) for k, v in r["dim_means"].items()))
        print("卡住维度：%s（均值最低，是下一个杠杆点）" % r["stuck_dim"])
        print("反思质量：%.2f/5（越高说明反思越点根因、带改进意图）" % r["reflection_quality"])
        if r["rounds"] > MAX_ROUNDS_HINT and not r["converged"]:
            print("⚠ 已超 %d 轮仍未收敛：可能触及当前能力天花板，或评分标准过严——考虑换思路而非硬磨"
                  % MAX_ROUNDS_HINT)
        print("建议：%s" % ("停止迭代，固化本轮为基线" if r["converged"]
                       else "针对 %s 维做下一轮重写" % r["stuck_dim"]))

def _all_rounds_grouped(rubric_name):
    if not os.path.isfile(EVAL_LOG):
        return []
    rows = [json.loads(l) for l in open(EVAL_LOG, encoding="utf-8") if l.strip()]
    if rubric_name:
        rb_name = load_rubric(rubric_name).get("name", rubric_name)
        rows = [r for r in rows if r.get("rubric") == rb_name]
    return rows

def cmd_report(dim, as_json):
    if not os.path.isfile(EVAL_LOG):
        raise PreflightError("还没有评分日志——先评一条吧", 3)
    rows = [json.loads(l) for l in open(EVAL_LOG, encoding="utf-8") if l.strip()]
    if dim:
        series = [{"ts": r["ts"], "round": r.get("round"), "v": r["scores"].get(dim.upper())}
                  for r in rows if dim.upper() in r["scores"]]
        print("维度 %s 趋势：" % dim.upper())
        for s in series:
            print("  %s  轮%s  %s" % (s["ts"], s["round"], s["v"]))
    else:
        totals = [r["total"] for r in rows]
        print("总趋势（共 %d 条评分）：" % len(rows))
        for r in rows:
            print("  %s  轮%s  总分=%.2f  %s" % (r["ts"], r.get("round", "?"),
                                             r["total"], r.get("reflection", "")[:30]))
        if totals:
            print("  均值=%.2f  最低=%.2f  最高=%.2f" % (sum(totals)/len(totals), min(totals), max(totals)))
    if as_json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))

# ---------- 评分标准管理（保留并增强） ----------

def cmd_init_rubric(name):
    if not name:
        raise PreflightError("--init-rubric 需要一个名称", 1)
    store = _load_store()
    if name in store["rubrics"]:
        raise PreflightError("评分标准已存在：%s" % name, 1)
    store["rubrics"][name] = {
        "name": name, "out_of": 5.0, "default": False,
        "dimensions": {
            "Q1": {"weight": 1.0, "max": 5.0, "desc": "在此填入你的维度"},
            "Q2": {"weight": 1.0, "max": 5.0, "desc": "在此填入你的维度"},
        },
        "anchors": {"5": "典范", "4": "扎实", "3": "及格", "2": "弱", "1": "坏"},
    }
    _save_store(store)
    print("✅ 已生成评分标准骨架：%s（在 resources/rubrics.json 内）" % name)

def cmd_calibrate(good, bad):
    for p in (good, bad):
        if not os.path.isfile(p):
            raise PreflightError("找不到样本：%s" % p, 2)
    g = open(good, encoding="utf-8").read()
    b = open(bad, encoding="utf-8").read()
    cand = []
    for txt in (g, b):
        for line in txt.splitlines():
            line = line.strip().lstrip("-*0123456789. ").strip()
            if 6 <= len(line) <= 60:
                cand.append(line)
    dims = {}
    for i, c in enumerate(cand[:6], 1):
        dims["C%d" % i] = {"weight": 1.0, "max": 5.0, "desc": c[:40]}
    store = _load_store()
    store["rubrics"]["calibrated"] = {
        "name": "calibrated", "out_of": 5.0, "default": False,
        "dimensions": dims,
        "anchors": {"5": "典范", "4": "扎实", "3": "及格", "2": "弱", "1": "坏"},
        "note": "从 %s（好）/ %s（差）自动播种；请手改 desc 与权重" % (good, bad),
    }
    _save_store(store)
    print("✅ 已用少量样本生成起步评分标准：calibrated（%d 个维度）" % len(dims))

def cmd_show_rubric(name):
    rb = load_rubric(name)
    print("评分标准：%s  （满分=%.1f）" % (rb.get("name", name or "default"), rb.get("out_of", 5)))
    for k, v in rb.get("dimensions", {}).items():
        print("  %s  权重=%.1f 满分=%.1f  %s" % (k, v.get("weight", 1), v.get("max", 5), v.get("desc", "")[:50]))
    if rb.get("anchors"):
        print("  锚点：%s" % "  ".join("%s=%s" % (k, v) for k, v in rb["anchors"].items()))

def _load_store():
    if not os.path.isfile(RUBRICS_FILE):
        return {"rubrics": {}}
    try:
        return json.load(open(RUBRICS_FILE, encoding="utf-8"))
    except Exception:
        return {"rubrics": {}}

def _save_store(store):
    json.dump(store, open(RUBRICS_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ---------- 参数解析（手动，退出码归我们） ----------

def _parse_argv(argv):
    a = {}
    i = 0
    flags1 = {"--probe", "--submit", "--scores", "--evidence", "--reflection",
              "--fix", "--rubric", "--init-rubric", "--show-rubric", "--dim"}
    while i < len(argv):
        x = argv[i]
        if x in flags1:
            if i + 1 >= len(argv):
                raise PreflightError("缺少 %s 的值" % x, 1)
            a[x.lstrip("-")] = argv[i + 1]; i += 2
        elif x == "--calibrate":
            if i + 2 >= len(argv):
                raise PreflightError("--calibrate 需要 <好样本> <差样本>", 1)
            a["calibrate"] = [argv[i + 1], argv[i + 2]]; i += 3
        elif x == "--round":
            if i + 1 >= len(argv):
                raise PreflightError("缺少 --round 的值", 1)
            a["round"] = argv[i + 1]; i += 2
        elif x in ("--report", "--converge", "--json"):
            a[x.lstrip("-")] = True; i += 1
        else:
            i += 1
    return a

def main():
    try:
        a = _parse_argv(sys.argv[1:])
    except PreflightError as e:
        print("❌ %s" % e); sys.exit(e.code)
    try:
        if "probe" in a:
            cmd_probe(a["probe"], a.get("rubric"))
        elif "submit" in a:
            if "scores" not in a:
                raise PreflightError("--submit 需要 --scores \"维度:分数,...\"", 1)
            cmd_submit(a["submit"], a["scores"], a.get("evidence", ""),
                       a.get("reflection", ""), a.get("fix", ""),
                       a.get("round"), a.get("rubric"), a.get("json"))
        elif "converge" in a:
            cmd_converge(a.get("submit") or a.get("probe"), a.get("rubric"), a.get("json"))
        elif "report" in a:
            cmd_report(a.get("dim"), a.get("json"))
        elif "init-rubric" in a:
            cmd_init_rubric(a["init-rubric"])
        elif "calibrate" in a:
            vals = a["calibrate"]
            cmd_calibrate(vals[0], vals[1])
        elif "show-rubric" in a:
            cmd_show_rubric(a.get("show-rubric") or None)
        else:
            print("用法：")
            print("  evaluate.py --probe <文件|文本> [--rubric 名]")
            print("  evaluate.py --submit <文件|文本> --scores \"T:5,R:4\" [--evidence \"R:3-出处\"] [--reflection 文] [--fix 文] [--round N] [--rubric 名] [--json]")
            print("  evaluate.py --converge [--rubric 名] [--json]")
            print("  evaluate.py --report [--dim T] [--json]")
            print("  evaluate.py --init-rubric <名称> | --calibrate <好样本> <差样本> | --show-rubric [名称]")
            sys.exit(1)
    except PreflightError as e:
        print("❌ %s" % e); sys.exit(e.code)
    except FileNotFoundError as e:
        print("❌ 找不到文件：%s" % e); sys.exit(2)
    except Exception as e:
        print("❌ 意外错误：%s" % e); sys.exit(3)

if __name__ == "__main__":
    main()
