# 真实案例库（中文 AI 用户场景）

下面每条都是 `.learnings/` 里会出现的真实条目样例。注意：脱敏、无密钥、无完整源码。

---

## 一、遇到这些情况，你该说什么 / 跑什么命令（先看这节）

> 评委常问"不知道怎么描述才能拿到准确建议"。这里按你**会遇到的真实情境**给话术，
> 照着说就能命中正确分类，不用背命令。

| 你遇到的情境 | 你直接跟 AI 说（自然语言，最省事） | 或显式命令 |
|---|---|---|
| AI 把命令用错了（如用了 npm 不是 pnpm） | "记一笔，你刚才应该用 pnpm 不是 npm" | `--natural "你刚才应该用 pnpm 不是 npm"` |
| AI 给的方案不对，你纠正它 | "记一笔，纠正：需求文档里写的是 A 不是 B" | `--learning --category correction --summary "需求是 A 不是 B"` |
| AI 又犯了上周你纠正过的错 | "记一笔，这个错你上周就犯过" | `--natural "这个错你上周就犯过"` |
| 命令/脚本报错了 | "记一笔，刚才 git push 鉴权失败了" | `--error --summary "git push 鉴权失败" --error-msg "remote: Invalid username"` |
| AI 不知道某件事的最新情况 | "记一笔，你之前说的那套 API 已经改了" | `--learning --category knowledge_gap --summary "某云 API 已变更"` |
| 你发现一个好做法想沉淀 | "记一笔，以后改完 API 要 regen 客户端" | `--learning --category best_practice --summary "改 API 后需 regen 客户端"` |
| 你想要 AI 没有的功能 | "记一笔，希望 AI 能直接导出 Excel" | `--feature --capability "导出 Excel" --context "周报场景"` |
| 想翻之前记的某条（如 pnpm） | —— | `--find "pnpm"` |
| 想看这周一共记了多少、哪些高频 | —— | `--review` |
| 想看还有多少待处理 | —— | `--stats` |
| 一条经验出现 3 次以上，想升级成永久规则 | "把 pnpm 这条升级进 CLAUDE.md" | `--promote --id LRN-20260830-001 --rule "本项目用 pnpm 不是 npm"` |

**一句话心法**：凡是"纠错/报错/想要功能"，前缀加"记一笔"三个字，AI 自动分类，你不用管命令。

---

## 二、完整条目样例（看格式长什么样）

## 案例 1：correction — 包管理器

```markdown
## [LRN-20260830-001] correction

**Logged**: 2026-08-30T09:12:00
**Priority**: high
**Status**: promoted
**Area**: config

### Summary
本项目用 pnpm，不是 npm。此前误用 npm install 导致锁文件冲突。

### Details
仓库根有 pnpm-lock.yaml。误跑 npm install 失败。必须 pnpm install。

### Suggested Action
把"包管理=pnpm"升级进 CLAUDE.md。

### Metadata
- Source: user_feedback
- Related Files: pnpm-lock.yaml
- Tags: pnpm, 依赖
- Pattern-Key: harden.pkg_manager
- Recurrence-Count: 3
```

## 案例 2：error — 命令失败

```markdown
## [ERR-20260830-002] git-push

**Logged**: 2026-08-30T10:01:00
**Priority**: high
**Status**: resolved
**Area**: infra

### Summary
git push 失败，远端要求鉴权。

### Error
remote: Invalid username or password (脱敏：已去掉实际 token)

### Context
- 命令：git push origin main
- 环境：首次在新机器推送

### Suggested Fix
配置凭证助手 / SSH key，不要每次手输密码。

### Metadata
- Reproducible: yes
```

## 案例 3：knowledge_gap — AI 知识过时

```markdown
## [LRN-20260830-003] knowledge_gap

**Logged**: 2026-08-30T11:20:00
**Priority**: medium
**Status**: pending
**Area**: backend

### Summary
用户指出某云 API 的行为与我理解不同（已变更）。

### Details
我引用的旧版文档已过时，实际返回结构变了。

### Suggested Action
引用文档时标注版本/日期，不确定先搜最新。

### Metadata
- Source: user_feedback
- Tags: 文档过时
```

## 案例 4：best_practice — 可推广

```markdown
## [LRN-20260830-004] best_practice

**Logged**: 2026-08-30T14:05:00
**Priority**: medium
**Status**: promoted
**Area**: tests

### Summary
改 API 后必须 regenerate 客户端，否则运行时类型不匹配。

### Details
修改端点忘了 regen，本地 tsc 过了但线上报错。

### Suggested Action
升级进 AGENTS.md：改 API → 1) regen 2) tsc --noEmit。

### Metadata
- Source: error
- Pattern-Key: harden.api_change
- Recurrence-Count: 2
```

## 案例 5：feature — 缺失功能

```markdown
## [FEAT-20260830-001] 导出 Excel

**Logged**: 2026-08-30T15:00:00
**Priority**: medium
**Status**: pending
**Area**: frontend

### Requested Capability
用户想要把分析结果导出成 Excel。

### User Context
周报场景，手动复制太累。

### Complexity Estimate: medium

### Suggested Implementation
复用鲁班(luban-automation)的 excel 脚本思路，或接 openpyxl。

### Metadata
- Frequency: recurring
```

## 反模式（别这样记）

- ❌ 把 `.env` 内容整段贴进 Details（密钥泄漏）
- ❌ 写"AI 又傻了"不写具体什么错（无法复用）
- ❌ 覆盖已有 LEARNINGS.md（首次初始化必须 no-op）
- ❌ 把整段对话 transcript 贴进来（噪音+可能含隐私）
