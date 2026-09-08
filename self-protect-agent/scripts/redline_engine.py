#!/usr/bin/env python3
# redline_engine.py — 红线规则引擎（确定性代码闸门）
#
# 设计原则（详见 references/redline-design.md）：
#   1. 红线由"确定性代码"判断，不靠模型自觉。prompt 层面的"别做危险事"是最弱的防御。
#   2. allowlist 优先于 blocklist：默认拒绝，只放行枚举项。
#   3. 命中按 level 分级：block(阻断) / warn(警告需确认) / info(提示)。
#   4. 正则非法时退化为子串匹配，保证引擎自身不崩。
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

LEVEL_RANK = {"info": 1, "warn": 2, "block": 3}

# 受保护凭据路径片段：命中即视为触碰红线（无论命令是什么）
PROTECTED_PATH_FRAGMENTS = (
    ".ssh", ".env", "id_rsa", "id_dsa", "credentials", "credential",
    "secret", "secrets", "known_hosts", "authorized_keys", "token",
    "password", "passwd", ".pem", ".key", "private_key",
)


def load_redlines(path=None):
    """加载红线规则库。path 缺省用 resources/redlines.json。"""
    if path is None:
        path = os.path.join(HERE, "..", "resources", "redlines.json")
    path = os.path.abspath(path)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def scan_text(text, lib):
    """对文本逐规则匹配，返回命中规则列表（可能多条）。"""
    hits = []
    for rule in lib.get("rules", []):
        pat = rule.get("pattern")
        if not pat:
            continue
        mode = rule.get("match", "regex")
        try:
            if mode == "regex":
                if re.search(pat, text, re.IGNORECASE | re.MULTILINE):
                    hits.append(rule)
            elif mode == "contains":
                if pat.lower() in text.lower():
                    hits.append(rule)
        except re.error:
            # 正则非法 → 退化子串匹配，引擎不崩
            if pat.lower() in text.lower():
                hits.append(rule)
    return hits


_VERDICT_RANK = {"allow": 0, "confirm": 1, "block": 2}


def _max_verdict(*vs):
    return max(vs, key=lambda v: _VERDICT_RANK[v])


def check_command(command, lib):
    """对一条具体命令做预执行校验（确定性闸门）。

    返回 (verdict, reasons[])，verdict ∈ {allow, confirm, block}。
    - allow   : 在边界内，可自动执行
    - confirm : 需人工确认（不可逆 / 批量 / 对外发送 / 不在白名单）
    - block   : 高风险，物理拦截 + 报告，最终决定权仍留给人
    """
    reasons = []
    verdict = "allow"
    low = command.lower()

    # 1) 受保护凭据路径：任何触碰都升级为 block
    for frag in PROTECTED_PATH_FRAGMENTS:
        if frag in low:
            verdict = _max_verdict(verdict, "block")
            reasons.append(f"触碰受保护凭据路径片段: {frag}")

    # 2) 不可逆 / 批量破坏操作 → 至少 confirm
    if re.search(r"\brm\s+-rf\b", low) or re.search(r"drop\s+table", low) \
            or re.search(r"drop\s+database", low) \
            or re.search(r"truncate\s+table", low) \
            or re.search(r"terraform\s+destroy", low) \
            or re.search(r"kubectl\s+delete\s+(ns|namespace|all)", low) \
            or re.search(r":\(\s*\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", low):
        verdict = _max_verdict(verdict, "block")
        reasons.append("不可逆/批量破坏操作，已物理拦截，需人工显式确认")
    elif re.search(r"delete\s+from\s+\w+", low) \
            or re.search(r"git\s+reset\s+--hard", low) \
            or re.search(r"git\s+clean\s+-f", low) \
            or re.search(r"git\s+push\s+(-f|--force)", low) \
            or re.search(r"chmod\s+777", low) \
            or re.search(r"chmod\s+000", low) \
            or re.search(r"\bsudo\b|\bsu\b", low):
        verdict = _max_verdict(verdict, "confirm")
        reasons.append("不可逆或提权操作，需人工确认")

    # 3) 对外发送：邮件 / 转账 / 发布 / 外部 POST
    if re.search(r"(send|mail|transfer|publish|deploy)\b", low) \
            or re.search(r"curl\s+-X\s+POST", low):
        if re.search(r"(all|external|customer|public|@(?!localhost)|broadcast)", low):
            verdict = _max_verdict(verdict, "confirm")
            reasons.append("涉及对外发送，需人工确认发送范围")

    # 4) 管道下载即执行（供应链攻击入口，含 wget）
    if re.search(r"curl\s+.*\|\s*(sh|bash)|wget\s+.*(\||;)\s*(sh|bash)", low):
        verdict = _max_verdict(verdict, "confirm")
        reasons.append("管道下载即执行，需确认来源可信")

    # 5) allowlist 兜底：命令头不在白名单且尚未被升级 → 降级 confirm
    allow = lib.get("allowlist", [])
    head = command.strip().split()[0] if command.strip() else ""
    if allow and head and head not in allow and verdict == "allow":
        verdict = "confirm"
        reasons.append(f"命令 '{head}' 不在放行白名单，需确认")

    return verdict, reasons
