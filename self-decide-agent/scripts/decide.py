#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
self-decide-agent · 决策日志 / 回放评分引擎 v2.0.0

帮用户做决定，并在事后最小化后悔地复盘。

子命令
  log        记录一次决策：选项 / 预期结果 / 可逆性(reversible|irreversible)
  replay     日后回放：填入实际结果、打分(预期达成度)、算后悔度，可纠正可逆性误判
  bias       识别反复出现的决策偏差（损失厌恶 / 现状偏误 / 确认偏误 …）
  report     决策质量报告：可逆vs不可逆误判率、常犯偏差、后悔最小化建议
  premortem  事前验尸（pre-mortem）：先假设已失败，反推原因 + 二阶思考提示
  list       列出已记录决策（含是否已回放）

理论锚点（落进 references 与本文档）
  · 可逆/不可逆决策框架（Bezos 单向门/双向门）
  · 事前验尸 pre-mortem（Gary Klein 2007）
  · 决策疲劳 decision fatigue（Baumeister）
  · 二阶思考 second-order thinking（Howard Marks）
  · 后悔最小化框架（Bezos regret minimization）

退出码
  0  正常
  1  发现反复决策偏差 / 可逆性误判率偏高 / 存在单次重大不可逆误判
  4  重大不可逆误判警报（如不可逆决策多次严重误判）

实物证据（4.8 基准：留可重跑文件）
  · decision-log.jsonl：每条决策一行，纯数据，可任意时刻重跑分析。
  · decision-report.md / bias-report.md / premortem-<slug>.md / replay-<id>.md：各命令生成的可复核 markdown。
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone

DEFAULT_STORE = ".self-decide"
EVENT_VERSION = "2.0.0"

HERE = os.path.dirname(os.path.abspath(__file__))


# ----------------------------------------------------------------------------
# 偏差库加载（resources/biases.json）
# ----------------------------------------------------------------------------
def load_biases(path=None):
    """加载决策偏差库。path 缺省用 resources/biases.json。"""
    if path is None:
        path = os.path.join(HERE, "..", "resources", "biases.json")
    path = os.path.abspath(path)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def detect_biases(text, lib):
    """扫描文本，返回命中的偏差 id 列表（确定性：子串命中）。"""
    text = (text or "").lower()
    hits = []
    for b in lib.get("biases", []):
        for hint in b.get("hints", []):
            if hint.lower() in text:
                hits.append(b["id"])
                break
    return hits


def load_frameworks(path=None):
    """加载决策框架库。path 缺省用 resources/decision-frameworks.json。"""
    if path is None:
        path = os.path.join(HERE, "..", "resources", "decision-frameworks.json")
    path = os.path.abspath(path)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ----------------------------------------------------------------------------
# 存储与 IO
# ----------------------------------------------------------------------------
def log_file(store):
    return os.path.join(store, "decision-log.jsonl")


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


def save_log(store, entries):
    ensure_store(store)
    with open(log_file(store), "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def next_id(store):
    return "d%d" % (len(load_log(store)) + 1)


# ----------------------------------------------------------------------------
# 子命令：log
# ----------------------------------------------------------------------------
def cmd_log(args):
    context = (args.context or "").strip()
    chosen = (args.chosen or "").strip()
    expected = (args.expected or "").strip()
    reversibility = (args.reversibility or "").strip().lower()
    framework = (args.framework or "").strip()
    if not context:
        print("错误：请至少提供 --context（决策情境）。", file=sys.stderr)
        return 2
    if reversibility not in ("reversible", "irreversible"):
        print("错误：--reversibility 必须为 reversible（可逆/双向门）或 irreversible（不可逆/单向门）。", file=sys.stderr)
        return 2

    # 选项：分号分隔，去空去重保序
    options = [o.strip() for o in (args.options or "").split(";") if o.strip()]
    if chosen and chosen not in options:
        options.append(chosen)

    lib = load_biases(args.biases)
    full = " ".join([context, " ".join(options), chosen, expected])
    biases_flag = detect_biases(full, lib)

    entry = {
        "id": next_id(args.store),
        "ts": now_iso(),
        "context": context,
        "options": options,
        "chosen": chosen,
        "expected": expected,
        "reversibility": reversibility,
        "framework": framework,
        "tags": [t.strip() for t in (args.tags or "").split(",") if t.strip()],
        "biases_flag": biases_flag,
        "actual": None,
        "actual_outcome": None,
        "score": None,      # 预期达成度/满意度 0-100
        "regret": None,     # 后悔度 0-100
        "reversibility_replay": None,  # 回放时纠正的可逆性
        "replay_ts": None,
        "version": EVENT_VERSION,
    }
    ensure_store(args.store)
    with open(log_file(args.store), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    kind = "可逆(双向门)" if reversibility == "reversible" else "不可逆(单向门)"
    print("已记录决策 %s：%s" % (entry["id"], context))
    print("  所选：%s" % (chosen or "（未指定）"))
    print("  可逆性：%s" % kind)
    if biases_flag:
        names = [b["name_cn"] for b in lib["biases"] if b["id"] in biases_flag]
        print("  ⚠ 检测到潜在决策偏差：%s（建议回放时复核）" % "、".join(names))
    else:
        print("  未检出明显偏差关键词。")
    return 0


# ----------------------------------------------------------------------------
# 子命令：replay
# ----------------------------------------------------------------------------
def cmd_replay(args):
    entries = load_log(args.store)
    if not entries:
        print("尚无决策记录，先用 `log` 记录一次决策。", file=sys.stderr)
        return 2
    target = None
    if args.id:
        target = next((e for e in entries if e.get("id") == args.id), None)
    else:
        target = entries[-1]
    if not target:
        print("错误：未找到决策 %s。" % args.id, file=sys.stderr)
        return 2

    actual = (args.actual or "").strip()
    if not actual:
        print("错误：replay 需提供 --actual（实际发生的结果描述）。", file=sys.stderr)
        return 2

    # 评分
    try:
        score = int(args.score) if args.score is not None else None
    except ValueError:
        print("错误：--score 必须为 0-100 整数。", file=sys.stderr)
        return 2
    if score is not None and not (0 <= score <= 100):
        print("错误：--score 必须在 0-100 之间。", file=sys.stderr)
        return 2

    try:
        regret = int(args.regret) if args.regret is not None else None
    except ValueError:
        print("错误：--regret 必须为 0-100 整数。", file=sys.stderr)
        return 2
    if regret is not None and not (0 <= regret <= 100):
        print("错误：--regret 必须在 0-100 之间。", file=sys.stderr)
        return 2

    # 后悔度缺省 = 100 - 满意度（互补近似，已在文档标注取舍）
    if regret is None:
        regret = 100 - score if score is not None else None

    # 可逆性纠正（误判检测）
    rev_replay = (args.reversibility or "").strip().lower() or None
    if rev_replay is not None and rev_replay not in ("reversible", "irreversible"):
        print("错误：--reversibility 必须为 reversible 或 irreversible。", file=sys.stderr)
        return 2

    target["actual"] = actual
    target["actual_outcome"] = (args.outcome or "").strip()
    target["score"] = score
    target["regret"] = regret
    target["reversibility_replay"] = rev_replay
    target["replay_ts"] = now_iso()

    save_log(args.store, entries)

    misjudge = rev_replay is not None and rev_replay != target["reversibility"]
    print("已回放决策 %s。" % target["id"])
    print("  实际结果：%s" % actual)
    if score is not None:
        print("  预期达成度：%d/100　后悔度：%d/100" % (score, regret))
    if misjudge:
        print("  ⚠ 可逆性误判：当时记为 %s，回放纠正为 %s。"
              % (target["reversibility"], rev_replay))

    # 实物证据：replay-<id>.md
    lines = []
    lines.append("# 决策回放 · %s" % target["id"])
    lines.append("")
    lines.append("- 情境：%s" % target["context"])
    lines.append("- 所选：%s" % (target["chosen"] or "（未指定）"))
    lines.append("- 当时预期：%s" % (target["expected"] or "（无）"))
    lines.append("- 当时可逆性：%s" % target["reversibility"])
    lines.append("- 实际结果：%s" % actual)
    lines.append("- 实际影响：%s" % (target["actual_outcome"] or "（无）"))
    if score is not None:
        lines.append("- 预期达成度：%d/100　后悔度：%d/100" % (score, regret))
    if misjudge:
        lines.append("- **可逆性误判**：原判 %s → 回放 %s" % (target["reversibility"], rev_replay))
    lines.append("")
    lines.append("## 后悔最小化提示")
    if regret is not None and regret >= 60:
        lines.append("- 后悔度偏高。回顾：这是可逆决策吗？若是，纠正成本低，不必过度自责；")
        lines.append("  若不可逆，重点是把这次的『判断前提』写下来，下次同类情境直接对照。")
    else:
        lines.append("- 后悔度可控。把『做对的前提假设』固化，复用到未来同类决策。")
    report = "\n".join(lines) + "\n"
    ensure_store(args.store)
    rp_path = os.path.join(args.store, "replay-%s.md" % target["id"])
    with open(rp_path, "w", encoding="utf-8") as f:
        f.write(report)
    print("  回放报告已写：%s" % rp_path)
    return 0


# ----------------------------------------------------------------------------
# 子命令：bias
# ----------------------------------------------------------------------------
def aggregate_bias(entries, lib):
    """统计所有决策中命中的偏差频次。返回 Counter(bias_id)。"""
    counter = Counter()
    for e in entries:
        for b in e.get("biases_flag", []):
            counter[b] += 1
    return counter


def cmd_bias(args):
    entries = load_log(args.store)
    if not entries:
        print("尚无决策记录。先用 `log` 记录几次决策，偏差才会显现。")
        return 0
    lib = load_biases(args.biases)
    counter = aggregate_bias(entries, lib)
    by_id = {b["id"]: b for b in lib["biases"]}

    lines = []
    lines.append("# 决策偏差识别报告")
    lines.append("")
    lines.append("- 生成时间：%s" % now_iso())
    lines.append("- 分析样本：%d 条决策" % len(entries))
    lines.append("")
    if not counter:
        lines.append("## 未发现反复偏差")
        lines.append("当前记录中未检出偏差关键词。注意：这是『不臆测』的诚实结果，不代表决策一定理性。")
        report = "\n".join(lines) + "\n"
        ensure_store(args.store)
        with open(os.path.join(args.store, "bias-report.md"), "w", encoding="utf-8") as f:
            f.write(report)
        print(report)
        print("偏差报告已写：%s" % os.path.join(args.store, "bias-report.md"))
        return 0

    recurring = [(bid, n) for bid, n in counter.most_common() if n >= 2]
    lines.append("## 偏差频次（按出现次数降序）")
    for bid, n in counter.most_common():
        tag = "  ← 反复出现" if n >= 2 else ""
        b = by_id.get(bid, {})
        lines.append("- **%s（%s）**：%d 次%s" % (b.get("name_cn", bid), b.get("name_en", ""), n, tag))
    lines.append("")
    lines.append("## 反复偏差拆解与对冲")
    if recurring:
        for bid, n in recurring:
            b = by_id.get(bid, {})
            lines.append("- **%s**：出现 %d 次。" % (b.get("name_cn", bid), n))
            lines.append("  - 是什么：%s" % b.get("desc", ""))
            lines.append("  - 怎么对冲：%s" % b.get("mitigation", ""))
    else:
        lines.append("- 暂未出现 ≥2 次的反复偏差。保持记录以持续验证。")
    lines.append("")
    lines.append("> 决策疲劳（Baumeister）提示：单次决策质量在一天后期会下降。")
    lines.append("> 反复偏差往往出现在疲劳时段——把重要决定挪到精力充沛时，并固化检查清单。")

    report = "\n".join(lines) + "\n"
    ensure_store(args.store)
    bp_path = os.path.join(args.store, "bias-report.md")
    with open(bp_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print("偏差报告已写：%s" % bp_path)

    # 退出码：存在反复偏差 → 1
    return 1 if recurring else 0


# ----------------------------------------------------------------------------
# 子命令：report
# ----------------------------------------------------------------------------
def cmd_report(args):
    entries = load_log(args.store)
    if not entries:
        print("尚无决策记录。先用 `log` 记录决策，再用 `replay` 回填实际结果。")
        return 0
    lib = load_biases(args.biases)
    by_id = {b["id"]: b for b in lib["biases"]}

    total = len(entries)
    rev_counts = Counter(e.get("reversibility") for e in entries)
    replayed = [e for e in entries if e.get("score") is not None or e.get("actual")]
    scored = [e for e in entries if e.get("score") is not None]

    # 可逆性误判率
    misjudged = [e for e in entries
                 if e.get("reversibility_replay") is not None
                 and e["reversibility_replay"] != e["reversibility"]]
    misjudge_rate = (len(misjudged) / len(replayed)) if replayed else 0.0

    # 重大不可逆误判：不可逆 + 满意度低 + 后悔高
    severe = [e for e in entries
              if e.get("reversibility") == "irreversible"
              and e.get("score") is not None and e["score"] < 40
              and e.get("regret") is not None and e["regret"] > 60]

    # 偏差频次
    bias_counter = aggregate_bias(entries, lib)
    recurring_bias = any(n >= 2 for n in bias_counter.values())

    # 后悔最小化排序
    regret_ranked = sorted(
        [e for e in entries if e.get("regret") is not None],
        key=lambda e: e["regret"], reverse=True
    )

    avg_score = (sum(e["score"] for e in scored) / len(scored)) if scored else None
    avg_regret = (sum(e["regret"] for e in scored) / len(scored)) if scored else None

    lines = []
    lines.append("# 决策质量报告（self-decide-agent v%s）" % EVENT_VERSION)
    lines.append("")
    lines.append("- 生成时间：%s" % now_iso())
    lines.append("- 决策总数：**%d**　已回放：**%d**" % (total, len(replayed)))
    lines.append("")
    lines.append("## 一、可逆性分布与误判")
    lines.append("- 可逆(双向门)：%d　不可逆(单向门)：%d" % (rev_counts.get("reversible", 0), rev_counts.get("irreversible", 0)))
    if replayed:
        lines.append("- 可逆性误判率：**%.0f%%**（%d/%d 条回放时纠正了原判断）"
                     % (misjudge_rate * 100, len(misjudged), len(replayed)))
        if misjudged:
            for e in misjudged:
                lines.append("  - %s：%s → %s（%s）"
                             % (e["id"], e["reversibility"], e["reversibility_replay"], e["context"]))
    lines.append("")
    lines.append("## 二、满意度与后悔度")
    if avg_score is not None:
        lines.append("- 平均预期达成度：%.1f/100　平均后悔度：%.1f/100" % (avg_score, avg_regret))
    else:
        lines.append("- 暂无带评分的回放，无法计算均值。先 `replay` 几条。")
    lines.append("")
    lines.append("## 三、常犯偏差")
    if bias_counter:
        for bid, n in bias_counter.most_common(8):
            b = by_id.get(bid, {})
            lines.append("- %s：%d 次%s" % (b.get("name_cn", bid), n, "（反复）" if n >= 2 else ""))
    else:
        lines.append("- 未检出明显偏差关键词。")
    lines.append("")
    lines.append("## 四、后悔最小化建议")
    if regret_ranked:
        lines.append("- 后悔度最高的决策（优先复盘根因）：")
        for e in regret_ranked[:3]:
            lines.append("  - %s [%s]：后悔度 %d，情境「%s」"
                         % (e["id"], e["reversibility"], e["regret"], e["context"]))
    if severe:
        lines.append("- ⚠ **重大不可逆误判 %d 次**：不可逆决策且满意度<40、后悔度>60，"
                     "需把每次的判断前提固化成检查清单，避免再犯。" % len(severe))
    lines.append("- 对反复偏差，建立『决策前检查清单』（见 bias 命令输出）。")
    lines.append("- 把不可逆决策的标准拉高：单向门要多想二阶后果（Howard Marks）。")

    report = "\n".join(lines) + "\n"
    ensure_store(args.store)
    rp_path = os.path.join(args.store, "decision-report.md")
    with open(rp_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print("报告已写：%s" % rp_path)

    # 退出码
    if len(severe) >= 2:
        return 4
    if len(severe) == 1 or misjudge_rate >= 0.5 or recurring_bias:
        return 1
    return 0


# ----------------------------------------------------------------------------
# 子命令：premortem（事前验尸 + 二阶思考）
# ----------------------------------------------------------------------------
def cmd_premortem(args):
    context = (args.context or "").strip()
    if not context:
        print("错误：请通过 --context 提供决策情境。", file=sys.stderr)
        return 2
    reversibility = (args.reversibility or "").strip().lower()
    if reversibility and reversibility not in ("reversible", "irreversible"):
        print("错误：--reversibility 必须为 reversible 或 irreversible。", file=sys.stderr)
        return 2

    lib = load_biases(args.biases)
    # 根据情境文本预检可能偏差，作为失败模式候选
    hints = detect_biases(context, lib)
    by_id = {b["id"]: b for b in lib["biases"]}

    slug = re.sub(r"[^\w一-鿿]+", "_", context)[:24].strip("_") or "decision"
    kind = ("不可逆(单向门)" if reversibility == "irreversible"
            else ("可逆(双向门)" if reversibility == "reversible" else "未指定"))

    lines = []
    lines.append("# 事前验尸 Pre-Mortem · %s" % context)
    lines.append("")
    lines.append("- 生成时间：%s" % now_iso())
    lines.append("- 决策可逆性：%s" % kind)
    lines.append("")
    lines.append("## 第一步：假设已经失败")
    lines.append("> 想象现在是未来，这个决定已经导致了**最糟糕的结果**。")
    lines.append("> 不要为它辩护，先接受失败是事实，然后倒推：*为什么会走到这一步？*")
    lines.append("")
    lines.append("## 第二步：反推失败原因（从偏差库中筛出的可能失败模式）")
    if hints:
        for bid in hints:
            b = by_id.get(bid, {})
            lines.append("- **%s**：%s" % (b.get("name_cn", bid), b.get("premortem_angle", "")))
    else:
        for b in lib["biases"][:6]:
            lines.append("- **%s**：%s" % (b["name_cn"], b.get("premortem_angle", "")))
    lines.append("")
    lines.append("## 第三步：二阶思考（Howard Marks）")
    lines.append("- 一阶结果（立刻看到的）：这个决定直接会带来什么？")
    lines.append("- 二阶结果（别人反应后的连锁）：相关方会如何回应？市场/关系/自我会怎么变？")
    lines.append("- 三阶结果（回应之回应）：二阶结果又会引发什么？")
    lines.append("- 关键问题：*大家都看得见的『好』，其二阶代价是否被低估了？*")
    lines.append("")
    lines.append("## 第四步：可逆性校验（Bezos 单向门/双向门）")
    if reversibility == "irreversible":
        lines.append("- 这是**单向门**：走过去就回不来。标准应更高——")
        lines.append("  只有在『不做会更后悔』时才走，且需先完成上面三步。")
    elif reversibility == "reversible":
        lines.append("- 这是**双向门**：走错了可以退回来。可降低决策成本，先小步试错。")
    else:
        lines.append("- 先判断可逆性：多数『看似不可逆』其实有退出路径，明确退出成本再决定。")
    lines.append("")
    lines.append("## 第五步：后悔最小化")
    lines.append("- 问自己：*80 岁的我，会更后悔『做了』还是『没做』这个决定？*")
    lines.append("- 把答案写下来，作为越过决策疲劳（Baumeister）时的锚点。")

    report = "\n".join(lines) + "\n"
    ensure_store(args.store)
    pm_path = os.path.join(args.store, "premortem-%s.md" % slug)
    with open(pm_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print("事前验尸已写：%s" % pm_path)
    return 0


# ----------------------------------------------------------------------------
# 子命令：list
# ----------------------------------------------------------------------------
def cmd_list(args):
    entries = load_log(args.store)
    if not entries:
        print("尚无决策记录。")
        return 0
    print("已记录 %d 条决策：" % len(entries))
    for e in entries:
        rev = e.get("reversibility", "?")
        done = "已回放" if e.get("score") is not None else "未回放"
        print("  %s | %s | %s | %s | %s"
              % (e["id"], rev, done, e.get("context", ""), e.get("chosen", "")))
    return 0


# ----------------------------------------------------------------------------
# 子命令：frameworks
# ----------------------------------------------------------------------------
def cmd_frameworks(args):
    lib = load_frameworks(args.frameworks)
    fra = lib.get("frameworks", [])
    if args.id:
        hit = next((f for f in fra if f.get("id") == args.id), None)
        if not hit:
            print("错误：未找到框架 %s。" % args.id, file=sys.stderr)
            return 2
        print("# %s（%s）" % (hit["name_cn"], hit["name_en"]))
        print("- 提出者：%s" % hit.get("originator", "—"))
        print("- 一句话：%s" % hit.get("one_liner", ""))
        print("- 何时用：%s" % hit.get("when_to_use", ""))
        print("- 步骤：")
        for i, s in enumerate(hit.get("steps", []), 1):
            print("  %d. %s" % (i, s))
        print("- 理论长文：%s" % hit.get("links_to_theory", ""))
        return 0
    print("决策框架库（v%s），共 %d 个。用 --id <id> 查看详情：" % (lib.get("version", "?"), len(fra)))
    for f in fra:
        print("  - %s：%s — %s" % (f["id"], f["name_cn"], f.get("one_liner", "")))
    return 0


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------
def build_parser():
    p = argparse.ArgumentParser(prog="decide", description="self-decide-agent 决策日志/回放评分引擎")
    p.add_argument("--store", default=DEFAULT_STORE, help="数据目录（默认 .self-decide）")
    sub = p.add_subparsers(dest="cmd")

    pl = sub.add_parser("log", help="记录一次决策")
    pl.add_argument("--context", help="决策情境：要决定什么")
    pl.add_argument("--options", default="", help="候选选项，分号分隔，如 'A;B;C'")
    pl.add_argument("--chosen", default="", help="所选的选项")
    pl.add_argument("--expected", default="", help="预期结果")
    pl.add_argument("--reversibility", default="", help="reversible(可逆/双向门) | irreversible(不可逆/单向门)")
    pl.add_argument("--tags", default="", help="补充标签，逗号分隔")
    pl.add_argument("--framework", default="", help="所用决策框架 id（见 frameworks 子命令）")
    pl.add_argument("--biases", default=None, help="偏差库路径")

    pr = sub.add_parser("replay", help="回放一次决策并打分")
    pr.add_argument("--id", help="决策 id（默认最新）")
    pr.add_argument("--actual", default=None, help="实际发生的结果描述（必填）")
    pr.add_argument("--outcome", default=None, help="实际影响/损失简述")
    pr.add_argument("--score", default=None, help="预期达成度/满意度 0-100")
    pr.add_argument("--regret", default=None, help="后悔度 0-100，缺省=100-score")
    pr.add_argument("--reversibility", default=None, help="回放纠正的可逆性（检测误判）")

    pb = sub.add_parser("bias", help="识别反复出现的决策偏差")
    pb.add_argument("--biases", default=None, help="偏差库路径")

    pp = sub.add_parser("report", help="决策质量报告")
    pp.add_argument("--biases", default=None, help="偏差库路径")

    pm = sub.add_parser("premortem", help="事前验尸 pre-mortem")
    pm.add_argument("--context", help="决策情境")
    pm.add_argument("--reversibility", default="", help="reversible | irreversible（可选，用于校验）")
    pm.add_argument("--biases", default=None, help="偏差库路径")

    pf = sub.add_parser("frameworks", help="列出/查看决策框架库")
    pf.add_argument("--id", default=None, help="框架 id（缺省列出全部）")
    pf.add_argument("--frameworks", default=None, help="框架库路径")

    pls = sub.add_parser("list", help="列出已记录决策")
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
        "replay": cmd_replay,
        "bias": cmd_bias,
        "report": cmd_report,
        "premortem": cmd_premortem,
        "frameworks": cmd_frameworks,
        "list": cmd_list,
    }
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
