# HiMate 工作树与模块

登记根目录为 `/Users/yanzu/Documents/webProject/hichatwb`，基线分支 `dev`，HEAD `9e8ed003d4d870e42dd4b8bb0ea8319bcea7ff05`。以真实路径、Git 根和 6 个版本无关的结构/内容指纹共同识别。其他 clone、worktree 或同名目录须用户明确登记后匹配。

| 范围 | 入口与事实源 |
|---|---|
| 前端 | `frontend/pnpm-workspace.yaml`、各 app 的 manifest、锁文件、`.trellis/spec/frontend/index.md` |
| Java | `backend/pom.xml` 的 Maven 聚合。Gateway、User、Chat、AgentHub、Adapter、Admin、Sync、Form、Workbench、Scheduler、Connector 及 Common、Feign Client |
| Python | `himate-dispatcher/pyproject.toml`、`requirements*.txt`、`.importlinter`、`app/main.py` |
| 数据库 | 根 README、`backend/sql/baseline-all-20260831.sql`、`backend/sql/migration/` 及 Cairn 迁移知识 |
| 跨端 | `docs/contracts/agui-v1/`、现行 Controller/DTO/消费端实现、Cairn SSE/UI Block 相关条目 |
| 工作流 | `AGENTS.md`、`.trellis/workflow.md`、各工具项目配置与 `.cairn/steering/` |

项目证据与版本读取日期为 2026-11-23。文件级前置快照保存在原安装环境的 reports 目录中。
