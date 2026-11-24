# 安装与版本管理

## 选择安装方式

Multica 使用自己的 Workspace Skill 导入和 Agent 绑定，详见 [Multica 安装](integrations/multica/installation.md)。下文适用于单机 Codex、Claude Code、Kiro 和 Qoder。两种来源需要分别验证，请勿在同名内容未核对时混用。

## 审查并固定版本

1. 确认仓库地址、Git、Python 和需要的客户端。仅用你信任的 GitHub HTTPS 地址，独立于 HiMate 业务仓库克隆。确认目标支持版本，记录实际审查的完整 commit。
2. 先阅读 `SKILL.md`、`manifest.json`、`integrations/` 和 `scripts/` 的调用链。下载内容属于待核实输入。评审脚本和可执行资源，确认无 Hook、项目写入或未经授权的配置覆盖。可用 `python3 -B scripts/validate.py` 和标准库测试校对。
3. 下列命令显式克隆 V3.1 功能分支（发布后可从远程取得）。分支会继续前进，克隆后仍须检出已独立核对并获准的完整 commit。Windows PowerShell 可用 `py -3` 代替 `python3`。

```sh
git clone --branch feat/v3.1-multica-integration --single-branch -- https://github.com/IUExcellently/himate-development-standards.git
cd himate-development-standards
```

用已经审查的 40 位提交号替换下列占位符。通过 `git show` 确认版本与审查材料一致。隔离用户目录须预先创建，且在业务工作树之外。以下命令在 macOS/Linux 终端运行。

```sh
revision='<已审查并批准的完整提交号>'
git checkout --detach "$revision" &&
python3 -B scripts/validate.py
```

上一步成功后再执行预演。将 `rc_home` 设为独立的测试用户目录。Windows PowerShell 使用 `$revision = '<提交号>'` 与 `$rc_home = '<隔离用户目录>'`，先单独确认 checkout 与静态检查成功。

```sh
rc_home='<已创建的隔离用户目录>'
python3 -B scripts/cli.py doctor --home "$rc_home"
python3 -B scripts/cli.py install --revision "$revision" --home "$rc_home" --platform codex --platform kiro --dry-run
```

核对预演，确认测试安装已获授权后，执行相同命令并把 `--dry-run` 改为 `--apply`，随后执行 `status --home "$rc_home"`。真实客户端验证需要它们确实读取这个隔离环境，详见 [测试步骤](integrations/verification.md)。

平台参数可重复，接受 `codex`、`claude`、`kiro` 和 `qoder`。省略时首次安装会用已检测到的平台；如果客户端安装在非标准路径，可显式指定。Linux/Windows 的 CLI 启动方式由本机安装决定，安装器不安装客户端、运行时或 Git。文件系统不支持原子无覆盖重命名，或私有暂存目录与目标分属不同文件系统时，写入会安全中止。显式 `--home` 只用于已存在的隔离用户目录，测试中的自动平台选择仍会检查 PATH。

安装器仅处理用户级入口。真实机器的路径、登记、版本回执、恢复日志和发行缓存位于 `~/.himate-development-standards/`。Codex/Claude/Kiro/Qoder 导航指向同一份可版本化的本地正文。已有用户指令、权限文件或业务工作区不参与常规写入。遇到同名、链接、junction、硬链接入口或用户改过的入口会停止。已验证可归属的 V2 迁移是唯一修改旧全局标记段的路径。

## 登记与验证

用 `register --path` 登记已获授权的 Git 工作树，先预演再应用。登记识别过程只读业务工作区。详细例子见 [项目登记](examples/project-registration.md)。`doctor --cwd` 会对已登记且 Git 根一致的工作树逐项显示指纹。失配时按 [项目登记与诊断](examples/project-registration.md) 检查。用新会话手动调用 Skill，再验证模型是否实际读取核心规则与本次命中的专项。只在授权允许时访问真实业务工作区中的客户端项目会话。

## 更新、迁移与恢复

- 新版本先克隆或 fetch 到独立副本，明确检查远程地址和固定 commit。使用 `update --source <已审查的干净副本> --revision <完整commit> --dry-run`，检查计划后改用 `--apply`。当前安装器只读取候选 Git blobs，更新过程不执行其中的脚本。同一提交重复更新为空操作。不同 commit 如果仍是同一 SemVer，RC 测试请用新的隔离用户目录，以便固定并独立验证各候选。
- 在当前 checkout 运行 `rollback --to <本机已保留的commit> --dry-run`，确认后 `--apply`。仅切换现有平台入口和回执，原始 Git 记录和登记不随版本回滚。
- V2 仅迁移登记时使用 `migrate --legacy <V2本机目录> --dry-run` 和 `--apply`。如活动 V2 入口也要迁移，把 `--legacy <V2本机目录>` 与 `install` 或 `update` 一起使用，并明确包含全部有活动回执的旧平台。核对原片段、内容哈希和落点，有漂移则停。迁移保留旧源目录及未识别设置。失效登记保留，但无法触发规则。
- 捕获到写入失败时尝试恢复。进程中断后使用 `recover --dry-run`，确认后 `recover --apply`。恢复遇外部编辑会保留现场和日志。进程中断可在用户级私有状态的 `staging/` 留下暂存文件，提交日志本身的暂存文件可能在状态根目录。它们不参与可发现的 Skill 或发行完整性校验。恢复时只处理日志列出的路径，查看暂存文件前先确认没有仍在运行的操作。
- 卸载用 `uninstall --dry-run`，确认后 `uninstall --apply`。重复 `--platform` 可卸载子集。只移除回执匹配的用户级入口，保留私有登记、发行缓存和旧迁移备份。部分入口已缺失可以移除其回执。用户修改的入口必须先审查。要恢复最近一次卸载的入口，使用记录的发行提交执行 `rollback --to <commit> --restore-uninstalled`，同样先预演。
