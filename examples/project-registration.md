# 工作树登记及增量路由

将下面的 `<项目路径>` 替换为经授权的本机 Git 工作树目录，包括常规 clone 或 linked worktree。登记一个 Git 根后，可在其子目录激活。不同 Git 根需分别登记。用本机 Python 3.10+，PowerShell 可把 `python3` 换为 `py -3`。

```sh
python3 -B scripts/cli.py register --path "<项目路径>" --dry-run
python3 -B scripts/cli.py register --path "<项目路径>" --apply
python3 -B scripts/cli.py doctor --cwd "<项目路径>"
python3 -B scripts/resolve_rules.py --cwd "<项目路径>" --task "评审HikariCP配置" --tag pool --loaded standards/core.md
```

同名目录或 Git 仓库仅凭名字不能激活。已登记目录发生迁移时，可用 `unregister --path` 预演和撤销旧路径，再显式登记新根。不要将注册文件提交到 Git。敏感任务用 `--path` 和 `--tag` 路由，避免把敏感数据放入命令行。
