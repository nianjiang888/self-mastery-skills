# 与人格宇宙的联动（本技能原创）

> self-improvement-agent 是**底层基础设施**，不抢任何人格的戏。
> 它和工匠三角（墨子 / 鲁班 / 毕昇）正交——互补，不抢流量，反而互相引用。

## 定位关系

```
                 self-improvement-agent（底层·元工具）
                          │ 记日志 / 升级 / 抽技能
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
   墨子(mozi)         鲁班(luban)        毕昇(skill-forge)
   工程纪律红线        办公自动化出脚本     一键造技能
        │                 │                 │
        └─────────────────┴─────────────────┘
              互相引用 → 工匠三角闭环
```

## 1. 与墨子（mozi-engineer）

- 墨子拦截 secret / injection / license 三道防线事件
- 这类"安全踩坑"可顺手记 `ERRORS.md`（category=integration）
- 例：用户试图贴 AWS AK → 墨子 BLOCK → 记 `ERR-...-aws-key-leak`，下次所有人格都长记性

## 2. 与鲁班（luban-automation）

- 鲁班生成的办公脚本若报错，记 `ERRORS.md`
- 下次鲁班遇到同类输入直接避开，或用 `preflight()` 先校验
- 例：Excel 拆分脚本对超大文件 OOM → 记 `ERR-...-excel-split-oom`，升级"大文件先切片"

## 3. 与毕昇（skill-forge）

- 抽技能时 `scripts/extract_skill.py` 直接调毕昇 `forge_skill.py`
- 复用现成供应链（SKILL.md + 引擎 + 资源 + 打包），**不重造**
- 例：某条 `best_practice` 够通用 → 抽成新技能骨架 → 毕昇补内容 → 上架

## 4. 与 context-bridge（跨会话记忆）

- 本技能 `.learnings/` = **项目级**持久化
- context-bridge = **会话级**上下文搬运
- 两者正交：项目经验留在 `.learnings/`，会话上下文走 context-bridge
- 可同时启用，互不干扰

## 5. 反哺所有人

- 孔明 / 子房 / 年爷 / 申报官 / 范蠡 等人格包，在 SKILL.md 末尾加：
  `同宇宙推荐：self-improvement-agent 让 AI 越用越懂你`
- 用户在任一人格里被纠正 → 该人格可调用本技能记一笔 → 全宇宙受益

## 6. 引用话术（放进各人格 SKILL.md）

```
同宇宙推荐：self-improvement-agent（AI 自我改进，让 AI 越用越懂你，纠错/报错/需求自动沉淀）
```

> 注意：只写 slug + 定位，**不写"去搜索"**（那是一致性红线，年爷教训）。
