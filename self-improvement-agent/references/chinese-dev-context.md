# 中文开发者语境（本技能原创护城河）

> 原版 self-improving-agent 面向英文 `/Users` 语境。我们面向中文 AI 开发者与中文团队——这是原版没有、也懒得做的一块。

## 1. 路径约定

| 场景 | 写法 | 说明 |
|---|---|---|
| 你的项目根 | `D:/项目/我的应用` | 示例用 D 盘；实际任意盘 |
| 技能仓库 | `D:/Skills` | 你放自己技能的地方 |
| 工作目录 | 用相对路径 `.learnings/` | 不写死绝对路径 |

> 注意：本技能所有示例用 `D:/项目` 这类通用写法，**不写死你机器上的真实路径**，避免把个人环境泄露进日志。

## 2. 包管理默认 pnpm

中文前端团队大量用 pnpm。日志里出现"依赖"相关，默认记：

- 锁文件是 `pnpm-lock.yaml` → 用 `pnpm install`
- 不要无脑 `npm install`（易锁文件冲突）

升级规则示例（进 CLAUDE.md）：

```markdown
## 依赖
- 包管理器：pnpm（不是 npm）→ 用 `pnpm install`
```

## 3. git 别名

很多中文开发者设了别名。记日志时认这些：

- `gst` = git status
- `gp` = git push
- `gc` = git commit

升级规则示例（进 AGENTS.md）：

```markdown
## git 别名
- gst=status, gp=push, gc=commit（本机已设）
```

## 4. 企业协作：错误日报推群（原创）

中文团队用飞书 / 钉钉 / 企业微信。配置自定义机器人后，`scripts/notify.py` 把 ERRORS.md 摘要推到群里，团队共享"今天 AI 踩了什么坑"。

**配置方式（webhook 不写死在包内）**：

1. 在飞书 / 钉钉 / 企业微信里建一个自定义机器人，拿到 Webhook 地址
2. 把地址填到项目 `config.json` 的 `webhook` 字段，或设环境变量
3. 运行 `python scripts/notify.py --today`

> 安全红线：Webhook 地址由**你**在配置里填，包内**不硬编码**任何机器人地址，也不写进 `.learnings/`（那是群可见的，会泄漏）。

群消息示例：

```
【AI 自我改进日报】2026-08-30
- ERR-20260830-002 git push 鉴权失败（已 resolved）
- ERR-20260830-005 构建超时（pending）
共 2 条待处理
```

## 5. 中文 AI 工具词

描述 / 触发词用中文用户真搜的词，方便被搜到：

- 程序员 / AI 工具党 / 码字员
- 让 AI 长记性 / AI 总忘事 / 纠错日志
- pnpm / git 别名 / 飞书机器人 / 企业微信

## 6. 合规提醒

- 群机器人推送**只推脱敏摘要**，绝不推密钥/完整报错路径
- `.learnings/` 若含敏感，加进 `.gitignore` 本地私有
- 抽技能时彻底脱敏，不带走原项目内部信息
