#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""self-teach-agent 间隔复现引擎：SM-2 调度 + 遗忘曲线读数。

把"学了别忘"变成可计算的数字：
- SM-2（SuperMemo 1987）根据每次回忆评分(0-5)更新易度因子与间隔，
  算出"下次复习日"。
- 遗忘曲线 R = e^(-t/S)（Ebbinghaus）：S 由当前间隔反推，给出"现在还记得多少"。

可计算硬核 2：和 curriculum 一起，把 self-teach 的两个独立子机制都变成
数字证据，而不是空谈"要复习"。
"""
import argparse
import json
import math
import sys
from datetime import date, timedelta

# SM-2 默认参数（可被 retention_schedule.json 覆盖）
DEFAULT_EASE = 2.5
MIN_EASE = 1.3


class RetentionError(Exception):
    pass


def _stability(interval_days):
    """由当前间隔反推记忆稳定性 S（经验近似：S≈interval/ln(2)）。"""
    if interval_days <= 0:
        return 1.0
    return interval_days / math.log(2)


def forgetting_curve(interval_days, elapsed_days):
    """返回经过 elapsed 天后，相对于"刚复习完"的保留率(0-1)。"""
    S = _stability(interval_days)
    if S <= 0:
        return 0.0
    return math.exp(-elapsed_days / S)


def sm2(ease, interval, reps, grade):
    """更新一个单元的 SM-2 状态。grade 0-5。返回 (ease, interval, reps)。"""
    if grade < 3:
        # 回忆失败：重置，明天重来
        return DEFAULT_EASE, 1, 0
    if reps == 0:
        interval = 1
    elif reps == 1:
        interval = 6
    else:
        interval = round(interval * ease)
    new_ease = ease + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02))
    new_ease = max(MIN_EASE, new_ease)
    return new_ease, interval, reps + 1


def cmd_demo(args):
    print("===== 间隔复现演示（SM-2） =====")
    ease, interval, reps = DEFAULT_EASE, 0, 0
    print("初始：ease=%.2f, reps=%d" % (ease, reps))
    for g in [5, 5, 4, 5, 3]:
        ease, interval, reps = sm2(ease, interval, reps, g)
        print("  评分 %d → 下次间隔 %d 天, ease=%.2f, reps=%d"
              % (g, interval, ease, reps))
    print("\n===== 遗忘曲线读数（假设刚复习完间隔=16天） =====")
    for d in [0, 1, 3, 7, 16, 30]:
        r = forgetting_curve(16, d)
        print("  经过 %2d 天：保留率 %.0f%%" % (d, r * 100))


def cmd_schedule(args):
    state = {"ease": DEFAULT_EASE, "interval": 0, "reps": 0}
    if args.state:
        state = json.load(open(args.state, encoding="utf-8"))
    ease, interval, reps = sm2(
        state["ease"], state["interval"], state["reps"], args.grade)
    due = date.today() + timedelta(days=interval)
    print("评分 %d：下次复习日 = %s（间隔 %d 天）" % (args.grade, due, interval))
    print("更新后 ease=%.2f, reps=%d" % (ease, reps))
    if args.out:
        json.dump({"ease": ease, "interval": interval, "reps": reps},
                  open(args.out, "w", encoding="utf-8"), ensure_ascii=False)
        print("状态已写入 %s" % args.out)


def cmd_retention(args):
    if args.interval <= 0:
        raise RetentionError("--interval 必须为正。")
    r = forgetting_curve(args.interval, args.elapsed)
    print("间隔=%d 天，已过 %d 天 → 保留率 %.0f%%"
          % (args.interval, args.elapsed, r * 100))
    if r < 0.6:
        print("⚠ 保留率低于 60%，该安排一次复习召回了。")


def build_parser():
    p = argparse.ArgumentParser(description="self-teach 间隔复现引擎")
    p.add_argument("--demo", action="store_true", help="演示 SM-2 与遗忘曲线")
    p.add_argument("--schedule", action="store_true", help="按评分算下次复习日")
    p.add_argument("--grade", type=int, choices=range(0, 6), help="回忆评分 0-5")
    p.add_argument("--state", help="单元状态 json（ease/interval/reps）")
    p.add_argument("--out", help="把更新后的状态写回文件")
    p.add_argument("--retention", action="store_true", help="算遗忘曲线保留率")
    p.add_argument("--interval", type=int, default=16, help="当前复习间隔(天)")
    p.add_argument("--elapsed", type=int, default=0, help="已过去天数")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.demo:
            cmd_demo(args)
            return 0
        if args.schedule:
            if args.grade is None:
                raise RetentionError("--schedule 需要 --grade。")
            cmd_schedule(args)
            return 0
        if args.retention:
            cmd_retention(args)
            return 0
        parser.print_help()
        return 0
    except RetentionError as e:
        print("间隔复现错误：%s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
