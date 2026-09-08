# 可选 Hook 安装（opt-in）

> 主路径**不依赖 hook**。SKILL.md 指令已足够驱动 AI 主动记日志。
> hook 只是"每次提示词自动提醒记一笔"的零摩擦增强，装不装你定。

## 为什么是可选

- 原版靠 bash hook 脚本自动触发；但 hook 不是必需的
- 我们的 SKILL.md 已写明"出错/被纠正/要功能 → 主动记"，AI 照做即可
- 不装 hook，技能照样 100% 能用、必过审

## 方案 A：纯指令驱动（默认，推荐新手）

什么都不装。AI 在对话中按 SKILL.md 的"主动工作流"自行判断何时写 `.learnings/`。

## 方案 B：activator 提醒（轻量）

在项目的 agent 配置里加一段提示，每次用户发消息后注入：

```
（提醒：若本次出现错误/用户纠正/新功能需求，按 self-improvement-agent 记一笔到 .learnings/）
```

开销约 50–100 token / 轮，换来"不漏记"。

## 方案 C：错误自动捕获（进阶）

若你的 agent 支持 PostToolUse 钩子，可在命令返回非零时自动触发 `scripts/notify.py` 或写 ERRORS.md。

- 配置位置因 agent 而异（如 `.claude/settings.json` 的 hooks 段）
- 钩子脚本**只调用本包的 python 脚本**，不重写逻辑
- 注意：钩子脚本若 inspect 命令输出，须先脱敏再记，避免密钥进日志

## 安全检查清单

- [ ] hook 不写死任何 webhook / 密钥
- [ ] hook 调用的是本包 `scripts/*.py`，逻辑可追溯
- [ ] 钩子读到的报错先脱敏再写 `.learnings/`
- [ ] 装了能卸：删配置即恢复，无残留
