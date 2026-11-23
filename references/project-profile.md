# HiMate 工作树与模块

只有用户明确登记的 Git 工作树才可激活。当前工作区的真实 Git 根还需匹配公开清单中的结构和内容指纹。clone、linked worktree 或同名项目独立核验。登记和本机环境信息只保存在用户级状态中。

| 范围 | 入口与事实源 |
|---|---|
| 前端 | `frontend/pnpm-workspace.yaml`、各 app 的 manifest、锁文件、`.trellis/spec/frontend/index.md` |
| Java | `backend/pom.xml` 的聚合模块与实际服务 POM、BOM 和 profile |
| Python | `himate-dispatcher/pyproject.toml`、`requirements*.txt`、`.importlinter`、`app/main.py` |
| 数据库 | 根 README、`backend/sql/baseline-all-20260831.sql`、`backend/sql/migration/` 及 Cairn 迁移知识 |
| 跨端 | `docs/contracts/agui-v1/`、现行 Controller/DTO/消费端、Cairn SSE/UI Block 条目 |
| 工作流 | 当前适用的用户与项目规则、`.trellis/workflow.md` 和 `.cairn/steering/` |

版本和规则证据见 [依赖清单](dependency-inventory.md) 和 [代码证据](coding-evidence.md)。涉及运行配置及历史阶段时以本任务的现行仓库证据为准。
