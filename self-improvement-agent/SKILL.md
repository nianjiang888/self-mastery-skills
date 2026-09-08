---
name: self-improvement-agent
display_name: AI 自我改进
version: 1.1.0
description: AI 自我改进 v1.1.0（主动 Agent）。你每次纠正 AI、AI 报错、你想要的缺失功能，它都自动记成永久记忆；高频经验升级进 CLAUDE.md/AGENTS.md，稳定经验一键抽成新技能。越用越懂你，不再重复犯同一个错。覆盖：纠错日志/错误记录/需求沉淀/经验升级/跨会话记忆/技能抽取/项目知识库/日志检索/周报复盘。触发词：技术「自我改进/AI记忆/纠错日志/经验沉淀/持续学习/项目记忆/CLAUDE.md/AGENTS.md/跨会话记忆/技能抽取/迭代优化/feedback loop/日志检索/周报」；口语「AI总忘事怎么办/让AI记住我的习惯/AI老犯同一个错/怎么让AI越用越聪明/把纠错记下来/AI报错自动记录/项目经验怎么沉淀/别再犯同样的错了/AI怎么学我的偏好/教AI长记性/记一笔」；英文「self-improving / AI memory / learn from mistakes / continuous improvement / project memory / feedback loop / promote learning / weekly review」；人名「无（这是底层工具，被所有人引用）」。用法：AI 出错或被你纠正时，你说一句"记一笔，你刚才应该用 pnpm 不是 npm"，它自动分类写进项目 .learnings/；想翻旧账 --find、想看本周 --review。同宇宙推荐：墨子(mozi-engineer)工程纪律红线、鲁班(luban-automation)办公自动化出脚本、毕昇(skill-forge)一键造技能、context-bridge 跨会话记忆。
license: MIT
---

# AI 自我改进（self-improvement-agent）

> 元工具定位：这是**底层基础设施**，不抢任何人格的戏。孔明/子房/鲁班/墨子都可以反过来引用它——它让所有人格"越用越懂你"。

AI 每次都忘、你每天重复纠正同一件事——这是所有 AI 用户最普遍的痛。本技能把"纠错→沉淀→升级→复用"做成一条自动链路。

## 它解决什么

| 场景 | 没有本技能 | 有本技能 |
|---|---|---|
| AI 又犯了上周你纠正过的错 | 你再骂一遍 | AI 翻开 .learnings/ 自己看见，不再犯 |
| AI 不知道你项目用 pnpm 不是 npm | 每次都要讲 | 升级进 CLAUDE.md，永久记住 |
| 你发现一个好做法 | 说完就忘 | 记成 best_practice，团队共享 |
| 某条经验特别通用 | 锁在某个对话里 | 一键抽成新技能，喂给社区 |

## 核心机制（三层棘轮 ratchet）

```
你纠正 / AI报错 / 你要新功能
        │
        ▼
 .learnings/ 写日志（LEARNINGS / ERRORS / FEATURE_REQUESTS）
        │  每次纠错 = 一次性成本，写进永久 DNA
        ▼
 高频 / 通用经验 → 升级到 CLAUDE.md / AGENTS.md / SOUL.md
        │  重复≥3次 或 高优先级 → 升永久记忆
        ▼
 稳定经验 → 抽成新技能（联动毕昇 forge_skill.py）
        │  经验反哺所有用户
        ▼
   AI 越用越懂你（闭环）
```

## 主动工作流（Agent 照做）

### 第一步：首次初始化
在写入任何日志前，确保项目根存在 `.learnings/` 与三个文件；缺失则创建（**绝不覆盖已有文件**）：

```bash
# 由 self_improve.py 自动完成，或手动：
mkdir -p .learnings
# LEARNINGS.md / ERRORS.md / FEATURE_REQUESTS.md 见仓库 templates
```

### 第二步：按触发写日志

| 触发 | 写到 | 分类 |
|---|---|---|
| 命令/操作失败、异常、报错 | ERRORS.md | — |
| 用户纠正你（"不对，应该用 pnpm"） | LEARNINGS.md | correction |
| 用户告诉你你不懂的事 | LEARNINGS.md | knowledge_gap |
| 你发现更好的做法 | LEARNINGS.md | best_practice |
| 用户要缺失功能（"怎么不能导出？"） | FEATURE_REQUESTS.md | — |

每条带元数据：`Priority`(low/medium/high/critical) / `Status`(pending) / `Area`(frontend/backend/infra/tests/docs/config) / `Source` / `Tags` / 可选 `Pattern-Key`（重复模式去重键）。

### 第三步：升级（promote）
当一条经验满足**全部**：
- `Recurrence-Count >= 3`，且
- 跨至少 2 个独立任务出现，且
- 30 天窗口内

→ 提炼成一条短预防规则，追加到：
- 项目事实/约定 → `CLAUDE.md`
- 工作流/自动化 → `AGENTS.md`
- 行为规范/沟通 → `SOUL.md`
- GitHub Copilot 上下文 → `.github/copilot-instructions.md`

原条目 `Status` 改 `promoted`，加 `Promoted` 字段。

### 第四步：抽技能（extract）
当一条 LEARNING 满足任一：被 2+ 相似条目 `See Also` 链接 / 高优先级且已 resolved / 用户说"存成技能" → 调用 `scripts/extract_skill.py`，联动毕昇 `forge_skill.py` 生成新技能骨架。**不重造轮子**。

## 红线（绝不碰）

- 不记密钥、token、私钥、环境变量、完整源码/配置——只记短摘要或脱敏片段
- 不覆盖已有 .learnings/ 文件（首次初始化的 no-op 原则）
- 不臆造未发生的纠错或功能请求
- 升级到 CLAUDE.md 等文件前先确认该文件存在/可写，且只**追加**短规则、不覆盖你写的内容
- **核心功能 100% 本地**：日志、检索、周报、升级全在本地跑，无需联网。只有你主动配置群机器人 webhook 后，`notify.py` 才会发消息；不配就纯本地，一条数据不出本机
- 不主动扫描/读取你整个项目代码——只在被明确叫到时，记那一句教训

## 与人格宇宙的联动

- **墨子(mozi-engineer)**：工程纪律红线。墨子拦截的 secret/injection 事件，可顺手记一笔到 ERRORS.md（category=integration）
- **鲁班(luban-automation)**：办公自动化出脚本。鲁班生成的脚本若报错，记 ERRORS.md，下次直接避开
- **毕昇(skill-forge)**：一键造技能。抽技能时直接调 `forge_skill.py`，复用现成供应链
- **context-bridge**：跨会话记忆。本技能的 .learnings/ 是项目级；context-bridge 是会话级——两者正交，可同时启用

详见 `references/cross-universe.md`。

## 中文开发者语境（我们的护城河）

原版面向英文 /Users 语境。我们面向中文开发者：路径用 `D:/项目`、包管理默认 pnpm、git 别名 `gst/gp/gc`、错误日报可推**飞书/钉钉/企业微信**群机器人。详见 `references/chinese-dev-context.md`。

## 可选 Hook（opt-in）

装 hook 后每次提示词自动注入"该记一笔吗"评估。主路径**不依赖 hook**——SKILL.md 指令已足够驱动；hook 只是零摩擦增强。详见 `references/hooks-setup.md`。

## 文件地图

```
SKILL.md                        ← 你正在看
README.md                       快速上手
FAQ.md                          中文用户痛点 Q&A
LEARNINGS-TEMPLATE.md           纠正/洞察/知识缺口/最佳实践 模板
ERRORS-TEMPLATE.md              命令失败模板
FEATURE_REQUESTS-TEMPLATE.md    用户需求模板
SKILL-EXTRACT-TEMPLATE.md       抽技能模板（联动毕昇）
references/examples.md          真实案例库
references/chinese-dev-context.md  中文开发者语境（原创）
references/hooks-setup.md       hook 安装（opt-in）
references/upgrade-rules.md     升级判定规则
references/cross-universe.md    与人格宇宙联动（原创）
scripts/self_improve.py         主引擎
scripts/extract_skill.py        抽技能（联动毕昇）
scripts/notify.py               飞书/钉钉/企微 webhook
resources/self_improve.json     分类/优先级/area 映射
```
