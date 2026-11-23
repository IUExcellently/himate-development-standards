---
name: himate-development-standards
description: 在已登记的 HiMate 工作树执行前端、Java、SQL、Python 调度器和 AG-UI 的开发、调试与审查时，按任务加载匹配规范。
---

# HiMate 开发规范入口

从会话环境取得工作区路径，选用本机可用的 Python 3.10+ 解释器，依次传入 `-B`、下方检测脚本路径、`--cwd` 和工作区路径。按本机 shell 语法安全传参。以下 JSON 字符串是路径数据。

- 检测脚本 @@DETECT@@
- 规范入口 @@BODY@@

仅在检测返回 `active=true` 时读取规范入口并遵循按任务加载流程。已经完成同一工作区校验时可复用结果。工作区变化时重新核验。
