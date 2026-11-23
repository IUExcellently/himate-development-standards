# 四平台接入

| 平台与本机 CLI | 接入点 | 自动作用范围 |
|---|---|---|
| Codex 0.142.5 | `~/.agents/skills/himate-development-standards/SKILL.md` 和 `~/.codex/AGENTS.md` 的有标记追加段 | 用户级引导根据工作目录选择，Skill 原生可显式调用。 |
| Claude Code 2.1.310 | `~/.claude/skills/himate-development-standards/SKILL.md` 及 `~/.claude/CLAUDE.md` | 全局 Memory 只给项目门槛与指引，正文根据模型指令加载。 |
| Kiro CLI 3.3.0 | `~/.kiro/steering/himate-development-standards.md` | `inclusion: always` 只包含定位和门槛。工作区 Steering、当前 Agent 与 IDE/CLI 模式可能影响适用和读取。 |
| Qoder CLI 1.0.46 | `~/.qoder/skills/himate-development-standards/SKILL.md` | 用户级 Skills 可按描述触发或显式调用。仅做最佳努力适配。IDE 与 CLI 各自刷新后核对。 |

四端适配不注册 Hook，不更改模型权限、工作区信任或 Trellis 运行机制。入口通过绝对路径读取单一外部正文。静态校验使用真实入口文件及安装回执。具体运行探针与未验证项见 [验证报告](validation-report.md)。

客户端机制依据 [Codex Skills](https://developers.openai.com/codex/skills)、[Codex AGENTS.md](https://developers.openai.com/codex/guides/agents-md)、[Claude Code Skills](https://code.claude.com/docs/en/skills)、[Claude Code Memory](https://code.claude.com/docs/en/memory)、[Kiro Steering](https://kiro.dev/docs/steering/)、[Qoder CLI Skills](https://docs.qoder.com/cli/Skills) 和 [Qoder IDE Skills](https://docs.qoder.com/extensions/skills)。Qoder 新版产品也识别 `~/.agents/skills`，原生目录优先并按名称去重，见 [Qoder Skills](https://docs.qoder.com/qoder/skills)。
