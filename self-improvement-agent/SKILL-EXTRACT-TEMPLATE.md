# 抽技能模板（Skill Extraction Template）

当一条 LEARNING 足够稳定、通用，值得变成可复用技能时，用本模板生成新技能的 `SKILL.md` 骨架。

## 抽取判定（满足任一即可）

- 有 2+ 相似条目通过 `See Also` 链接它（重复问题）
- `Status` = resolved 且有可用修复
- 非显而易见（需要实际调试/排查才发现）
- 广泛适用（不限于本项目，跨代码库有用）
- 用户明确说"存成技能"或类似

## 抽取流程

1. 识别候选：满足上述条件的 LEARNING
2. 运行 `scripts/extract_skill.py --dry-run` 预览
3. 运行 `scripts/extract_skill.py <skill-name>` 生成骨架
   - 若环境已装 `skill-forge`，直接复用其 `forge_skill.py` 一键脚手架（不重造）
4. 填 `SKILL.md`：用下方模板，内容自包含、不依赖原对话上下文
5. 把原 LEARNING 的 `Status` 改为 `promoted_to_skill`，加 `Skill-Path`

## SKILL.md 骨架

```markdown
---
name: <skill-name>
version: 1.0.0
description: <一句话功能 + 四路触发词 + 同宇宙>
---

# <技能名>

## 它解决什么
<痛点>

## 何时用
<触发场景>

## 怎么用
<可执行步骤 / 脚本 / 红线>

## 红线
<绝不碰的>

## 来源
提炼自 LRN-YYYYMMDD-XXX（原对话上下文已脱敏）
```

## 质量门（抽取前自检）

- [ ] 解法已验证可用
- [ ] description 无需原上下文也能读懂
- [ ] 代码示例自包含
- [ ] 无项目硬编码值
- [ ] 符合技能命名（小写、连字符）
