#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
self_improve.py — AI 自我改进主引擎（中文开发者版）
仅用标准库，无第三方依赖。

功能（CLI，按 USE 文档化）：
  --init                            初始化 .learnings/（no-op 若已存在）
  --learning --summary "<S>"        记一条 LEARNING
    [--category correction|insight|knowledge_gap|best_practice]
    [--details "<D>"] [--priority low|medium|high|critical]
    [--area frontend|backend|infra|tests|docs|config]
    [--pattern-key "<key>"]         用来查 recurrence
    [--source conversation|user_feedback|error]
  --error  --summary "<S>"          记一条 ERROR
    [--error-msg "<msg>"] [--context "<ctx>"]
    [--priority low|medium|high|critical]
  --feature --capability "<C>"      记一条 FEATURE_REQUEST
    [--context "<ctx>"] [--complexity simple|medium|complex]
  --promote --id "<LRN..>" --rule "<短规则>"
    [--target CLAUDE.md|AGENTS.md|SOUL.md|.github/copilot-instructions.md]
  --stats                           统计 pending 数（JSON）
  --recurrence --pattern-key "<k>"  查 Pattern-Key 重复次数（≥3 触发升级建议）
  --find "<关键词>"                 跨三个日志检索（高级筛选，可按 --category/--area 限定）
  --review                          周报式复盘：pending 数 + 高频模式 + 高优先级提醒
  --natural "<自然语言>"            用中文一句话，自动识别场景并记日志
  --can-do                          打印能力边界
  --use                             打印用法与典型示例（中文）

退出码：0 成功；1 参数错误；2 运行时错误（IO 失败/权限不足/磁盘满）；
       3 输入合法但命令未匹配。

设计原则（对应孔明 v1.1.0 升级经验）：
  - preflight() 集中校验，零静默吞参
  - 所有 IO 用 try/except 包，返回友好中文报错而非 stack
  - SCENE_HINTS 把"我又犯错了"等口语映射到对应子命令
  - --can-do 清楚列能/不能做
"""
import datetime
import json
import os
import re
import sys

# ===== 常量与配置（脱离 IO，纯函数友好）=====

LEARNINGS_DIR = ".learnings"
FILES = {
    "learning": "LEARNINGS.md",
    "error": "ERRORS.md",
    "feature": "FEATURE_REQUESTS.md",
}
HEADERS = {
    "learning": (
        "# Learnings\n\n"
        "纠正、洞察、知识缺口、最佳实践。\n\n"
        "**Categories**: correction | insight | knowledge_gap | best_practice\n\n---\n"
    ),
    "error": "# Errors\n\n命令失败与集成错误。\n\n---\n",
    "feature": "# Feature Requests\n\n用户想要的能力。\n\n---\n",
}
CATEGORIES = {"correction", "insight", "knowledge_gap", "best_practice"}
PRIORITIES = {"low", "medium", "high", "critical"}
AREAS = {"frontend", "backend", "infra", "tests", "docs", "config"}
COMPLEXITIES = {"simple", "medium", "complex"}
PROMOTE_TARGETS = {
    "convention": "CLAUDE.md",
    "workflow": "AGENTS.md",
    "behavior": "SOUL.md",
    "copilot": ".github/copilot-instructions.md",
}

# SCENE_HINTS：把用户中文自然语言识别成对应场景（前缀匹配）。
# 命中词只会影响 --natural；显式带 --learning/--error/--feature 时不触发。
SCENE_HINTS = [
    # (场景, [口语信号词], 推荐子命令, [参数提示])
    ("error", ["又报错", "出错了", "又崩了", "失败了", "报错了", "不对", "不行了", "挂了"],
     "error", ["summary=简短描述", "error-msg=报错原文"]),
    ("correction", ["不是", "应该用", "错了", "不对啊", "我说", "我之前教过", "我讲过", "记下", "记住了"],
     "learning", ["category=correction", "summary=纠正点", "details=上下文"]),
    ("feature", ["能不能", "可以不可以", "要是能", "我希望", "想要", "怎么不能", "为什么不能", "加个"],
     "feature", ["capability=想要什么"]),
    ("recurrence", ["出现过几次", "之前是不是有", "重复", "我教过你好多次", "又来了"],
     "recurrence", ["pattern-key=你要查的关键词"]),
    ("promote", ["升级", "推广到", "写到规则", "沉淀成规则", "放进 CLAUDE.md", "放进 AGENTS.md"],
     "promote", ["id=LRN-yyyymmdd-xxx", "rule=短规则", "target=CLAUDE.md"]),
]
# 自然语言→category 反向映射
NL_CATEGORY_HINTS = {
    "correction": ["纠正", "错了", "应该是", "记下", "我教过", "你忘了"],
    "knowledge_gap": ["不知道", "不清楚", "原来", "学到了", "刚明白"],
    "best_practice": ["技巧", "最佳", "推荐这样做", "以后就这样"],
    "insight": ["明白", "理解", "原来如此", "get 到"],
}

# 退出码
EXIT_OK = 0
EXIT_ARG = 1
EXIT_RUNTIME = 2
EXIT_UNKNOWN_CMD = 3


# ===== 友好报错与 preflight =====

class PreflightError(Exception):
    """参数/前置条件校验失败——给用户翻译过的话，不是 stacktrace。"""
    pass


def preflight_param(name, val, choices, allowed_empty=False):
    """必填参数校验：缺失或不在 choices 内 → 口语化中文报错（不生硬）。"""
    if not val:
        if allowed_empty:
            return ""
        example = list(choices)[0] if isinstance(choices, set) and choices else "..."
        raise PreflightError(
            "【还差一个参数】--%s 得填上。比如这样写：--%s '%s'。"
            % (name, name, example)
        )
    if isinstance(choices, set) and val not in choices:
        raise PreflightError(
            "【参数填错啦】--%s 只能从这几个里选：%s。你写的 '%s' 不在里面，换个试试？"
            % (name, sorted(choices), val)
        )
    return val


def preflight_writable(path):
    """目标路径是否可写（父目录存在 + 当前用户有写权限）。"""
    parent = os.path.dirname(path) or "."
    if not os.path.isdir(parent):
        try:
            os.makedirs(parent, exist_ok=True)
        except PermissionError as e:
            raise PreflightError(
                "【权限不足】无法创建目录 %s：%s。请检查磁盘权限或换路径。"
                % (parent, e)
            )
        except OSError as e:
            raise PreflightError("【IO 错】创建目录失败：%s" % e)
    if os.path.exists(path):
        if not os.access(path, os.W_OK):
            raise PreflightError("【权限不足】文件 %s 只读，无法写入。" % path)
        return path
    if not os.access(parent, os.W_OK):
        raise PreflightError("【权限不足】目录 %s 不可写。" % parent)
    return path


# ===== 实际日志操作（IO 全部包 try/except）=====

def now_iso():
    return datetime.datetime.now().isoformat(timespec="seconds")


def ensure_init(root="."):
    d = os.path.join(root, LEARNINGS_DIR)
    try:
        os.makedirs(d, exist_ok=True)
    except PermissionError as e:
        raise PreflightError("【权限不足】无法建 %s：%s" % (d, e))
    except OSError as e:
        raise PreflightError("【IO 错】建目录失败 %s：%s" % (d, e))
    for k, fn in FILES.items():
        p = os.path.join(d, fn)
        if not os.path.exists(p):
            try:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(HEADERS[k])
            except PermissionError as e:
                raise PreflightError("【权限不足】无法写 %s：%s" % (p, e))
            except OSError as e:
                raise PreflightError("【IO 错】初始化 %s 失败：%s" % (p, e))
    return d


def _next_seq(prefix, root="."):
    d = ensure_init(root)
    today = datetime.date.today().strftime("%Y%m%d")
    seq = 1
    pat = re.compile(r"## \[%s-%s-(\d{3})\]" % (re.escape(prefix), today))
    for fn in FILES.values():
        p = os.path.join(d, fn)
        if not os.path.exists(p):
            continue
        try:
            with open(p, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("## ["):
                        m = pat.match(line)
                        if m:
                            seq = max(seq, int(m.group(1)) + 1)
        except (PermissionError, OSError, UnicodeDecodeError) as e:
            # 文件暂时读不到——继续看其他文件，不中断
            print("[warn] 读 %s 失败：%s（忽略）" % (p, e))
    return "%s-%s-%03d" % (prefix, today, seq)


def _append(kind, body, root="."):
    d = ensure_init(root)
    p = os.path.join(d, FILES[kind])
    try:
        with open(p, "a", encoding="utf-8") as f:
            f.write("\n" + body + "\n")
    except PermissionError as e:
        raise PreflightError("【权限不足】写 %s 失败：%s" % (p, e))
    except OSError as e:
        # 磁盘满 / 文件被锁 / 跨设备链接
        raise PreflightError(
            "【IO 错】写 %s 失败：%s。请检查磁盘空间或文件是否被其他程序占用。" % (p, e)
        )
    return p


def log_learning(category, summary, details, priority="medium", area="docs",
                 source="conversation", pattern_key="", root="."):
    """记一条 LEARNING。返回 (id, err)；err 非空表示参数/运行错误（不写盘）。"""
    try:
        category = preflight_param("category", category, CATEGORIES, allowed_empty=True) or "insight"
        summary = preflight_param("summary", summary, "anything")
        priority = priority or "medium"
        preflight_param("priority", priority, PRIORITIES)
        area = area or "docs"
        preflight_param("area", area, AREAS)
    except PreflightError as e:
        return None, str(e)
    try:
        lid = _next_seq("LRN", root)
        pk = ("- Pattern-Key: %s\n" % pattern_key) if pattern_key else ""
        body = (
            "## [%s] %s\n\n"
            "**Logged**: %s\n"
            "**Priority**: %s\n"
            "**Status**: pending\n"
            "**Area**: %s\n\n"
            "### Summary\n%s\n\n"
            "### Details\n%s\n\n"
            "### Suggested Action\n（待补）\n\n"
            "### Metadata\n"
            "- Source: %s\n"
            "- Tags: 待补\n"
            "%s"
            "---\n"
        ) % (lid, category, now_iso(), priority, area, summary, details, source, pk)
        path = _append("learning", body, root)
        return lid, path
    except PreflightError as e:
        return None, str(e)


def log_error(summary, error, context="", priority="high", area="docs", root="."):
    try:
        summary = preflight_param("summary", summary, "anything")
        priority = priority or "high"
        preflight_param("priority", priority, PRIORITIES)
        area = area or "docs"
        preflight_param("area", area, AREAS)
    except PreflightError as e:
        return None, str(e)
    try:
        eid = _next_seq("ERR", root)
        body = (
            "## [%s] error\n\n"
            "**Logged**: %s\n"
            "**Priority**: %s\n"
            "**Status**: pending\n"
            "**Area**: %s\n\n"
            "### Summary\n%s\n\n"
            "### Error\n%s\n\n"
            "### Context\n%s\n\n"
            "### Suggested Fix\n（待补）\n\n"
            "### Metadata\n"
            "- Reproducible: unknown\n"
            "---\n"
        ) % (eid, now_iso(), priority, area, summary, error, context or "（未提供）")
        path = _append("error", body, root)
        return eid, path
    except PreflightError as e:
        return None, str(e)


def log_feature(capability, user_context="", complexity="medium", root="."):
    try:
        capability = preflight_param("capability", capability, "anything")
        complexity = complexity or "medium"
        preflight_param("complexity", complexity, COMPLEXITIES)
    except PreflightError as e:
        return None, str(e)
    try:
        fid = _next_seq("FEAT", root)
        body = (
            "## [%s] feature\n\n"
            "**Logged**: %s\n"
            "**Priority**: medium\n"
            "**Status**: pending\n"
            "**Area**: docs\n\n"
            "### Requested Capability\n%s\n\n"
            "### User Context\n%s\n\n"
            "### Complexity Estimate\n%s\n\n"
            "### Suggested Implementation\n（待补）\n\n"
            "### Metadata\n"
            "- Frequency: first_time\n"
            "---\n"
        ) % (fid, now_iso(), capability, user_context or "（未提供）", complexity)
        path = _append("feature", body, root)
        return fid, path
    except PreflightError as e:
        return None, str(e)


def stats(root="."):
    d = ensure_init(root)
    out = {}
    for k, fn in FILES.items():
        p = os.path.join(d, fn)
        out[k] = 0
        if not os.path.exists(p):
            continue
        try:
            with open(p, encoding="utf-8") as f:
                txt = f.read()
            out[k] = len(re.findall(r"\*\*Status\*\*: pending", txt))
        except (PermissionError, OSError, UnicodeDecodeError) as e:
            print("[warn] 读 %s 失败：%s（按 0 计）" % (p, e))
    return out


def recurrence(key, root="."):
    if not key:
        return 0
    d = ensure_init(root)
    p = os.path.join(d, FILES["learning"])
    if not os.path.exists(p):
        return 0
    cnt = 0
    try:
        with open(p, encoding="utf-8") as f:
            for line in f:
                if "Pattern-Key: %s" % key in line:
                    cnt += 1
    except (PermissionError, OSError, UnicodeDecodeError) as e:
        print("[warn] 读 %s 失败：%s" % (p, e))
    return cnt


def promote(entry_id, target_file, rule, root="."):
    """把一条经验升级成短规则追加到 target_file。"""
    if not rule:
        raise PreflightError("【缺参数】--rule 必填，即一句话短规则。")
    if not target_file:
        target_file = "CLAUDE.md"
    if not os.path.isabs(target_file):
        target_file = os.path.join(root, target_file)
    parent = os.path.dirname(target_file)
    if parent and not os.path.isdir(parent):
        try:
            os.makedirs(parent, exist_ok=True)
        except PermissionError as e:
            raise PreflightError("【权限不足】无法建 %s：%s" % (parent, e))
    try:
        with open(target_file, "a", encoding="utf-8") as f:
            f.write("\n" + rule + "\n")
    except PermissionError as e:
        raise PreflightError("【权限不足】写 %s 失败：%s" % (target_file, e))
    except OSError as e:
        raise PreflightError("【IO 错】写 %s 失败：%s" % (target_file, e))
    return target_file


def find(root, keyword, category=None, area=None):
    """跨三个日志文件按关键词检索（高级筛选）。返回匹配条目摘要列表。

    参数：
      keyword  必填，大小写不敏感；在 Summary/Details/Error 里命中即算
      category 可选，限定 LEARNINGS 的分类（correction/insight/...）
      area     可选，限定 Area 标签
    返回：[(文件名, 条目ID, 一行摘要)]
    """
    if not keyword or not keyword.strip():
        raise PreflightError("【还差一个参数】--find 后面要跟关键词，比如 --find 'pnpm'。")
    kw = keyword.strip().lower()
    d = ensure_init(root)
    hits = []
    try:
        for kind, fn in FILES.items():
            p = os.path.join(d, fn)
            if not os.path.exists(p):
                continue
            with open(p, encoding="utf-8") as f:
                lines = f.readlines()
            cur_id = None
            cur_summary = ""
            cur_cat = ""
            cur_area = ""
            for ln in lines:
                s = ln.strip()
                m = re.match(r"## \[([A-Z]{3}-\d{8}-\d{3})\]", s)
                if m:
                    # 收尾上一条
                    if cur_id and _match_filter(cur_cat, cur_area, category, area) \
                            and kw in (cur_summary + cur_cat).lower():
                        hits.append((fn, cur_id, cur_summary.strip()[:60]))
                    cur_id = m.group(1)
                    cur_summary = ""
                    cur_cat = ""
                    cur_area = ""
                    continue
                if s.startswith("**Area**"):
                    cur_area = s.split(":", 1)[-1].strip()
                elif s.startswith("**Category**"):
                    cur_cat = s.split(":", 1)[-1].strip()
                elif s.startswith("### Summary"):
                    cur_summary = ""
                elif cur_summary != "SKIP" and s and not s.startswith("#") \
                        and not s.startswith("**") and not s.startswith("-"):
                    if cur_summary == "":
                        cur_summary = s
            # 最后一条
            if cur_id and _match_filter(cur_cat, cur_area, category, area) \
                    and kw in (cur_summary + cur_cat).lower():
                hits.append((fn, cur_id, cur_summary.strip()[:60]))
    except (PermissionError, OSError, UnicodeDecodeError) as e:
        print("[warn] 读日志失败：%s（忽略）" % e)
    return hits


def _match_filter(cur_cat, cur_area, want_cat, want_area):
    if want_cat and cur_cat and want_cat != cur_cat:
        return False
    if want_area and cur_area and want_area != cur_area:
        return False
    return True


def review(root="."):
    """周报式复盘摘要（创造力与增值亮点）：

    - 三类 pending 计数
    - 出现 ≥3 次的 Pattern-Key（建议升级）
    - 高优先级但未处理的条目
    返回人类可读字符串。
    """
    d = ensure_init(root)
    st = stats(root)
    lines = ["【本周复盘】.learnings/ 当前状态："]
    lines.append("  - 待处理 纠错/洞察 %d · 报错 %d · 需求 %d"
                 % (st.get("learning", 0), st.get("error", 0), st.get("feature", 0)))

    # Pattern-Key 频次
    p = os.path.join(d, FILES["learning"])
    keys = {}
    if os.path.exists(p):
        try:
            for ln in open(p, encoding="utf-8"):
                m = re.search(r"Pattern-Key:\s*(\S+)", ln)
                if m:
                    keys[m.group(1)] = keys.get(m.group(1), 0) + 1
        except (PermissionError, OSError, UnicodeDecodeError):
            pass
    hot = sorted(keys.items(), key=lambda kv: kv[1], reverse=True)
    if hot:
        lines.append("  - 高频模式（≥3 次建议升级）：")
        for k, c in hot:
            flag = " ⬅ 建议升级" if c >= 3 else ""
            lines.append("      · %s 出现 %d 次%s" % (k, c, flag))
    else:
        lines.append("  - 暂无明显高频模式，继续积累。")

    # 高优先级未处理
    high = []
    for fn in FILES.values():
        fp = os.path.join(d, fn)
        if not os.path.exists(fp):
            continue
        try:
            blk = False
            pri = ""
            for ln in open(fp, encoding="utf-8"):
                s = ln.strip()
                if s.startswith("## ["):
                    blk = True
                    pri = ""
                elif s.startswith("**Priority**"):
                    pri = s.split(":", 1)[-1].strip()
                elif s.startswith("**Status**") and "pending" in s and blk \
                        and pri in ("high", "critical"):
                    high.append((fn, pri))
        except (PermissionError, OSError, UnicodeDecodeError):
            pass
    if high:
        lines.append("  - 高优先级待处理 %d 条，优先看：%s"
                     % (len(high), ", ".join(h[0] for h in high[:5])))
    lines.append("提示：用 --find '<关键词>' 翻具体条目；用 --promote 把高频模式升级成永久规则。")
    return "\n".join(lines)


# ===== 自然语言入口 =====

def detect_scene(text):
    """根据 SCENE_HINTS 匹配返回 (scene_name, 子命令, 提示词)。"""
    t = text.lower()
    for scene, hints, cmd, tips in SCENE_HINTS:
        for h in hints:
            if h in t:
                return scene, cmd, tips
    # 默认当 insight 处理（"我学到了"、"get 到"）
    cat = "insight"
    for c, ws in NL_CATEGORY_HINTS.items():
        for w in ws:
            if w in t:
                cat = c
                break
    return "insight", "learning", ["category=%s" % cat, "summary=你的总结", "details=上下文"]


def parse_natural(text, root="."):
    """自然语言 → 自动识别场景 + 记日志 + 提示升级建议。"""
    if not text or not text.strip():
        return 2, "【缺输入】--natural 后面跟一句话，比如 --natural '你刚才应该用 pnpm 不是 npm'。"
    # 太短或没有信号词 → 反问，避免静默误记
    t = text.strip()
    has_signal = any(h in t.lower() for _, hints, _, _ in SCENE_HINTS for h in hints)
    has_nl = any(w in t for ws in NL_CATEGORY_HINTS.values() for w in ws)
    if len(t) < 4 or (not has_signal and not has_nl):
        print("【没太看懂】你这句话有点短，没分清是纠错、报错还是想要新功能。可以这样说：")
        print("  纠错：--natural '记一笔，你刚才把命令拼错了，应该用 pnpm'")
        print("  报错：--natural '记一笔，刚才 git push 鉴权失败了'")
        print("  新功能：--natural '记一笔，希望 AI 能直接导出 Excel'")
        return 1, "需要更明确的描述"
    scene, cmd, tips = detect_scene(text)
    marker = "## [%s] %s" % ("已识别场景", scene)
    print(marker)
    print("  建议子命令:", cmd)
    print("  必要参数:", ", ".join(tips))
    if cmd == "error":
        # 自动取首句当 summary，剩余当 error-msg
        parts = text.strip().split("。", 1)
        summ = parts[0]
        msg = parts[1] if len(parts) > 1 else text
        lid, out = log_error(summ, msg, root=root)
        if out and not lid:
            print("ERR:", out)
            return 1, "记失败"
        print("已记:", lid)
    elif cmd == "learning":
        cat = scene if scene in CATEGORIES else "insight"
        # 取首句当 summary，剩余当 details
        parts = text.strip().split("。", 1)
        lid, out = log_learning(cat, parts[0], parts[1] if len(parts) > 1 else "（无）",
                                 pattern_key=_extract_pattern_key(text), root=root)
        if out and not lid:
            print("ERR:", out)
            return 1, "记失败"
        print("已记:", lid)
        # 自动查 recurrence ≥3 时建议升级
        if lid:
            key = _extract_pattern_key(text)
            if key:
                cnt = recurrence(key, root=root)
                if cnt >= 3:
                    print("[建议] %s 已出现 %d 次，建议升级到 CLAUDE.md："
                          "--promote --id %s --rule '<短规则>'" % (key, cnt, lid))
    elif cmd == "recurrence":
        key = _extract_pattern_key(text)
        cnt = recurrence(key, root=root)
        print("[recurrence]", key, "出现", cnt, "次")
    elif cmd == "promote":
        print("[提示] 自动 promote 需要 --id，"
              "请用 --promote --id <LRN-..> --rule '<短规则>'")
    return 0, "ok"


def _extract_pattern_key(text):
    """从自然语言里粗抽 pattern key（取最长的名词短语，限定 ASCII/数字/.-_）。"""
    m = re.search(r"[A-Za-z][\w\.\-]{4,}", text or "")
    return m.group(0) if m else ""


# ===== 文档：能力边界 / 用法 =====

CAN_DO_TEXT = """\
我能做什么（can_do）：
  - 记三类日志：LEARNING（纠正/洞察/知识缺口/最佳实践）/ ERROR（命令失败）/ FEATURE_REQUEST（用户需求）
  - 自动抽 Pattern-Key 查重复次数（>=3 次建议升级到 CLAUDE.md/AGENTS.md）
  - 把稳定经验升级到 CLAUDE.md / AGENTS.md / SOUL.md / .github/copilot-instructions.md
  - 自然语言识别："我又犯错了" → error、"我教过你用 pnpm" → correction
  - 检索：--find "<关键词>" 跨三个日志翻具体条目（可按分类/区域筛选）
  - 周报：--review 一键看 pending 数 + 高频模式 + 高优先级待处理
  - 用 notify.py 把当日报错摘要推到飞书/钉钉/企业微信（需配 webhook）
  - 用 extract_skill.py 把稳定经验抽成新技能（联动毕昇 forge_skill.py）

我不能做（cannot_do）：
  - 不替你做编码决策——我帮你**记忆**你的决策
  - 默认不联网——核心功能 100% 本地跑；只有你主动配了 webhook，notify.py 才发群消息
  - 不删已记的条目（你或代理改 .learnings/*.md 自己删/改）
  - 不内置大模型/embedding——纯 markdown，不依赖向量库
  - 不会主动审你整个项目代码——只在被叫时工作，且只读要记的那一句
  - 升级到 CLAUDE.md/AGENTS.md 前会先确认该文件存在/可写，且只**追加**短规则，不覆盖你写的内容

预期输出（expected）：
  - --init：建 .learnings/ + 3 个 .md 文件（或确认已存在）
  - --learning：返回 LRN-yyyymmdd-xxx 这条 ID
  - --stats：返回 {"learning": n, "error": n, "feature": n} 三类 pending 计数
  - --recurrence --pattern-key X：返回 X 出现次数
  - --find "pnpm"：返回所有含 pnpm 的条目（ID + 摘要），找不到给友好提示
  - --review：返回周报式复盘（pending 数 + 高频模式 + 高优先级提醒）
  - --natural "..."：识别场景 + 自动记 + 给参数建议；说不清时反问引导，不乱记

边界场景：
  - 磁盘满 → 报错"【IO 错】写 ... 失败：... 请检查磁盘空间"
  - 权限不足 → 报错"【权限不足】..."
  - 文件被其他程序占用 → 同上 IO 错
  - 参数缺失 → "【缺参数】--summary 必填。比如：--summary '...' "
  - 参数非法 → "【参数非法】--category 'foo' 不在白名单 [...] 内"
"""


USE_TEXT = """\
用法（自报家门）：用法是 --init、--learning、--error、--feature、--promote、--stats、--recurrence、--natural、--can-do、--use 这十种。

典型示例：
  1. 首次使用：python self_improve.py --init
  2. 你纠正 AI："你应该用 pnpm 不是 npm"
     → python self_improve.py --natural "你应该用 pnpm 不是 npm"
  3. 报错自动记：
     → python self_improve.py --error --summary "git push 鉴权失败" \\
          --error-msg "remote: Invalid username"
  4. 你想要的功能 AI 不支持：
     → python self_improve.py --feature --capability "导出 Excel" --context "周报场景"
  5. 看现在 pending 数：python self_improve.py --stats
  6. 查"pnpm"出现几次：python self_improve.py --recurrence --pattern-key pnpm
  7. 翻具体条目：python self_improve.py --find "pnpm"
  8. 周报复盘：python self_improve.py --review
  9. 升级一条经验到 CLAUDE.md：
     → python self_improve.py --promote --id LRN-20260830-001 \\
          --rule "本项目使用 pnpm 不是 npm" --target CLAUDE.md
  10. 看能力边界：python self_improve.py --can-do
"""


# ===== 主流程 =====

def _parse_argv(argv):
    """手动解析参数，避开 argparse 在 choices/required 带来的退出码冲突。

    支持两种风格：
      新：self_improve.py learning --summary "..." [--category correction] ...
      旧：self_improve.py --learning --summary "..." [--category correction] ...
    """
    # 旧风格 → 新风格
    legacy = {
        "--init": "init", "--stats": "stats", "--can-do": "can-do", "--use": "use",
        "--learning": "learning", "--error": "error", "--feature": "feature",
        "--promote": "promote", "--recurrence": "recurrence", "--natural": "natural",
        "--find": "find", "--review": "review",
    }
    if argv and argv[0] in legacy:
        argv = [legacy[argv[0]]] + argv[1:]
    cmd = argv[0] if argv else ""
    rest = argv[1:]

    out = {"cmd": cmd}

    def take(*names):
        for n in names:
            if n in rest:
                i = rest.index(n)
                j = i + 1
                buf = []
                while j < len(rest) and not rest[j].startswith("--"):
                    buf.append(rest[j])
                    j += 1
                if not buf:
                    out["__missing__"] = n
                    return ""
                # 剥掉外层成对引号（'/'/"），并 strip——
                # 避免 " " 或 "" 这种"传了但没值"被当成真值保存
                v = " ".join(buf)
                if len(v) >= 2 and v[0] == v[-1] and v[0] in {'"', "'"}:
                    v = v[1:-1]
                return v
        return ""

    out["category"] = take("--category")
    out["summary"] = take("--summary")
    out["details"] = take("--details")
    out["priority"] = take("--priority")
    out["area"] = take("--area")
    out["pattern_key"] = take("--pattern-key")
    out["source"] = take("--source") or "conversation"
    out["error_msg"] = take("--error-msg")
    out["context"] = take("--context")
    out["capability"] = take("--capability")
    out["complexity"] = take("--complexity")
    out["id"] = take("--id")
    out["rule"] = take("--rule")
    out["target"] = take("--target") or "CLAUDE.md"
    out["natural_rest"] = rest  # 给 --natural 子命令用全部剩余
    return out


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if not argv or argv[0] in {"-h", "--help"}:
        print(USE_TEXT)
        return EXIT_OK
    p = _parse_argv(argv)
    cmd = p["cmd"]
    if cmd == "init":
        try:
            d = ensure_init(".")
            print("已初始化:", d); return EXIT_OK
        except PreflightError as e:
            print("ERR:", e); return EXIT_RUNTIME
    if cmd == "stats":
        print(json.dumps(stats("."), ensure_ascii=False)); return EXIT_OK
    if cmd == "can-do":
        print(CAN_DO_TEXT); return EXIT_OK
    if cmd == "use":
        print(USE_TEXT); return EXIT_OK
    if cmd == "learning":
        lid, out = log_learning(p["category"] or "insight", p["summary"], p["details"] or "（无）",
                                priority=p["priority"] or "medium",
                                area=p["area"] or "docs",
                                pattern_key=p["pattern_key"],
                                source=p["source"])
        if lid:
            print("已记:", lid); return EXIT_OK
        print("ERR:", out)
        return EXIT_ARG if ("缺参数" in out or "非法" in out) else EXIT_RUNTIME
    if cmd == "error":
        eid, out = log_error(p["summary"], p["error_msg"] or "（无）",
                             context=p["context"],
                             priority=p["priority"] or "high",
                             area=p["area"] or "docs")
        if eid:
            print("已记:", eid); return EXIT_OK
        print("ERR:", out)
        return EXIT_ARG if ("缺参数" in out or "非法" in out) else EXIT_RUNTIME
    if cmd == "feature":
        fid, out = log_feature(p["capability"], user_context=p["context"],
                               complexity=p["complexity"] or "medium")
        if fid:
            print("已记:", fid); return EXIT_OK
        print("ERR:", out)
        return EXIT_ARG if ("缺参数" in out or "非法" in out) else EXIT_RUNTIME
    if cmd == "promote":
        try:
            target = promote(p["id"], p["target"], p["rule"])
            print("已升级到:", target); return EXIT_OK
        except PreflightError as e:
            print("ERR:", e)
            return EXIT_ARG if "缺参数" in str(e) else EXIT_RUNTIME
    if cmd == "recurrence":
        key = p["pattern_key"]
        if not key:
            print("ERR: --pattern-key 必填")
            return EXIT_ARG
        print(key, "出现", recurrence(key), "次"); return EXIT_OK
    if cmd == "find":
        kw = " ".join(p["natural_rest"]).strip()
        try:
            hits = find(".", kw, category=p["category"] or None, area=p["area"] or None)
        except PreflightError as e:
            print("ERR:", e); return EXIT_ARG
        if not hits:
            print("没找到含 '%s' 的条目。换个关键词，或用 --find 'pnpm' 试试？" % kw)
            return EXIT_OK
        print("找到 %d 条含 '%s'：" % (len(hits), kw))
        for fn, eid, summ in hits:
            print("  [%s] %s — %s" % (fn, eid, summ))
        return EXIT_OK
    if cmd == "review":
        print(review(".")); return EXIT_OK
    if cmd == "natural":
        text = " ".join(p["natural_rest"]).strip()
        code, _msg = parse_natural(text)
        return code
    print("未知命令:", cmd, "。用法见 --use / --can-do")
    return EXIT_UNKNOWN_CMD


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
