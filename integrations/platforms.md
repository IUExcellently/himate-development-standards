# 用户级平台集成

| 平台 | V3 渲染入口 | 发现与激活边界 |
|---|---|---|
| Codex | `~/.agents/skills/<name>/SKILL.md` | 本地用户级 Skills，可显式选。相同名称可能并列出现，先检查有效选择。 |
| Claude Code | `~/.claude/skills/<name>/SKILL.md`，本机明确配置目录可随 `CLAUDE_CONFIG_DIR` | 个人 Skill 在本地工作会话生效，企业或运行模式可能限制。V3 不追加 CLAUDE.md。 |
| Kiro CLI | `~/.kiro/skills/<name>/SKILL.md` | 官方文档支持本地原生 Skills 和 slash 命令。自定义 agent 可能需要启用 `skill://` 资源，由用户审查，不修改现有 agent。 |
| Kiro IDE | 同 CLI | 官方 IDE 支持全局 Skills，IDE 的 GitHub URL 导入对根目录有限制。此处使用本地安装，避免借 Power 或 Always Steering 模拟激活。 |
| Qoder CLI / IDE | `~/.qoder/skills/<name>/SKILL.md` | 可从 CLI 列表或 IDE 的 Skills 面板核对。不同产品代际及多目录同名冲突按实际用户客户端判断。 |

记录五个可区分的阶段。安装回执及文件完整、客户端可发现、模型选中、正文被读、规则实际应用。后四项需有对应的运行证据，客户端已运行时可能需要重新开会话。不同部署的外部文件权限、Kiro agent 和云端支持各自生效。V3 没有注册 Hook 或修改平台权限。当前验证状态见 [V3 报告](../reports/v3-delivery.md)。

机制来源 [Agent Skills](https://agentskills.io/specification) · [Codex](https://developers.openai.com/codex/skills) · [Claude Code](https://code.claude.com/docs/en/skills) · [Kiro](https://kiro.dev/docs/skills/) · [Qoder CLI](https://docs.qoder.com/cli/Skills) · [Qoder IDE](https://docs.qoder.com/extensions/skills)。
