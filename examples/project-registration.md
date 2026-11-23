# 工作树登记及增量路由

将下面的 `<项目路径>` 替换为经授权的本机 Git 工作树目录，包括常规 clone 或 linked worktree。登记一个 Git 根后，可在其子目录激活。不同 Git 根需分别登记。用本机 Python 3.10+，PowerShell 可把 `python3` 换为 `py -3`。

```sh
python3 -B scripts/cli.py register --path "<项目路径>" --dry-run
python3 -B scripts/cli.py register --path "<项目路径>" --apply
python3 -B scripts/cli.py doctor --cwd "<项目路径>"
python3 -B scripts/resolve_rules.py --cwd "<项目路径>" --task "评审HikariCP配置" --tag pool --loaded standards/core.md
```

同名目录或 Git 仓库仅凭名字不能激活。已登记目录发生迁移时，可用 `unregister --path` 预演和撤销旧路径，再显式登记新根。不要将注册文件提交到 Git。敏感任务用 `--path` 和 `--tag` 路由，避免把敏感数据放入命令行。

## 指纹失配诊断

在已登记目录执行 `python3 -B scripts/detect_project.py --cwd "<项目路径>" --diagnose`。使用隔离配置时追加 `--home "<隔离用户目录>"`。也可以用同一套参数运行 `scripts/cli.py doctor --cwd "<项目路径>"`。未登记目录不会被探测。Git 根须与登记一致才会输出逐项指纹结果。

| 公开检查文件 | 当前必须命中的字面标记 |
|---|---|
| `README.md` | `HiMate`、`docs/contracts/agui-v1/` |
| `frontend/pnpm-workspace.yaml` | `packages:`、`apps/` |
| `frontend/package.json` | `pnpm@` |
| `backend/pom.xml` | `<java.version>`、`himate-agenthub` |
| `himate-dispatcher/pyproject.toml` | `[tool.ruff]` |
| `docs/contracts/agui-v1/README.md` | `AG-UI` |

指纹只匹配每个 UTF-8 文件的前 256 Ki 个字符。诊断会指出文件缺失、解析到工作树之外、不是普通文件、不可读、缺少标记，或搜索触及上限。确认是稀疏检出或登记路径变化时，补全获准的工作副本或重新登记正确的 Git 根，再运行诊断。重新登记仍会校验全部指纹。

若 AG-UI 文档搬迁、Ruff 配置拆出或模块名调整属于已确认的业务演进，请提交证据，由 Skill 维护者更新公开指纹并验证同名/未登记仓库仍被拒绝，再安装已审查的版本。诊断期间保持 `active=false`。无需修改业务文件来迎合旧指纹。
