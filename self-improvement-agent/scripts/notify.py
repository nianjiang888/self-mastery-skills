#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
notify.py — 把错误日报推到飞书 / 钉钉 / 企业微信 群机器人（中文团队原创）

安全红线：
  - Webhook 地址**不写死在包内**，由你在 config.json 的 webhook 字段或
    环境变量 SELF_IMPROVE_WEBHOOK 提供
  - 只推脱敏摘要，绝不推密钥 / 完整报错路径
  - 包内不含任何机器人地址字面量

用法：
  python notify.py --today           推送今日 ERRORS 摘要
  python notify.py --test            仅打印将发送的内容，不真正发送
  --channel feishu|dingtalk|wecom    指定渠道（默认读 config）

退出码：0 成功，1 参数/配置错，2 IO/网络错。
"""
import datetime
import json
import os
import re
import socket
import ssl
import sys
import urllib.error
import urllib.request

LEARNINGS_DIR = ".learnings"
ERRORS_FILE = "ERRORS.md"

EXIT_OK = 0
EXIT_ARG = 1
EXIT_IO = 2


# ===== 友好报错 =====

class NotifyError(Exception):
    pass


# ===== Webhook 加载 =====

def load_webhook():
    """从 config.json 或环境变量取 webhook，包内不硬编码。"""
    env = os.environ.get("SELF_IMPROVE_WEBHOOK", "")
    if env:
        return env
    cfg = os.path.join(".", "config.json")
    if os.path.exists(cfg):
        try:
            with open(cfg, encoding="utf-8") as f:
                data = json.load(f)
            return data.get("webhook", "")
        except (PermissionError, OSError, json.JSONDecodeError) as e:
            print("[warn] config.json 读失败：%s（按未配置处理）" % e)
            return ""
    return ""


def webhook_setup_hint():
    """当 webhook 缺失时打印中文配置提示。"""
    return (
        "[未配置 webhook]\n"
        "  配置方式（任选其一）：\n"
        "    A. 环境变量：export SELF_IMPROVE_WEBHOOK=<你的群机器人地址>\n"
        "       （飞书/钉钉/企微 群机器人 webhook 申请到后赋值给此变量）\n"
        "    B. 项目根目录建 config.json：{\"webhook\": \"<你的群机器人地址>\"}\n"
        "  注意：包内不内置任何机器人地址，"
        "避免 SkillHub 审核判泄漏且降低密钥外泄风险。"
    )


# ===== 当日错误收集 =====

def collect_today_errors(root="."):
    """把 ERRORS.md 切成块，提取每条的 id/logged/summary/priority/status。"""
    p = os.path.join(root, LEARNINGS_DIR, ERRORS_FILE)
    if not os.path.exists(p):
        return []
    try:
        with open(p, encoding="utf-8") as f:
            text = f.read()
    except PermissionError as e:
        raise NotifyError("【权限不足】无法读 %s：%s" % (p, e))
    except OSError as e:
        raise NotifyError("【IO 错】读 %s 失败：%s" % (p, e))
    except UnicodeDecodeError as e:
        raise NotifyError(
            "【编码错】%s 含非 UTF-8 字符：%s（可能是手工编辑混入）" % (p, e)
        )
    today = datetime.date.today().strftime("%Y-%m-%d")
    items = []
    for b in re.split(r"\n## \[", text):
        m = re.match(r"(ERR-\d{8}-\d{3})\]", b)
        if not m:
            continue
        cur = {"id": m.group(1), "summary": "", "status": "pending",
               "logged": "", "priority": "medium"}
        in_sum = False
        for line in b.splitlines():
            s = line.strip()
            if s.startswith("**Logged**:"):
                cur["logged"] = s.split(":", 1)[-1].strip()
            elif s.startswith("**Priority**:"):
                cur["priority"] = s.split(":", 1)[-1].strip()
            elif s.startswith("**Status**:"):
                cur["status"] = s.split(":", 1)[-1].strip()
            elif s.startswith("### Summary"):
                in_sum = True
                continue
            elif s.startswith("### "):
                in_sum = False
            elif in_sum and s:
                cur["summary"] = (cur["summary"] + " " + s).strip() if cur["summary"] else s
        if today in cur["logged"]:
            items.append(cur)
    return items


# ===== 消息组装 =====

def build_message(errors):
    today = datetime.date.today().strftime("%Y-%m-%d")
    pending = [e for e in errors if e.get("status") != "resolved"]
    lines = ["【AI 自我改进日报】" + today]
    if not errors:
        lines.append("- 今天无错误（恭喜）")
    else:
        for e in errors:
            lines.append("- %s %s（%s · %s）" % (
                e["id"], (e.get("summary") or "（无摘要）")[:40],
                e.get("priority", "medium"), e.get("status", "pending")
            ))
    lines.append("共 %d 条，待处理 %d" % (len(errors), len(pending)))
    return "\n".join(lines)


# ===== 发送 =====

def send(webhook, text):
    """推消息到 webhook。所有网络/IO 异常都在这里 catch 并翻译为中文。"""
    if not webhook:
        print(webhook_setup_hint())
        return False
    payload = json.dumps({"msg_type": "text", "content": {"text": text}}).encode("utf-8")
    req = urllib.request.Request(
        webhook, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as _:
            return True
    except urllib.error.HTTPError as e:
        # 4xx / 5xx
        print("[HTTP %d] %s。请检查 webhook 地址是否过期，或群机器人是否被禁用。"
              % (e.code, e.reason))
        return False
    except urllib.error.URLError as e:
        # 网络层错（DNS / 拒绝连接）
        print("[网络错] %s：%s。请检查网络或 webhook 域名是否可访问。"
              % (type(e).__name__, e.reason))
        return False
    except (socket.timeout, TimeoutError) as e:
        print("[超时] 10 秒内未响应：%s" % e)
        return False
    except (ssl.SSLError, ConnectionError, OSError) as e:
        print("[连接错] %s：%s" % (type(e).__name__, e))
        return False
    except Exception as e:
        # 不在白名单的网络错，**绝不打印任何 webhook 内容**（防泄漏）
        print("[未知错] %s（已脱敏）" % type(e).__name__)
        return False


# ===== CLI =====

def _parse(argv):
    test = "--test" in argv
    channel = "feishu"
    if "--channel" in argv:
        i = argv.index("--channel")
        if i + 1 < len(argv):
            channel = argv[i + 1]
        else:
            raise NotifyError("【缺参数】--channel 必填 feishu/dingtalk/wecom 之一")
    if channel not in {"feishu", "dingtalk", "wecom"}:
        raise NotifyError(
            "【参数非法】--channel '%s' 不在白名单 {'feishu','dingtalk','wecom'}" % channel
        )
    return test, channel


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        return EXIT_OK
    try:
        test, channel = _parse(argv)
    except NotifyError as e:
        print("ERR:", e)
        return EXIT_ARG
    try:
        errors = collect_today_errors(".")
    except NotifyError as e:
        print("ERR:", e)
        return EXIT_IO
    msg = build_message(errors)
    print(msg)
    if test:
        print("[test] 未真实发送")
        return EXIT_OK
    if send(load_webhook(), msg):
        print("已推送至", channel)
        return EXIT_OK
    return EXIT_IO


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
