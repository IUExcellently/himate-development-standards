# HiMate Development Standards

面向已登记的 HiMate Git 工作树的跨平台 Agent Skill。覆盖前端与 CSS/Less、12 项 Java/Spring/PostgreSQL 专题、Python 调度器与 AG-UI/API 契约。只在登记和结构指纹验证通过后应用项目专属规则。

## 交给 AI 安装

> 请从 https://github.com/IUExcellently/himate-development-standards 的 `feat/v3-portable-agent-skill` 分支获取 V3 测试版。按 INSTALL.md 核对源码和获准的完整 commit，检出该 commit 后先在隔离用户目录 dry-run。本次只登记我明确给出的隔离 HiMate 工作树。请分别报告安装、客户端发现、自动或主动选择，以及实际规则加载。

## 支持范围

| 工具 | 用户级落点 | 手动调用 |
|---|---|---|
| Codex | `~/.agents/skills/himate-development-standards/` | `$himate-development-standards` |
| Claude Code | `~/.claude/skills/himate-development-standards/` | `/himate-development-standards` |
| Kiro CLI / IDE | `~/.kiro/skills/himate-development-standards/` | `/himate-development-standards` |
| Qoder CLI / IDE | `~/.qoder/skills/himate-development-standards/` | `/himate-development-standards` |

面向 macOS、Linux 和 Windows 11，要求 Python 3.10+、Git、支持同文件系统原子无覆盖重命名的用户文件系统。Windows PowerShell 可用 `py -3`，macOS/Linux 用 `python3`，Git Bash 选实际安装的 Python。各端安装策略见 [平台说明](integrations/platforms.md)，首次验证见 [真实客户端测试](integrations/verification.md)。

## 使用与维护

- [安装、更新、回滚、卸载及迁移](INSTALL.md)
- [AI 自助安装示例](examples/install-with-ai.md)
- [登记工作树与增量加载](examples/project-registration.md)
- [Skill 入口](SKILL.md) · [版本说明](CHANGELOG.md)
- [仓库对比](reports/v3-repository-comparison.md) · [V3 审计与验证](reports/v3-delivery.md)

发现阶段只公开名称与描述。模型选择入口后，先核验工作区，再读核心规则和命中专项，最后按需查 `references/`。在 `standards/` 维护统一正文，`manifest.json` 维护规则索引和公开指纹。

条件匹配、手动调用、文件读取和遵循规范属于不同验证层级。无法发现时先看 `doctor` 输出、当前用户配置目录、同名入口、客户端或自定义 agent 的 Skills 支持，再在新会话核验。外部规范目录不可读时，沿用既有开发规则并报告限制。

项目级 AI 配置、Trellis、Cairn、权限和依赖保持原样。技术优先级、依赖审批和无法消解的冲突按 [优先级规范](standards/priority.md) 处理。
