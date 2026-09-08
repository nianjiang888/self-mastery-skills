# FAQ · 中文用户痛点

## Q1：记了会不会泄露我的代码 / 密钥？
不会。红线规定：不记密钥、token、私钥、环境变量、完整源码。只记**短摘要或脱敏片段**（比如"用 pnpm 不是 npm"，而不贴你的 package.json）。真要记敏感上下文，会先问你。

## Q2：老板 / 同事能看到我的 .learnings 吗？
`.learnings/` 默认在你项目根，跟代码一起。想本地私有就加进 `.gitignore`（仓库默认忽略）；想团队共享就提交。两种都支持，你定。

## Q3：和 Cursor / Claude Code 的 rules 文件冲突吗？
不冲突。`.learnings/` 是 markdown 日志，AI 自己读；`CLAUDE.md`/`AGENTS.md` 是升级后的永久规则。本技能**会**往这些文件追加，但只追加短规则，不覆盖你写的内容。

## Q4：AI 老记一些没用的废话怎么办？
每条日志有 `Priority` 和 `Status`。低优先级、一次性的，你可以手动在 `.learnings/*.md` 里把 `Status` 改成 `wont_fix` 并写原因；AI 也会在周期复盘时清理。文件是普通文本，你随时改。

## Q5：中文路径 / 中文命令怎么处理？
本技能面向中文开发者：路径示例用 `D:/项目`、包管理默认 pnpm、git 别名 `gst/gp/gc`。详见 `references/chinese-dev-context.md`。

## Q6：必须装 hook 才能用吗？
不用。主路径靠 SKILL.md 指令驱动，AI 主动记。hook 只是"每次提示词自动提醒记一笔"的零摩擦增强，可选。详见 `references/hooks-setup.md`。

## Q7：抽技能要单独装毕昇吗？
抽技能时 `extract_skill.py` 会找毕昇 `forge_skill.py`；若环境已装 `skill-forge`，直接复用；没装就只产出 SKILL.md 骨架，不影响主功能。

## Q8：和你们其他人格包（孔明/子房/鲁班/墨子）冲突吗？
不冲突，反而互补。本技能是底层基础设施，被所有人引用——墨子拦的红线事件、鲁班出的脚本报错，都能顺手记一笔。见 `references/cross-universe.md`。

## Q9：记多了文件很大、AI 一读就爆 context 怎么办？
`.learnings/*.md` 是短条目（每条几十到几百字）。AI 只在"该记/该查"时才读，不会全灌。原版 330KB 全灌的毛病我们规避了——见墨子(mozi-engineer)的"路由引擎"思路。

## Q10：能跨项目共享同一条经验吗？
项目级经验在 `.learnings/`；跨项目/跨会话用 `context-bridge`。两者正交，可同时启用。通用经验升级到 `CLAUDE.md` 后，同项目所有人都受益。

## Q11：记错了 / 记了一条废话，怎么删？
`.learnings/*.md` 是普通 markdown，你随时改：
- 整条删除：打开对应文件，删掉从 `## [LRN-...]` 到下一个 `---` 的那一段即可。
- 不想真删、只想标记作废：把那条 `**Status**: pending` 改成 `**Status**: wont_fix`，并加一句原因。AI 周期复盘时会跳过 wont_fix。
- 命令行也行：`python self_improve.py --find "关键词"` 先定位 ID，再手动删对应段落。

## Q12：升级到 CLAUDE.md 后，发现升级错了能回退吗？
能。升级动作是**追加**一条短规则到 CLAUDE.md 末尾，不覆盖你原有内容：
- 打开 `CLAUDE.md`，删掉最后追加的那一行规则即可。
- 同时把原日志条目 `**Status**: promoted` 改回 `pending`，保持两边一致。
- 没把握就先别 promote——`--review` 会列出"建议升级"项，你确认后再跑 `--promote`。

## Q13：想改一条已记的内容（比如补充细节）怎么办？
直接编辑对应 `.md` 文件里那条目的 `### Details` 段落。日志是给人看的文本，没有"锁定"，改完下次 AI 读到就是新内容。建议补 `Pattern-Key` 方便以后 `--find` / 查重复。
