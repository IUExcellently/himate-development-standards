# 真实客户端隔离验证

选定已审查的完整提交，按 [安装手册](../INSTALL.md) 在临时系统用户、虚拟机或有明确隔离配置能力的客户端环境准备 Skill。使用原有系统用户的实际用户级配置必须另行授权。安装器的 `--home` 只改变安装文件落点。需要单独确认客户端以相同用户身份或使用该隔离配置启动。选择至少一个已登记的合成 HiMate Git 工作树和一个未登记的同名 Git 工作树，均放在业务仓库之外。可在 Skill 根使用标准库创建样本，目标目录须已存在，样本子目录由命令新建：

```sh
python3 -B -c 'import sys; from pathlib import Path; sys.path.insert(0,"tests"); from support import project; root=Path(sys.argv[1]); assert root.is_dir(); project(root/"registered"/"himate"); project(root/"unregistered"/"himate")' "<样本父目录>"
```

用 `register --path "<样本父目录>/registered/himate"` 在同一隔离用户环境先预演、再登记。两个样本有相同结构指纹，只有前者应激活。通过 `doctor --cwd` 检查。若用单独的系统测试用户，客户端和安装器均在该用户下运行即可。

## 各端发现与显式调用

| 客户端 | 验证发现 | 验证主动调用 |
|---|---|---|
| Codex CLI / 桌面 | 从隔离用户启动新会话，在 Skill 选择器或 CLI `/skills` 查找唯一的 HiMate 项，记录显示名与来源。 | 在已登记样本会话主动选中 `$himate-development-standards`。 |
| Claude Code | 用隔离用户启动新会话，在斜杠命令建议中查找 `/himate-development-standards`。若存在同名项，核对来源或命名空间。 | 选择该命令，并检查会话中实际运行的检测脚本。 |
| Kiro CLI / IDE | 分别在 CLI 斜杠建议和 IDE 的 Agent Steering & Skills 面板确认。缺失时检查当前 agent 的 `skill://` 资源和运行模式。 | 分别调用 `/himate-development-standards` 或在 IDE 选择对应项。两个结果分别记录。 |
| Qoder CLI / IDE | CLI 执行 `qodercli skills list`，核对来源与 Enabled。仅测试发现可用 `qodercli --config-dir "<隔离用户目录>/.qoder" skills list`。IDE 在 Skills 面板核对，通过配置参数验证 CLI 不能替代 IDE。 | 新会话中调用 `/himate-development-standards`。 |

## 规则加载及行为

1. 先记录平台、版本、已审查提交、用户配置来源及 `status` 中的 `matches_receipt`。这一步验证入口文件和回执。
2. 在已登记样本的全新会话输入“只读评审 `frontend/apps/admin/src/example.css` 的局部样式”。测试自动选择时避免输入 Skill 名称或主动调用，记录实际 Skill 调用或入口读取。看不到相关事件时记为自动选择未验证。
3. 单独开新会话主动调用 Skill，重复相同任务。查看终端调用、文件读取记录或工具审批卡，确认检测返回 `active=true`，实际读取核心、优先级及前端样式规则。再加入 `backend/ExampleController.java`，应增量读取 Java API 和相关契约。记录实际读取路径以及用局部作用域解释方案的证据。仅转述规则名不足以验证读取。
4. 在未登记样本中重复主动调用。应能发现入口，检测返回 `active=false`，会话不应读取项目专属规则正文。工作区中的任何文件和 Git 状态应原样保留。
5. 退出或关闭该隔离客户端会话，卸载前先 dry-run。卸载后重开会话复查入口已移除，并核对原有其他 Skills 和全局配置。文件级检查、发现、自动选择、显式调用、正文读取与遵循分别记为通过、未通过或未验证。

平台路径与适用版本见 [平台集成](platforms.md)。
