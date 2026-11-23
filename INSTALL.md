# 安装与版本管理

## 审查并固定版本

1. 确认仓库地址、Git、Python 和需要的客户端。仅用你信任的 GitHub HTTPS 地址，独立于 HiMate 业务仓库克隆。确认目标支持版本，记录实际审查的完整 commit。
2. 先阅读 `SKILL.md`、`manifest.json`、`integrations/` 和 `scripts/` 的调用链。下载内容属于待核实输入。评审脚本和可执行资源，确认无 Hook、项目写入或未经授权的配置覆盖。可用 `python3 -B scripts/validate.py` 和标准库测试校对。
3. 下面的 POSIX 命令需在已审查的 checkout 中执行。Windows 用 `py -3` 替换 `python3`，把 `$revision` 用 PowerShell 的语法赋值为 `$revision = git rev-parse HEAD`。执行前确认该提交确实是审查过的版本。

```sh
git clone -- https://github.com/IUExcellently/himate-development-standards.git
cd himate-development-standards
```

完成源码审查、确认此 checkout 已包含 V3 后，从同一目录执行。

```sh
revision="$(git rev-parse HEAD)"
python3 -B scripts/cli.py doctor
python3 -B scripts/cli.py install --revision "$revision" --platform codex --platform kiro --dry-run
python3 -B scripts/cli.py install --revision "$revision" --platform codex --platform kiro --apply
python3 -B scripts/cli.py status
```

平台参数可重复，接受 `codex`、`claude`、`kiro` 和 `qoder`。省略时首次安装会用已检测到的平台；如果客户端安装在非标准路径，可显式指定。Linux/Windows 的 CLI 启动方式由本机安装决定，安装器不安装客户端、运行时或 Git。文件系统不支持原子无覆盖重命名时，写入会安全中止。显式 `--home` 只用于已存在的隔离用户目录，测试中的自动平台选择仍会检查 PATH。

安装器仅处理用户级入口。真实机器的路径、登记、版本回执、恢复日志和发行缓存位于 `~/.himate-development-standards/`。Codex/Claude/Kiro/Qoder 导航指向同一份可版本化的本地正文。已有用户指令、权限文件或业务工作区不参与常规写入。遇到同名、链接、junction、硬链接入口或用户改过的入口会停止。已验证可归属的 V2 迁移是唯一修改旧全局标记段的路径。

## 登记与验证

用 `register --path` 登记已获授权的 Git 工作树，先预演再应用。登记识别过程只读业务工作区。详细例子见 [项目登记](examples/project-registration.md)。`doctor --cwd` 会显示工作区能否激活。用新会话手动调用 Skill，再验证模型是否实际读取核心规则与本次命中的专项。只在授权允许时访问真实业务工作区中的客户端项目会话。

## 更新、迁移与恢复

- 新版本先克隆或 fetch 到独立副本，明确检查远程地址和固定 commit。使用 `update --source <已审查的干净副本> --revision <完整commit> --dry-run`，检查计划后改用 `--apply`。当前安装器只读取候选 Git blobs，更新过程不执行其中的脚本。同一已安装版本无需更新，高版本才可前进。
- 在当前 checkout 运行 `rollback --to <本机已保留的commit> --dry-run`，确认后 `--apply`。仅切换现有平台入口和回执，原始 Git 记录和登记不随版本回滚。
- V2 仅迁移登记时使用 `migrate --legacy <V2本机目录> --dry-run` 和 `--apply`。如活动 V2 入口也要迁移，把 `--legacy <V2本机目录>` 与 `install` 或 `update` 一起使用，并明确包含全部有活动回执的旧平台。核对原片段、内容哈希和落点，有漂移则停。迁移保留旧源目录及未识别设置。失效登记保留，但无法触发规则。
- 捕获到写入失败时尝试恢复。进程中断后使用 `recover --dry-run`，确认后 `recover --apply`。恢复遇外部编辑会保留现场和日志。进程中断可能留下空目录或同目录暂存文件，已有配置和目录的归属需人工核对。
- 卸载用 `uninstall --dry-run`，确认后 `uninstall --apply`。重复 `--platform` 可卸载子集。只移除回执匹配的用户级入口，保留私有登记、发行缓存和旧迁移备份。部分入口已缺失可以移除其回执。用户修改的入口必须先审查。要恢复最近一次卸载的入口，使用记录的发行提交执行 `rollback --to <commit> --restore-uninstalled`，同样先预演。
