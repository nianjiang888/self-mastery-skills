# 升级判定规则（Promotion Rules）

当一条经验足够通用，从"某次日志"升为"永久项目记忆"。

## 升级触发（全部满足才升）

| 条件 | 阈值 |
|---|---|
| 重复出现次数 | `Recurrence-Count >= 3` |
| 跨独立任务数 | >= 2 个不同任务 |
| 时间窗口 | 30 天内 |

或任一**快速通道**：
- `Priority = critical`（阻断核心功能 / 数据丢失 / 安全风险）→ 直接升
- 用户明确说"记进 CLAUDE.md" → 直接升

## 升级目标映射

| 经验类型 | 升到哪里 | 写什么 |
|---|---|---|
| 项目事实 / 约定 / 坑 | `CLAUDE.md` | 短事实（"包管理=pnpm"） |
| 工作流 / 自动化步骤 | `AGENTS.md` | 可执行步骤（改 API→regen→tsc） |
| 行为规范 / 沟通风格 | `SOUL.md` | 原则（"简洁、不加免责声明"） |
| GitHub Copilot 上下文 | `.github/copilot-instructions.md` | 项目约定 |

## 升级写法（短预防规则，不是事故报告）

❌ 不要升这种：
```
## [LRN-20260830-001] correction
（贴 200 字事故经过……）
```

✅ 要升这种：
```
## 依赖
- 包管理器：pnpm（不是 npm）→ 用 `pnpm install`
```

## 升级后回写

原条目：
- `Status`: pending → `promoted`
- 加 `Promoted: CLAUDE.md`（或对应文件）

## 周期复盘

在natural断点检查 `.learnings/`：

- 新任务开始前
- 功能完成后
- 该区域曾有 learnings 时
- 活跃开发期每周

动作：resolve 已修的、promote 适用的、link 相关的、escalate 反复的。

## 递归模式检测

记到类似已有条目时：
1. `grep "Pattern-Key: <key>" .learnings/LEARNINGS.md`
2. 找到 → `Recurrence-Count +1`、`Last-Seen` 更新、加 `See Also`
3. 没找到 → 新建，`Source: simplify-and-harden`，`Pattern-Key` 设去重键

## 优先级速查

| 优先级 | 用何时 |
|---|---|
| critical | 阻断核心 / 数据丢失 / 安全 |
| high | 影响常见流程 / 反复出现 |
| medium | 有影响但有 workaround |
| low | 边缘 / 偶发 / 锦上添花 |
