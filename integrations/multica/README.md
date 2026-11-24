# Multica 接入

Multica 管理 Workspace、Agent、Squad、任务和执行日志。运行由 daemon 在所选机器和 Runtime 上交给 Codex、Claude Code 等工具完成。Workspace Skill 存在 Multica，Agent Instructions 随该 Agent 的运行提供，底层权限与真实工作目录另行判断。

[安装与解绑](installation.md) · [官方能力与边界](compatibility.md) · [分层验证](verification.md) · [Squad 交接](squad-guide.md)

| Agent | 安装 Instructions |
|---|---|
| 单 Agent | 保留已有指令，追加一份 [通用入口](agent-instructions.md)。 |
| Lead | 通用入口加 [Lead 补充](lead-instructions.md)。 |
| Engineer | 通用入口加 [Engineer 补充](engineer-instructions.md)。 |
| Reviewer | 通用入口加 [Reviewer 补充](reviewer-instructions.md)。 |

指定 Agent 分别绑定同一 Workspace Skill。正文统一维护于根目录的 `standards/`，平台入口只负责定位、门槛和职责。实际加载从根 [SKILL.md](../../SKILL.md) 开始。
