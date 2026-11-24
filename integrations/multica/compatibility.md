# Multica 兼容证据和隔离边界

核对口径为 Multica 官方仓库 `6368504e1181a0365013ca5796ec453bf9535f11` 和本机 Desktop 与内置 CLI `0.12.1`（CLI 构建提交 `fc8028d76`）。系统 PATH 没有独立 CLI。已只读执行内置 CLI 的 version 和帮助，未登录或切换 Workspace。服务部署与源码可能不同，以目标部署试验为准。

| 能力 | 已核对行为 |
|---|---|
| 导入 | URL 使用 GitHub 默认分支或显式 ref；解析器通过 GitHub commits API 分辨带斜杠的 branch 并支持固定 SHA。归档接受 `.skill` 或 `.zip`。保留可导入的相对附属路径。服务会过滤部分文件，使用导入后证据验证完整性。 |
| 限制 | 每个文本文件不超过 1 MiB，附属最多 512 个、总计 8 MiB，上传请求上限 16 MiB。正文单计。精简包再执行 V3 自身更严格的审阅和完整性检查。 |
| 版本 | 导入不是实时同步。Workspace revision、Git 提交及实际 Runtime 内容哈希分开记录。刷新支持带来源的 URL Skill，会覆盖人工编辑并保留绑定；本地归档或 Runtime 本机导入没有可刷新的 URL。 |
| 权限 | 导入、覆盖、刷新和编辑的权限可能不同。部署源码中 import overwrite 要求创建者，refresh 支持创建者或 owner/admin。Agent Skills 的编辑须有 Agent 管理权限。Workspace 共享范围需确认。 |
| 传递 | Agent Instructions 独立于 Workspace Skill。daemon 在运行准备阶段根据 provider 写入内容和日志回执。当前源码中 Codex 写到该运行的 Codex home，Claude Code 使用执行目录的 `.claude/skills/`；其他 provider 路径由运行信息确定。若还需写入指令文件，以目标执行环境为边界。 |
| Qoder provider | `qoder_cloud` catalog Agent 的 Skills 来自 Qoder Agent，服务端拒绝 Multica Workspace Skill 追加绑定。本机 Qoder Runtime 有原生 Skill 目录支持，原 V3 Qoder 接入保留。见 [provider 限制](https://github.com/multica-ai/multica/blob/6368504e1181a0365013ca5796ec453bf9535f11/server/internal/handler/qoder_catalog.go#L207-L242) 和 [本机交付实现](https://github.com/multica-ai/multica/blob/6368504e1181a0365013ca5796ec453bf9535f11/server/internal/daemon/execenv/context.go#L411-L414)。 |
| Runtime-local | Agent Skills 可发现某些 Runtime 上的本机 Skill。官方文档注明 Claude Code/Codex 有逐 Agent 停用能力。无授权不操作。Workspace 与本机出现同名时，路径或名称可能经调整；根据日志与字节校验，不预设优先级。 |
| CLI | 本机核对 skill import/list/get/refresh 和 agent get/update、agent skills list/add/set 的帮助。add 保留原有，set 替换。解绑使用官方 UI 单项操作。 |

用于 HiMate 的 daemon clone、worktree、临时运行目录与容器按实际 Git 根独立登记。现有 Skill 用当前工作目录和 V3 私有登记校验结构，一处注册不能自动覆盖其他机器或 Git 根。在该 Runtime 用户和文件系统内先用 `detect_project.py --cwd <实际目录> --diagnose` 检查；必要时由用户明确授权后使用既有 register。不要根据 Issue 字段、项目名、共享 Git remote 或未经审阅的环境变量推断信任。审批及运行验证阶段不要使用登记原始 HiMate 工作树来试运行。

来源 [官方 Skills](https://multica.ai/docs/skills) · [Agent 配置](https://multica.ai/docs/agents-create) · [Agents](https://multica.ai/docs/agents) · [Daemon](https://multica.ai/docs/daemon-runtimes) · [Provider 对照](https://multica.ai/docs/providers) · [CLI](https://multica.ai/docs/cli) · [GitHub 导入实现](https://github.com/multica-ai/multica/blob/6368504e1181a0365013ca5796ec453bf9535f11/server/internal/handler/skill.go) · [归档实现](https://github.com/multica-ai/multica/blob/6368504e1181a0365013ca5796ec453bf9535f11/server/internal/handler/skill_import_archive.go) · [Runtime 回执](https://github.com/multica-ai/multica/blob/6368504e1181a0365013ca5796ec453bf9535f11/server/internal/daemon/execenv/receipt.go)。
