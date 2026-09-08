#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""self-verify-agent 的核心引擎：验证门禁 / 步骤核对 / 证伪探针 / 清单 / 记录。

设计原则（与 self-evaluate / self-debug 同源）：
- 只验证、不改东西：拦下、点名、给证据，不替用户写补丁。
- 中文报错、明确退出码：门禁不通过一律 exit 1，通过 exit 0。
- 零外部依赖：纯标准库，能在任何 Python 3.8+ 环境跑。
- 开关式 CLI：所有动作以 --xxx 形式调用，与文档示例一致。
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time

LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "verify_log.jsonl")
RES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "verify_checks.json")


class PreflightError(Exception):
    """预检失败：参数非法或环境不满足，用中文明确告知。"""

    def __init__(self, msg):
        super().__init__("【预检未过】" + msg)


def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _append_log(record):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _load_checks():
    if not os.path.exists(RES_PATH):
        raise PreflightError("找不到 resources/verify_checks.json，无法加载验证清单。")
    try:
        with open(RES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise PreflightError("验证清单解析失败：" + str(e))


# ----------------------------------------------------------------------------
# 1) gate：把命令当门禁跑，解析失败模式，物理拦下
# ----------------------------------------------------------------------------
FAIL_PATTERNS = [
    (r"Traceback \(most recent call last\)", "Python 异常栈"),
    (r"\bError\b|\bException\b", "出现 Error/Exception 字样"),
    (r"断言失败|assert.*failed|AssertionError", "断言失败"),
    (r"FAILED|✗|❌|失败", "显式失败标记"),
    (r"panic:|fatal:", "致命错误"),
]


def cmd_gate(command, expect_pass=True, timeout=60):
    if not command or not command.strip():
        raise PreflightError("门禁命令不能为空。")
    print("【门禁】执行：%s" % command)
    print("【门禁】预期方向：%s" % ("应通过(退出码0)" if expect_pass else "应失败(退出码非0)"))
    try:
        proc = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        print("【门禁·拦下】超时（>%d 秒），视为不通过。" % timeout)
        _append_log({"t": _now(), "action": "gate", "command": command, "result": "timeout"})
        return 1
    out = (proc.stdout or "") + (proc.stderr or "")
    rc = proc.returncode
    hits = []
    for pat, label in FAIL_PATTERNS:
        for m in re.finditer(pat, out):
            snippet = out[max(0, m.start() - 30):m.start() + 60].replace("\n", " ")
            hits.append((label, snippet.strip()))
            break
    passed = (rc == 0)
    ok = passed and not hits if expect_pass else (not passed) or bool(hits)
    print("【门禁】命令退出码：%d" % rc)
    if hits:
        print("【门禁】检测到 %d 处失败信号：" % len(hits))
        for label, snippet in hits[:5]:
            print("   - %s：…%s…" % (label, snippet))
    if ok:
        print("【门禁·通过】✅ 未触发失败模式，可以交付/继续。")
        _append_log({"t": _now(), "action": "gate", "command": command, "result": "pass"})
        return 0
    print("【门禁·拦下】❌ 未达预期，物理拦截，停止交付。")
    _append_log({"t": _now(), "action": "gate", "command": command, "result": "block"})
    return 1


# ----------------------------------------------------------------------------
# 2) stepcheck：把推理拆步骤，逐条点名是否成立（PRM 风格）
# ----------------------------------------------------------------------------
SUSPECT_WORDS = ["应该", "大概", "可能", "也许", "估计", "似乎", "没问题吧", "应该没问题",
                 "probably", "maybe", "should be", "i think", "我猜", "差不多"]
UNFOUNDED_PAT = re.compile(r"(没有证据|缺乏依据|未经检验|假设.*成立|默认.*正确)")


def cmd_stepcheck(text):
    if not text or not text.strip():
        raise PreflightError("待核对的推理文本不能为空。")
    raw_steps = re.split(r"\n+|(?:(?:^|\n)\s*(?:\d+[.、]|[-*]\s))", text)
    steps = [s.strip() for s in raw_steps if s and s.strip()]
    if not steps:
        steps = [s.strip() for s in text.split("。") if s.strip()]
    print("【步骤核对】共拆出 %d 步：" % len(steps))
    dubious = 0
    for i, step in enumerate(steps, 1):
        reasons = []
        if any(w in step.lower() for w in SUSPECT_WORDS):
            reasons.append("含不确定措辞（应该/大概/可能…），未独立证实")
        if UNFOUNDED_PAT.search(step):
            reasons.append("显式声明了未经检验的假设")
        if len(step) < 6:
            reasons.append("过短，可能是口号而非论证")
        verdict = "存疑" if reasons else "成立（需外部确认）"
        if reasons:
            dubious += 1
        print("  步骤 %d [%s]：%s" % (i, verdict, step[:50] + ("…" if len(step) > 50 else "")))
        for r in reasons:
            print("        ↳ %s" % r)
    print("【步骤核对】%d/%d 步存疑。" % (dubious, len(steps)))
    if dubious:
        print("【步骤核对·提示】存疑步就是验证重点：要么补证据，要么走证伪探针推翻它。")
    return 0 if dubious == 0 else 1


# ----------------------------------------------------------------------------
# 3) probe：证伪与边界探针
# ----------------------------------------------------------------------------
ABSOLUTE_WORDS = ["一定", "必然", "所有", "永远", "绝对", "100%", "从不", "always",
                  "never", "all", "definitely", "certainly"]
EDGE_HINTS = ["边界", "极端", "空", "零", "负数", "超大", "并发", "超时", "权限", "异常"]


def cmd_probe(text):
    if not text or not text.strip():
        raise PreflightError("待探针的结论/产出不能为空。")
    print("【证伪探针】针对：%s" % (text[:60] + ("…" if len(text) > 60 else "")))
    findings = []
    for w in ABSOLUTE_WORDS:
        if w in text.lower():
            findings.append("绝对化措辞「%s」——试着举一个反例推翻它" % w)
    if re.search(r"(因为.*所以|如果.*就|显然|众所周知)", text):
        findings.append("含『显然/因为所以/如果就』等跳跃，底层假设可能未证")
    missing_edge = [h for h in EDGE_HINTS if h not in text]
    if missing_edge:
        findings.append("文本未触及边界条件（如 %s），考虑补一个极端用例" %
                        "、".join(missing_edge[:3]))
    if not findings:
        print("【证伪探针】未发现明显可被推翻的薄弱点，但仍建议做一次自洽性检查。")
        return 0
    print("【证伪探针】发现 %d 处可能被推翻的薄弱点：" % len(findings))
    for f in findings:
        print("   - %s" % f)
    return 1


# ----------------------------------------------------------------------------
# 4) checks：加载清单逐类核对
# ----------------------------------------------------------------------------
def cmd_checks(class_name):
    data = _load_checks()
    classes = data.get("classes", {})
    if class_name and class_name not in classes:
        raise PreflightError("清单里没有「%s」这一类，可选：%s" % (class_name, "、".join(classes.keys())))
    targets = {class_name: classes[class_name]} if class_name else classes
    total = 0
    for cname, spec in targets.items():
        print("【清单·%s】%s" % (cname, spec.get("desc", "")))
        for item in spec.get("items", []):
            total += 1
            print("   ☐ %s" % item)
    print("【清单】共 %d 项待查（逐项由门禁/步骤/探针落实）。" % total)
    return 0


# ----------------------------------------------------------------------------
# 5) record：记一条验证命中率样本
# ----------------------------------------------------------------------------
def cmd_record(conclusion, outcome):
    if outcome not in (0, 1):
        raise PreflightError("--record 的 outcome 只能是 0(后来证明错)或 1(后来证明对)。")
    _append_log({"t": _now(), "action": "record", "conclusion": conclusion,
                 "outcome": "correct" if outcome == 1 else "wrong"})
    print("【记录】已记：验证结论「%s」→ 后来证明%s" %
          (conclusion, "正确" if outcome == 1 else "错误（说明这次验证漏了，下次加强）"))
    return 0


def build_parser():
    p = argparse.ArgumentParser(
        description="self-verify-agent 验证门禁引擎（中文输出，门禁不通过退出码 1）。")
    p.add_argument("--gate", action="store_true", help="把命令当门禁跑，不通过物理拦下")
    p.add_argument("--command", default=None, help="要跑的命令（会被 shell 执行）")
    p.add_argument("--expect-pass", dest="expect_pass", action="store_true", default=True)
    p.add_argument("--expect-fail", dest="expect_pass", action="store_false")
    p.add_argument("--timeout", type=int, default=60)
    p.add_argument("--stepcheck", action="store_true", help="把推理拆步骤逐条点名是否成立")
    p.add_argument("--probe", action="store_true", help="证伪与边界探针")
    p.add_argument("--text", default=None, help="待核对/探针的文本")
    p.add_argument("--checks", nargs="?", const="ALL", default=None, help="加载验证清单（可跟类名）")
    p.add_argument("--record", default=None, help="记一条验证命中率样本（结论文本）")
    p.add_argument("outcome", nargs="?", type=int, default=None, help="--record 的 0/1 结果")
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.gate:
            return cmd_gate(args.command, args.expect_pass, args.timeout)
        if args.stepcheck:
            return cmd_stepcheck(args.text)
        if args.probe:
            return cmd_probe(args.text)
        if args.checks is not None:
            cls = None if args.checks == "ALL" else args.checks
            return cmd_checks(cls)
        if args.record is not None:
            if args.outcome not in (0, 1):
                raise PreflightError("--record 需要末尾跟 0(错)或 1(对)。")
            return cmd_record(args.record, args.outcome)
    except PreflightError as e:
        print(str(e), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("【中断】用户终止。", file=sys.stderr)
        return 130
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
