# 由 AI 安装

用户可只提供仓库 URL 和目标平台。例如“从 https://github.com/IUExcellently/himate-development-standards 为我的 Codex 安装 HiMate Skill，先预演并验证”。

AI 依次执行以下动作。

1. 核对 GitHub 地址和用户授权，确认 Git、Python 与客户端，克隆到独立开发目录。
2. 核实 Git commit 与发行版本，阅读并审查脚本和规则，按 [安装指引](../INSTALL.md) 跑静态验证。
3. 预演显示落点、要写的文件、冲突、备份和恢复方式。已有授权范围内应用。遇到覆盖未知状态、提升权限或受权限拒绝的操作时停止受影响步骤。
4. 用 `status` 检查回执，用 `doctor --cwd` 确认受信工作树。只登记用户指定目录。新会话验证客户端发现、选择、正文读取、所选规则及遵循行为各自到达的层级。
