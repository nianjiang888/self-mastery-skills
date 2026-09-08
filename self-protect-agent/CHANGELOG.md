# CHANGELOG · self-protect-agent

## v2.0.1 （2026-09-01，小升级）
- `protect.py` 的 `scan` / `check` 新增 `--json` 输出：以机器可读 JSON 打印结果，便于嵌进 CI / pre-commit 钩子做门禁（退出码仍为 0/1/4）。
- 红线库新增 4 条高价值规则：
  - `RL-FORK-BOMB`（block）：fork bomb `:(){ :|:& };:`。
  - `RL-DROP-DB`（block）：`DROP DATABASE` 整库删除。
  - `RL-GIT-CLEAN`（warn）：`git clean -f` 强制清除未跟踪文件。
  - `RL-CHMOD-000`（warn）：`chmod 000` 权限清零把自己锁门外。
- `RL-CURL-PIPE` 扩展：除 `curl ... | sh` 外，新增覆盖 `wget ... | sh` / `wget ... ; sh` 管道下载即执行。
- `check_command` 同步覆盖上述命令（scan 与 check 判定一致）。
- 文件数不变（仍为 11 文件），仅规则与输出能力增强；版本号三处一致（SKILL.md / EVENT_VERSION / redlines.json version）。

## v2.0.0 （2026-09-01）
- 初始发布。self 系列第 7 个成员。
- 主引擎 `protect.py`：scan / check / record / audit 四命令。
- 确定性代码闸门 `redline_engine.py`：allowlist + 路径保护 + 批量检测 + 对外发送校验。
- 红线规则库 `redlines.json`：allowlist + 4 风险面（destructive/privilege/external_send/prompt_injection）共 16 条规则。
- 实物证据机制：`.redline-event-*.json` + `near-miss-log.jsonl` + `redline-report.md`。
- 理论打底：海恩法则 / Bird 三角 / 瑞士奶酪模型 / 最小权限 / 影响×可逆性矩阵 / 纵深防御五柱。
- 文档：SKILL.md / FAQ / README / SELF_EVAL / 3 篇 references（protect-theory / near-miss-method / redline-design）。
- 退出码约定：0 通过 / 1 需确认 / 4 已拦截（对应 guard 系列"第五态"）。
