# Errors

命令失败与集成错误。

**优先级**：low | medium | high | critical
**状态**：pending | in_progress | resolved | wont_fix

> 红线：不记密钥、token、私钥、环境变量、完整源码。只记短摘要或脱敏片段。

---

## [ERR-YYYYMMDD-XXX] 命令或集成名

**Logged**: ISO-8601 时间戳
**Priority**: high
**Status**: pending
**Area**: frontend | backend | infra | tests | docs | config

### Summary
一句话描述什么失败了

### Error
实际报错信息（脱敏，去掉路径/密钥/内部域名）

### Context
- 尝试的命令 / 操作
- 使用的输入或参数
- 环境（可选）

### Suggested Fix
若可定位，写可能的解法

### Metadata
- Reproducible: yes | no | unknown
- Related Files: 路径/文件
- See Also: ERR-20250110-001（如重复出现）

---
