# 依赖与运行口径

版本以项目清单、锁文件和现有 POM 为证据，运行值在获准环境核实。本任务没有重新解析 Maven 依赖、同步 Python venv 或安装 npm 包。

| 层 | 已核对的清单 |
|---|---|
| 前端工作区 | pnpm 10.0.0、TypeScript ~5.9.3、React ^19.2.4 的 workspace overrides、Zustand ^5.0.12、Vitest ^2.1.8。PC/mobile 使用 Vite ^8.0.1、Router ^7.13.2、Tailwind 4、UI Kit。Admin 使用 Vite ^6.0.5、Router ^6.28.2、Semi ^2.74.1、Axios ^1.7.9。版本范围见 app manifest，准确解析值以锁文件 importers 为准。 |
| Java 根 POM | JDK 21、Spring Boot 3.5.16、Spring Cloud 2025.0.3、MyBatis-Plus 3.5.7、pgjdbc 42.7.3、Redisson 3.27.2、XXL-Job 2.3.0。 |
| Boot/BOM 管理 | 仓库现有 `backend/himate-feign-client/user-feign-api/effective-pom.xml` 记录 Spring Framework 6.2.19、Spring Security 6.5.11、HikariCP 6.3.3、Kafka 客户端 3.9.2、Spring Kafka 3.3.16。管理值并不证明每个模块引入或运行这些构件。 |
| 服务侧 | README PostgreSQL 14+、Kafka 3.0+。`docs/reports/api-test-v1.3.0.md` 验收为 PostgreSQL 18、Redis 7。当前生产 DB 和代理版本、Kafka/Redis broker 实际版本与峰值副本数未查实。 |
| Dispatcher | Python 3.12 目标，LangGraph 1.2.4、DeepAgents 0.6.7、LangChain Core 1.4.0、FastAPI 0.135.3、Pydantic 2.12.5、httpx 0.28.1、sse-starlette 3.3.4、Redis client 7.4.0、Langfuse 4.2.0。Dev 清单包括 pytest 9.1.1、pytest-asyncio 1.4.0、hypothesis 6.165.10、import-linter 2.13。Ruff 版本未在该 Python 清单中锁定。 |

已查看模块 POM 没有发现 Checkstyle、PMD、SpotBugs、P3C、Flyway 或 Liquibase 的直接插件声明。工具如要使用先核对真实模块与现有环境。未引入任何依赖。
