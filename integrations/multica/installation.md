# 原生导入、绑定与更新

仅有配置计划授权时执行审阅、离线预演、包生成和必要的脱敏检查。真实 Workspace 的导入、刷新、绑定、解绑、修改 Instructions 或运行任务，需要用户明确批准对应 Workspace、Agent、Runtime 与操作。隔离试验先创建外部独立 Git clone，需要 worktree 时从该独立 clone 派生。直接从 HiMate 原仓库执行 `git worktree add` 会写入其 Git 元数据。禁止将 HiMate 原始工作树作为运行落点。确认 Runtime 的实际执行目录和权限，尤其检查 daemon 可能在执行目录写入的 AI 文件。

## 选定版本和来源

独立检出本仓库功能分支 `feat/v3.1-multica-integration` 的获准完整 commit。先审阅脚本、规范和需共享的内容。将输出目录建在任何 Git 工作树之外。以下 `$revision` 须填独立核对的 40 位提交号，`$archive` 须指向尚不存在的 `.skill` 文件。POSIX 用 `python3`，Windows 可用 `py -3`。

```sh
git checkout --detach "$revision"
python3 -B scripts/validate.py
python3 -B scripts/multica.py package --revision "$revision" --output "$archive" --dry-run
```

`--apply` 只生成外部归档，不调用 Workspace 服务。排查路径无误后可本地生成。报告保存版本、commit、文件数和内容 SHA-256。检查归档及只读证据时用 `python3 -B scripts/multica.py verify --archive "$archive"`。

- **GitHub URL**。Multica 当前服务端支持 [仓库 URL](https://github.com/IUExcellently/himate-development-standards)、`/tree/<ref>` 和 `/blob/<ref>/SKILL.md`。使用打包预演输出的固定提交 URL，且该提交需要已在远程可访问。裸仓库地址会读默认分支。按分支 URL 支持带斜杠的分支，但受 GitHub ref 查询可用性影响。根目录 URL 会纳入其可导入的附属文件，务必先审阅整个引用。入库后核对清单和所有正文。固定 SHA 的来源刷新仍读取同一 SHA。
- **本地归档**。使用审阅过的 `.skill` 文件。当分支未发布、GitHub API 受限，或只希望共享精简运行文件时，归档可保持固定内容与完整附属目录。Workspace 中的 Import from local/runtime 是另一种从已配置 Runtime 发现的本机 Skill 复制方式，可能复制到旧版本或轻量包装。以目标部署 UI 入口为准，本地归档使用已核对的 CLI `--file`。
- **权限与数据**。Workspace 内成员可能查看内容。只共享获得批准的规范包。静态扫描覆盖已知密钥和内网地址样式，代码证据仍含项目内模块、表结构参考、相对路径和接口约定，需核对公司政策及 Workspace 成员范围。无法共享时使用经安全审查的固定提交或在规范源审议脱敏后重新打包。不要上传登记、回执、备份、本机日志、Issue 原始数据或凭证。

## 只读预演和授权后的操作

先核对本机命令 `multica version`、`multica skill import --help`、`multica agent skills --help`。本机被验证的版本在 [兼容性](compatibility.md) 记录。查询真实 Workspace 也应在已明确授权的作用域内进行。CLI 最好显式指定工作区，凭证由客户端原有安全机制提供。

```sh
multica --workspace-id "$workspace" skill list --output json > "$inventory"
multica --workspace-id "$workspace" agent skills list "$agent" --output json > "$bindings"
multica --workspace-id "$workspace" skill get "$skill" --with-content --output json > "$export"
python3 -B scripts/multica.py plan --archive "$archive" --workspace "$workspace" --agent "$agent" --inventory "$inventory" --bindings "$bindings" --workspace-export "$export"
```

`$inventory`、`$bindings` 和 `$export` 保存在已授权的私有工作目录。只有查到同名 Skill 才执行 get 并传 export。预演是只读的，返回候选命令及应保留的绑定，不执行其中的任何命令。断网、鉴权失败和超时不算空清单，不能以错误响应代替成功返回的空数组。同名而版本未知、内容不同或多个匹配时先审阅，不重复创建。导入成功后再按 Skill ID 核对正文，重新预演绑定。若固定 GitHub URL 导入比精简包多出文档等文件，预演会给出额外路径和全量哈希。逐项核对该固定提交及 Workspace 实际内容，经脱敏审查后可重跑并传 `--reviewed-extras-sha256 <全量哈希>`。缺失或变更的必需文件始终阻止绑定。实际改动前再次刷新清单，确认 ID、revision 和内容未漂移。

获准后，使用 Workspace Skills 的 URL 导入，或按 CLI 本地导入。导入冲突默认停止。先确认 Agent 的 Runtime provider 支持 Workspace Skills。官方 `qoder_cloud` Agent 由 Qoder Agent 自身提供 Skills，服务端会拒绝下列追加绑定。支持绑定的 Agent 推荐 UI 单项添加或 `agent skills add`，它保留其他绑定。 `agent skills set` 会整体替换。先后查询绑定并对比。Instructions 在 Agent 页面保存完整原指令后只追加一份通用模板，按角色加一个补充。CLI `agent update --instructions` 设置完整值，只有已合并原文且获准时才适用。

```sh
multica --workspace-id "$workspace" skill import --file "$archive" --on-conflict fail --output json
multica --workspace-id "$workspace" agent skills add "$agent" --skill-ids "$skill" --output json
```

## 刷新、回滚和解绑

- 更新前保存当前 Skill 内容、revision、来源和 Agent 绑定证据，确认人工编辑是否允许被覆盖。GitHub 已更新与 Workspace 已刷新分别记录。获准刷新 URL 来源时，用 `multica skill refresh <id>`。它按已有来源覆盖正文和附属文件，保留身份和绑定。若需从固定旧 SHA 前进，单纯刷新不会更改 ref。确认新归档或 URL，再使用目标部署支持的经批准替换流程。支持的 archive 导入可用显式覆盖策略，经原作者权限核对后更新同名 Skill。本地归档和 runtime-local 导入无可刷新来源。
- 更新或回滚后核对相同 ID 及其他绑定，重新验证每个 Agent 的下一次独立运行。保留原归档和 Instructions 版本以供回滚。刷新失败保留旧版；别根据一次失败盲目重试或覆盖人工内容。
- 移除时使用 Agent 的 Skills 页面单项 Remove，或停用特定绑定以保留配置。CLI 0.12.1 的 skills 组只列出 list/add/set，避免用 set 模拟单项删除。预演可用 `plan --remove`。仅在另行获准并核对所有 Agent 使用情况后删除 Workspace Skill。原 Instructions 仅移除本次受控追加段，其他内容保持一致。底层用户级 Skills 由各自原有管理流程维护。

操作后按 [分层验证](verification.md) 核对。
