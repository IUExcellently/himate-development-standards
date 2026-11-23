# HiMate 全局 AI 开发规范

本目录是规范正文唯一来源，面向已登记的 HiMate 工作树。用户级入口在会话内请求项目校验，路由器按任务和文件返回需要读取的规范。项目源码、契约及 AI 工作区保持只读。

- [Skill 入口](SKILL.md)
- [项目识别与技术证据](references/project-profile.md)
- [依赖版本](references/dependency-inventory.md)
- [Java、前端及调度器证据](references/coding-evidence.md)
- [官方参考](references/official-references.md)
- [规范冲突](references/conflict-analysis.md)
- [分析报告](reports/code-analysis.md)
- [四平台接入报告](reports/integration-report.md)
- [验证报告](reports/validation-report.md)

## 从当前工作区运行

从本目录执行下列命令，将 `--cwd` 设为目标工作目录。Python 3.10+、Git 和标准库即可。使用 `-B` 禁止生成字节码文件。

```sh
python3 -B scripts/detect_project.py --cwd /Users/yanzu/Documents/webProject/hichatwb
python3 -B scripts/resolve_rules.py --cwd /Users/yanzu/Documents/webProject/hichatwb --task '修改 Kafka 消费者的幂等逻辑' --path backend/himate-connector/src/main/java/com/hisense/himate/connector/kafka/MessageKafkaConsumer.java
python3 -B scripts/status.py --cwd /Users/yanzu/Documents/webProject/hichatwb
```

通过 `--path`、`--tag` 和 `--loaded` 反复传入目标、补充领域、排除本会话已读项。路径路由与语义提示结合，含糊任务先验证实际文件再补选。只分析已登记根，其他 worktree 要单独加入 `manifest.json` 的 canonical roots。

## 安装和撤销

```sh
python3 -B scripts/install_global.py --dry-run
python3 -B scripts/install_global.py --apply
python3 -B scripts/install_global.py --uninstall --dry-run
python3 -B scripts/install_global.py --uninstall --apply
python3 -B scripts/validate.py
```

`--platform` 可限定平台，允许重复。安装前预览，备份和回执在外部主目录 `.install-state/`。撤销保留部署后被其他操作改动的文件并提示处理。命令按本机用户配置和权限运行。已有客户端需要新开会话或刷新 Skill 列表。

Codex 可用 `$himate-development-standards`，Claude Code 与 Qoder 可用 `/himate-development-standards`。Kiro 的用户级 Steering 提供条件入口，也可在 HiMate 会话显式要求读取外部 `SKILL.md`。自动读取正文仍取决于各端模型、有效指令和外部目录读取权限。运行能力分项见接入报告。
