# 分层验证与多 Agent 验收

用户授权真实隔离 Workspace 和测试 Agent 后再执行本页的运行场景。使用从未用于原始 HiMate 的独立执行根。为每次运行分别记录 Workspace、Agent、Runtime、执行根登记状态、期望的 Git 提交和包哈希、Workspace revision、绑定 ID、Run ID 和实际读取规则。敏感元数据保存在获准的私有位置。

| 层级 | 核对的证据 |
|---|---|
| 导入 | CLI 导入结果或 UI 对象；用 `skill get --with-content` 保存正文证据，并用 `scripts/multica.py verify --archive ... --workspace-export ...` 比对。 |
| 绑定 | 每个 Agent 的 Skills 逐一确认同一 ID 已启用，其他绑定保留。 |
| 交付 | Issue 执行日志中打开 Run 的 **Context received**，查看该 Skill 条目的路径、哈希和交付状态。Not verified 加路径只证明 daemon 写入包，Not delivered 表示失败。 |
| Runtime 发现 | 在相同隔离 Runtime 的新运行查看原生发现列表或工具事件中的实际入口，识别别名、同名和历史版本。 |
| 实际读取 | 查看检测脚本输出和真实工具调用中的 `SKILL.md`、核心及专项路径。保留必要的脱敏结果。 |
| 实际遵循 | 用 diff、审批记录、冲突决策和测试证明所选规则在这次任务生效。 |

对仅获准读的 Runtime 路径，用 `verify --archive ... --runtime-directory ... --runtime-local-directory ...` 比较声明的文件字节。若同时提供完整的 `--workspace-export`，Workspace Runtime 比对以该导出声明的全量路径为范围，包含 GitHub URL 导入的额外文件。只有所有声明文件存在时才给出可和 daemon 交付回执对照的哈希前缀。仅有归档时，结果只覆盖归档声明的路径。入口 frontmatter 或名称可能被 Runtime 重写，实际哈希也会变化。核对差异文件和语义，保留冲突证据。相同名称或版本号不证明内容一致。只检查一次同一会话同一规则，不全量注入。不同 Agent、版本或工作树分别核验。

| 用例 | 验收 |
|---|---|
| A Java Controller、B SQL | 同一登记工作树的新会话使用 Java/Spring/API 或 SQL/PostgreSQL/事务规则。 |
| C HikariCP、D CSS | 加载池、事务、数据库并验证参数来源；CSS 用局部作用域并保留全局样式边界。 |
| E 依赖、F Trellis 冲突 | Agent 暂停相关步骤并请求用户明确裁决，无获准证明时清单与锁文件不变。 |
| G 非 HiMate、J Skill 缺失 | 同名未登记项目不激活；入口、内容或脚本缺失时报告具体失败，只停止受影响工作。 |
| H 跨 Agent、I 更新 | Lead、Engineer、Reviewer 都独立记录实际读取；更新后各 Agent 的新 Run 获取目标版本或明确报告不一致。 |

依赖审批用角色任务或脱敏假设模拟，避免意外变更生产 Bot、Issue 或其他绑定。执行证据不齐时标记未验证。测试结果见 [V3.1 集成报告](../../reports/v3.1-multica.md)。
