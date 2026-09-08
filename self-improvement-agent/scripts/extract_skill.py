#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_skill.py — 把稳定经验抽成新技能（联动毕昇 skill-forge）

不重造轮子：若环境已装 skill-forge，直接调它的 forge_skill.py 一键脚手架；
没装则产出 SKILL.md 骨架（含占位说明，用户后续填真实内容）。

用法：
  python extract_skill.py --dry-run <skill-name>    预览
  python extract_skill.py <skill-name>              生成（默认 ./<skill-name>/）
  --persona "墨子" --title "工程指挥官" --scenes "红线/审查/重构"

退出码：0 成功，1 参数/路径错，2 外部进程错。

设计：
  - argv 越界被 catch，不会 IndexError 崩
  - subprocess.run 加 30s 超时，防外部 forge 卡死
  - 找不到 forge 时不报错，回退到基础骨架（且骨架 description 写明"待补"避免空文档）
"""
import os
import shutil
import subprocess
import sys

EXIT_OK = 0
EXIT_ARG = 1
EXIT_PROC = 2

# 占位骨架：description 内明确写"提炼自 LRN-..."，避免审核判空。
SKILL_TEMPLATE = """---
name: {name}
version: 1.0.0
description: {name} v1.0.0（自动抽取骨架，待人工补完）。提炼自 self-improvement-agent 的经验沉淀。覆盖：（待补——什么场景触发、要解决什么、可执行步骤）。触发词：技术「{name}」；口语「待补」；英文「{name}」；人名「待补」。同宇宙推荐：self-improvement-agent（AI 自我改进·记录来源）。
---

# {name}

## 它解决什么
（由原始 LEARNING 中 Details 段提炼——把"AI 学到了什么"提炼成一句话痛点）

## 何时用
（触发场景：什么场景/什么输入下 AI 应启用本技能）

## 怎么用
（可执行步骤 / 脚本 / 红线——直接照做能跑的部分）

## 红线
（绝不碰的——避免重蹈原始错误）

## 可挂的钩子
- notify.py: 出现 LRN 升 PRR 时 --feature 召唤通知
- self_improve.py: 用 --recurrence --pattern-key <本技能特征词> 持续看复发

## 来源
提炼自 LRN-YYYYMMDD-XXX（已脱敏）——self-improvement-agent

## 待补字段（上传前必须填）
- [ ] description 触发词海（技术 / 口语 / 英文 / 人名 四路）
- [ ] scripts/ 实际脚本（if 需要）
- [ ] FAQ.md 反模式 Q&A
- [ ] version 字段确认
"""


def find_forge():
    """找毕昇 forge_skill.py：常见位置或环境变量。"""
    cand = [
        os.environ.get("FORGE_SKILL_PATH", ""),
        os.path.join("..", "skill-forge", "scripts", "forge_skill.py"),
        os.path.join(os.path.expanduser("~"), "Skills", "skill-forge", "scripts", "forge_skill.py"),
    ]
    for c in cand:
        if c and os.path.exists(c):
            return c
    return None


def dry_run(name):
    if not name:
        print("ERR: --dry-run 后要跟 skill-name")
        return EXIT_ARG
    print("[dry-run] 将生成技能:", name)
    forge = find_forge()
    if forge:
        print("[dry-run] 检测到毕昇:", forge)
        print("[dry-run] 将调用:", sys.executable, forge,
              "--slug", name, "--persona ... --title ... --scenes ...")
    else:
        print("[dry-run] 未检测到毕昇（FORGE_SKILL_PATH 或 ../skill-forge）")
        print("[dry-run] 回退方案：产出 SKILL.md 骨架到 ./" + name + "/")
    return EXIT_OK


def generate(name, persona="", title="", scenes=""):
    if not name:
        print("ERR: skill-name 必填")
        return EXIT_ARG
    out_dir = os.path.join(".", name)
    forge = find_forge()
    if forge:
        cmd = [sys.executable, forge, "--slug", name]
        if persona: cmd += ["--persona", persona]
        if title: cmd += ["--title", title]
        if scenes: cmd += ["--scenes", scenes]
        print("[extract] 调用毕昇:", " ".join(cmd))
        try:
            subprocess.run(cmd, check=True, timeout=30)
            print("[extract] 已用毕昇脚手架生成:", name)
            return EXIT_OK
        except subprocess.TimeoutExpired:
            print("[extract] 毕昇调用超时（>30s），回退骨架")
        except subprocess.CalledProcessError as e:
            print("[extract] 毕昇返回非 0（rc=%d），回退骨架" % e.returncode)
        except (FileNotFoundError, OSError) as e:
            print("[extract] 毕昇无法启动（%s），回退骨架" % e)
    # 回退：只产 SKILL.md 骨架
    try:
        os.makedirs(out_dir, exist_ok=True)
    except (PermissionError, OSError) as e:
        print("[extract] 【IO错】无法建 %s：%s" % (out_dir, e))
        return EXIT_PROC
    target = os.path.join(out_dir, "SKILL.md")
    try:
        with open(target, "w", encoding="utf-8") as f:
            f.write(SKILL_TEMPLATE.format(name=name))
    except (PermissionError, OSError) as e:
        print("[extract] 【IO错】无法写 %s：%s" % (target, e))
        return EXIT_PROC
    print("[extract] 已产 SKILL.md 骨架到:", out_dir)
    print("[extract] ⚠  骨架里有占位字段，上传 SkillHub 前请补完，否则可能审核不通过")
    return EXIT_OK


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        return EXIT_OK
    if not argv:
        print(__doc__)
        return EXIT_ARG
    dry = False
    if "--dry-run" in argv:
        dry = True
        argv.remove("--dry-run")
    if not argv:
        print("ERR: --dry-run 后要跟 skill-name")
        return EXIT_ARG
    name = argv[0]
    persona = ""
    title = ""
    scenes = ""
    # 防止 --xxx 后跟 --yyy 这种吃错位的边界情况
    def take(flag):
        if flag in argv:
            i = argv.index(flag)
            if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
                raise ValueError("%s 后必须跟一个值" % flag)
            return argv[i + 1]
        return ""
    try:
        persona = take("--persona")
        title = take("--title")
        scenes = take("--scenes")
    except ValueError as e:
        print("ERR:", e)
        return EXIT_ARG

    if dry:
        return dry_run(name)
    return generate(name, persona, title, scenes)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
