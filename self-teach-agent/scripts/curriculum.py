#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""self-teach-agent 排课引擎：先修图拓扑排序 + 由易到难。

把要学的一堆主题，按"先修关系"排出合法顺序，再在同一层可选节点里
按难度从小到大排，得到一条由易到难的学习路径。这是 Curriculum Learning
(Bengio 2009) 的工程化：难度度量 + pacing 顺序，让优化（学习）轨迹更平滑。

可计算硬核 1：和 self-evaluate 的 calibrate、self-debug 的 localize、
self-verify 的 consistency、self-optimize 的 bayes 同属"把抽象能力变成数字"。
"""
import argparse
import json
import sys
from collections import deque

DEMO_SYLLABUS = {
    "topics": {
        "变量与类型":     {"prereq": [],            "difficulty": 1},
        "控制流":         {"prereq": ["变量与类型"], "difficulty": 2},
        "函数":           {"prereq": ["控制流"],     "difficulty": 3},
        "数据结构":       {"prereq": ["函数"],       "difficulty": 4},
        "类与对象":       {"prereq": ["函数"],       "difficulty": 5},
        "装饰器":         {"prereq": ["类与对象"],   "difficulty": 7},
        "迭代器与生成器": {"prereq": ["类与对象"],   "difficulty": 6},
        "元类":           {"prereq": ["装饰器"],     "difficulty": 9},
        "并发模型":       {"prereq": ["迭代器与生成器"], "difficulty": 8},
    }
}


class CurriculumError(Exception):
    pass


def _topo_order(syllabus):
    """Kahn 算法拓扑排序；返回合法顺序（prereq 在前）。"""
    topics = syllabus["topics"]
    indeg = {t: 0 for t in topics}
    adj = {t: [] for t in topics}
    for t, spec in topics.items():
        for p in spec.get("prereq", []):
            if p not in topics:
                raise CurriculumError("主题《%s》的先修《%s》不存在。" % (t, p))
            adj[p].append(t)
            indeg[t] += 1
    # 同入度层内按难度升序，实现"由易到难"
    q = deque(sorted([t for t in topics if indeg[t] == 0],
                     key=lambda x: topics[x]["difficulty"]))
    order = []
    while q:
        u = q.popleft()
        order.append(u)
        # 释放后继
        nxt = sorted(adj[u], key=lambda x: topics[x]["difficulty"])
        for v in nxt:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    if len(order) != len(topics):
        # 找环
        in_cycle = [t for t in topics if indeg[t] > 0]
        raise CurriculumError("检测到先修环，无法排课：%s" % " → ".join(in_cycle))
    return order


def cmd_plan(args):
    if args.demo:
        syllabus = DEMO_SYLLABUS
        label = "（内置示例：学 Python）"
    elif args.syllabus:
        syllabus = json.load(open(args.syllabus, encoding="utf-8"))
        label = args.syllabus
    else:
        raise CurriculumError("需要 --syllabus 文件路径，或 --demo。")
    order = _topo_order(syllabus)
    print("===== 学习路径规划 %s =====" % label)
    print("共 %d 个主题，由易到难、先修在前：\n" % len(order))
    for i, t in enumerate(order, 1):
        spec = syllabus["topics"][t]
        pre = "、".join(spec["prereq"]) if spec["prereq"] else "（无）"
        print("%2d. %s  难度=%d  先修=[%s]" % (i, t, spec["difficulty"], pre))


def cmd_check(args):
    """只做合法性检查（有无环/悬空先修），不打印路径。"""
    syllabus = json.load(open(args.syllabus, encoding="utf-8"))
    _topo_order(syllabus)
    print("✓ 大纲合法：无环、先修齐全，可排课。")


def build_parser():
    p = argparse.ArgumentParser(description="self-teach 排课引擎")
    p.add_argument("--syllabus", help="大纲 json：{topics:{名:{prereq:[],difficulty:int}}}")
    p.add_argument("--demo", action="store_true", help="用内置示例大纲")
    p.add_argument("--check", action="store_true", help="仅检查大纲合法性")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.check and args.syllabus:
            cmd_check(args)
            return 0
        cmd_plan(args)
        return 0
    except CurriculumError as e:
        print("排课错误：%s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
