# AI 自我改进 · 快速上手

> 让 AI 越用越懂你。每次纠正、报错、想要的功能，自动记成永久记忆。

## 1. 装上就会用

本技能是"元工具"：你不用手动调它。在对话里正常用 AI，当出现下面三种情况，AI 会**主动**记一笔：

- AI 报错了 / 命令失败了
- 你纠正了 AI（"不对，应该用 pnpm 不是 npm"）
- 你要个 AI 没有的功能（"怎么不能导出 Excel？"）

AI 会说"我记一笔"，然后把教训写进你项目根的 `.learnings/`。

## 2. 手动初始化（可选）

```bash
# 在你的项目根执行，AI 通常会自己干这件事
mkdir -p .learnings
```

首次会自动生成三个文件：`LEARNINGS.md` / `ERRORS.md` / `FEATURE_REQUESTS.md`。**已有文件不会被覆盖**。

## 3. 看看记了什么

```bash
cat .learnings/LEARNINGS.md
cat .learnings/ERRORS.md
```

想看还有多少待处理：

```bash
grep -c "Status\*\*: pending" .learnings/*.md
```

## 4. 升级成永久记忆

一条经验重复出现 3 次以上，AI 会把它提炼成一条短规则，写进：

- `CLAUDE.md` — 项目事实/约定
- `AGENTS.md` — 工作流/自动化
- `SOUL.md` — 行为规范
- `.github/copilot-instructions.md` — Copilot 上下文

下次任何 AI 打开这个项目，都自动遵守。

## 5. 中文专属：推送到群

配置了飞书/钉钉/企业微信机器人后，错误日报会自动推到群里。见 `references/chinese-dev-context.md`。

## 6. 抽成新技能

一条经验足够通用，AI 会调用 `scripts/extract_skill.py`，联动毕昇 `forge_skill.py` 直接生成新技能骨架——经验反哺社区。

## 目录结构

```
self-improvement-agent/
├── SKILL.md
├── README.md
├── FAQ.md
├── LEARNINGS-TEMPLATE.md
├── ERRORS-TEMPLATE.md
├── FEATURE_REQUESTS-TEMPLATE.md
├── SKILL-EXTRACT-TEMPLATE.md
├── references/
│   ├── examples.md
│   ├── chinese-dev-context.md
│   ├── hooks-setup.md
│   ├── upgrade-rules.md
│   └── cross-universe.md
├── scripts/
│   ├── self_improve.py
│   ├── extract_skill.py
│   └── notify.py
└── resources/
    └── self_improve.json
```

## 文件导航（想看什么，直接开哪个）

| 我想了解 / 想做 | 打开 / 跑 |
|---|---|
| 这技能是干嘛的、核心机制 | `SKILL.md` |
| 30 秒上手流程 | `README.md`（本文） |
| 隐私 / 和 Cursor 冲突 / 误记怎么删 | `FAQ.md` |
| "遇到 X 情况我该说什么"话术表 | `references/examples.md` 第一节 |
| 抄一条完整日志长什么样 | `references/examples.md` 第二节 |
| 中文路径 / pnpm / 飞书钉钉企微推送 | `references/chinese-dev-context.md` |
| 想装自动提醒 hook（可选） | `references/hooks-setup.md` |
| 什么经验该升级、怎么升级 | `references/upgrade-rules.md` |
| 和孔明/子房/鲁班/墨子怎么联动 | `references/cross-universe.md` |
| 把一条经验抽成新技能 | `SKILL-EXTRACT-TEMPLATE.md` + `scripts/extract_skill.py` |
| 自己动手记 / 查 / 周报 | `scripts/self_improve.py`（--use 看全部命令） |

## 版本

v1.0.0 — 中文开发者版，原创差异化：中文语境 + 毕昇联动抽技能 + context-bridge 跨会话 + 飞书/钉钉/企微推送。
