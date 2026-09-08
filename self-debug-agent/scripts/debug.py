#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""self-debug-agent 调试引擎：复现 / 归类 / 治愈循环 / 自动回归。

脚本定位是「纪律引擎」，不是补丁生成器：
- 复现萃取：把模糊报错变成最小失败事实
- 归类探针：按 bug_taxonomy.json 把 bug 归到六类并给证据
- 治愈循环：失败 -> 根因反思 -> 重试行，记 heal_log.jsonl
- 自动免疫：把每个 bug 落成永久回归测试脚手架

真正写补丁的是人或编程 Agent；本脚本保证过程有证据、能收敛、留抗体。
"""
import sys
import os
import re
import json
import subprocess
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TAXONOMY_PATH = os.path.join(ROOT, "resources", "bug_taxonomy.json")
HEAL_LOG = os.path.join(ROOT, "heal_log.jsonl")
REGRESS_LOG = os.path.join(ROOT, "regression_log.jsonl")

# 退出码：纪律优先
EXIT_OK = 0
EXIT_PREFlight = 1          # 前置条件不满足（如没复现就修）
EXIT_NO_REPRO = 2           # 无法复现
EXIT_NOT_CONVERGED = 3      # 治愈轮数耗尽仍未收敛
EXIT_BAD_ARGS = 4


class PreflightError(Exception):
    """前置纪律被破坏时抛出，统一走中文报错 + 退出码 1。"""


def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _load_taxonomy():
    if not os.path.exists(TAXONOMY_PATH):
        raise PreflightError("找不到 bug_taxonomy.json（%s），无法归类。" % TAXONOMY_PATH)
    with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _read(path):
    if not path or not os.path.exists(path):
        raise PreflightError("文件不存在：%s" % path)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _parse_traceback(trace_text):
    """从 traceback 文本里萃取错误类型、消息、失败行、帧栈。"""
    info = {"error_type": None, "message": None, "failing_line": None,
            "frames": [], "raw": trace_text}
    m = re.search(r"(\w+(?:Error|Exception|Warning)):\s*(.*)", trace_text)
    if m:
        info["error_type"] = m.group(1)
        info["message"] = m.group(2).strip()
    # 帧：File "x", line N, in func（标准 traceback 的失败行在最后一帧）
    for fm in re.finditer(r'File "([^"]+)", line (\d+), in (.+)', trace_text):
        info["frames"].append({"file": fm.group(1), "line": int(fm.group(2)), "func": fm.group(3)})
    if info["frames"]:
        info["failing_line"] = info["frames"][-1]["line"]
    else:
        lm = re.search(r"line (\d+)", trace_text)
        if lm:
            info["failing_line"] = int(lm.group(1))
    return info


def _minimal_repro(trace_text, code_text):
    """提炼最小失败事实：错误类型 + 失败行 + 该行源码（若有）。"""
    ti = _parse_traceback(trace_text)
    line_src = None
    if ti["failing_line"] and code_text:
        code_lines = code_text.splitlines()
        if 1 <= ti["failing_line"] <= len(code_lines):
            line_src = code_lines[ti["failing_line"] - 1].strip()
    repro = {
        "error_type": ti["error_type"] or "未知错误",
        "message": ti["message"] or "（无消息）",
        "failing_line": ti["failing_line"],
        "failing_line_source": line_src,
        "reproducible": ti["error_type"] is not None,
    }
    return repro, ti


def cmd_reproduce(trace, code):
    trace_text = _read(trace)
    code_text = _read(code) if code else ""
    repro, _ = _minimal_repro(trace_text, code_text)
    if not repro["reproducible"]:
        print("【复现失败】无法从报错中识别错误类型，复现不了就不算 bug。")
        print("请确认 trace 文本包含完整的 traceback（含 Error/Exception 类型）。")
        return EXIT_NO_REPRO
    print("【复现事实】")
    print("  错误类型 : %s" % repro["error_type"])
    print("  错误消息 : %s" % repro["message"])
    print("  失败行号 : %s" % repro["failing_line"])
    if repro["failing_line_source"]:
        print("  该行源码 : %s" % repro["failing_line_source"])
    print("  可复现   : 是")
    return EXIT_OK


def cmd_classify(trace, code):
    """用 taxonomy 的签名探针给 bug 归类，输出证据 + 根因 + 建议修法。"""
    trace_text = _read(trace)
    code_text = _read(code) if code else ""
    ti = _parse_traceback(trace_text)
    tax = _load_taxonomy()

    hits = []
    combined_lower = (trace_text + "\n" + code_text).lower()
    for btype, spec in tax.get("types", {}).items():
        evidence = []
        for sig in spec.get("signatures", []):
            # 签名可能是 "a|b|c" 形式的多候选，逐段做子串匹配（避免裸正则崩）
            for alt in sig.split("|"):
                alt = alt.strip()
                if not alt:
                    continue
                idx = combined_lower.find(alt.lower())
                if idx >= 0:
                    snippet = combined_lower[idx:idx + len(alt)]
                    ctx = ""
                    if code_text and alt.lower() in code_text.lower():
                        ln = [i for i, l in enumerate(code_text.splitlines(), 1)
                              if alt.lower() in l.lower()][0]
                        ctx = "（代码第 %d 行）" % ln
                    evidence.append(snippet + ctx)
                    break
            if len(evidence) >= 3:
                break
        if evidence:
            hits.append((btype, spec, evidence))

    if not hits:
        print("【归类】未命中任何已知签名。建议作为『待验证假设』手工排查：")
        print("  - 检查是否环境/数据导致（非代码逻辑）")
        print("  - 用 --reproduce 拿到的失败行，逐行读执行语义")
        return EXIT_OK

    print("【归类结果】按命中证据数排序：")
    hits.sort(key=lambda h: len(h[2]), reverse=True)
    for btype, spec, evidence in hits[:3]:
        print("\n  类别 : %s（%s）" % (btype, spec.get("label", "")))
        print("  证据 : " + " / ".join(evidence[:3]))
        print("  根因 : " + spec.get("root_cause", "（未定义）"))
        print("  修法 : " + spec.get("fix_pattern", "（未定义）"))
    print("\n提示：用 scripts/localize.py 按覆盖率给每一行算可疑度，进一步锁死病灶。")
    return EXIT_OK


def cmd_heal(trace, code, max_rounds):
    """治愈循环：失败 -> 根因反思 -> 重试行。脚本管记账，人/模型管补丁。"""
    if not trace or not code:
        raise PreflightError("治愈循环需要 --trace 与 --code 同时给出。")
    ti = _parse_traceback(_read(trace))
    if ti["error_type"] is None:
        raise PreflightError("复现不了（无错误类型），按纪律不进入治愈循环。先 --reproduce。")

    print("【治愈循环】最多 %d 轮。纪律：每轮必须记录根因反思与证据。" % max_rounds)
    print("（本脚本负责记账与校验；请在此循环里由你或编程 Agent 实际修改 %s）" % code)
    for r in range(1, max_rounds + 1):
        print("\n--- 第 %d 轮 ---" % r)
        print("  请完成：①读失败行 ②写候选补丁 ③运行 --verify 验证")
        print("  若未收敛，记录根因反思后进入下一轮。")
        entry = {
            "ts": _now(), "round": r,
            "error_type": ti["error_type"],
            "failing_line": ti["failing_line"],
            "status": "pending_your_fix",
        }
        with open(HEAL_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print("\n已为 %d 轮建立治愈台账（%s）。轮次到上限后仍未收敛请如实报告卡点。" % (max_rounds, HEAL_LOG))
    return EXIT_OK


def cmd_verify(test_cmd):
    if not test_cmd:
        raise PreflightError("需要 --test 指定验证命令（如 'pytest -q'）。")
    print("【验证】运行：%s" % test_cmd)
    rc = subprocess.call(test_cmd, shell=True)
    if rc == 0:
        print("  结果：通过 ✅ 修复成立。")
        return EXIT_OK
    print("  结果：失败 ❌（退出码 %d）。回到治愈循环反思根因。" % rc)
    return EXIT_NOT_CONVERGED


def cmd_regress(bug, case, expect):
    """把 bug 落成永久回归测试脚手架（确定性断言）。"""
    if not bug or not case or not expect:
        raise PreflightError("需要 --bug / --case / --expect 三者齐全才能生成回归测试。")
    # 纪律：禁止脆弱断言特征
    fragile = ["random", "time.time", "datetime.now", "uuid", "网络", "http"]
    low = (case + expect).lower()
    for kw in fragile:
        if kw in low:
            raise PreflightError("回归测试含脆弱特征「%s」。断言必须确定性：固定输入->固定期望。" % kw)
    test_name = "test_regress_" + re.sub(r"\W+", "_", bug)[:40].strip("_")
    scaffold = (
        "def %s():\n"
        "    # 回归：%s\n"
        "    # 输入: %s\n"
        "    # 期望: %s\n"
        "    result = None  # TODO: 调用被测函数\n"
        "    assert result == expected  # TODO: 填期望\n"
    ) % (test_name, bug, case, expect)
    entry = {"ts": _now(), "bug": bug, "case": case,
             "expect": expect, "test_name": test_name}
    with open(REGRESS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print("【免疫】已记录永久回归测试条目：")
    print(scaffold)
    print("（已写入 %s；请把上面脚手架补完，落到你的测试套件，bug 就再不能复发。）" % REGRESS_LOG)
    return EXIT_OK


def cmd_report():
    print("【治愈台账】%s" % HEAL_LOG)
    if os.path.exists(HEAL_LOG):
        n = 0
        for line in open(HEAL_LOG, encoding="utf-8"):
            n += 1
            e = json.loads(line)
            print("  %s | 轮%d | %s @L%s | %s" % (
                e["ts"], e["round"], e["error_type"], e.get("failing_line"), e["status"]))
        print("  共 %d 条治愈记录。" % n)
    else:
        print("  （空）")
    print("\n【回归墙】%s" % REGRESS_LOG)
    if os.path.exists(REGRESS_LOG):
        n = 0
        for line in open(REGRESS_LOG, encoding="utf-8"):
            n += 1
            e = json.loads(line)
            print("  %s | %s" % (e["test_name"], e["bug"]))
        print("  共 %d 条永久抗体。" % n)
    else:
        print("  （空）提示：每修一个 bug 跑一次 --regress，墙越厚越不会重复踩坑。")
    return EXIT_OK


def _parse_argv(argv):
    cmd = None
    opts = {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith("--"):
            key = a[2:]
            if key in ("reproduce", "classify", "heal", "verify", "regress", "report"):
                cmd = key
                i += 1
                continue
            # 取值参数
            val = ""
            if "=" in a:
                key, val = a[2:].split("=", 1)
            elif i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                val = argv[i + 1]
                i += 1
            opts[key] = val
            i += 1
        else:
            i += 1
    return cmd, opts


def main(argv):
    try:
        cmd, opts = _parse_argv(argv)
        if cmd == "reproduce":
            return cmd_reproduce(opts.get("trace"), opts.get("code"))
        if cmd == "classify":
            return cmd_classify(opts.get("trace"), opts.get("code"))
        if cmd == "heal":
            mr = int(opts.get("max-rounds") or "5")
            return cmd_heal(opts.get("trace"), opts.get("code"), mr)
        if cmd == "verify":
            return cmd_verify(opts.get("test"))
        if cmd == "regress":
            return cmd_regress(opts.get("bug"), opts.get("case"), opts.get("expect"))
        if cmd == "report":
            return cmd_report()
        print("用法：debug.py --reproduce|--classify|--heal|--verify|--regress|--report [选项]")
        print("  --reproduce --trace <文件> [--code <文件>]")
        print("  --classify  --trace <文件> [--code <文件>]")
        print("  --heal      --trace <文件> --code <文件> [--max-rounds N]")
        print("  --verify    --test <命令>")
        print("  --regress   --bug <描述> --case <输入> --expect <期望>")
        print("  --report")
        return EXIT_BAD_ARGS
    except PreflightError as e:
        print("【纪律拦截】%s" % e, file=sys.stderr)
        return EXIT_PREFlight
    except FileNotFoundError as e:
        print("【文件缺失】%s" % e, file=sys.stderr)
        return EXIT_PREFlight


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
