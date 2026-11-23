# 规范证据索引

以下仓库相对路径以 [工作树](project-profile.md) 为准。配置值为静态证据；运行配置或业务状态以任务实测为准。

| ID | 对应规则 | 代码、配置与验证线索 |
|---|---|---|
| E01 | JAVA、SPR | `backend/pom.xml` 的 JDK 21 与模块声明；`backend/himate-chat/src/main/java/com/hisense/himate/chat/service/impl/ChatServiceImpl.java` 的服务实现；`.trellis/spec/backend/index.md`。 |
| E02 | SPR、JAPI | `backend/himate-agenthub/src/main/java/com/hisense/himate/agent/controller/AgentChatController.java`；`himate-common` 的 `GlobalExceptionHandler.java`；各 `himate-feign-client/*/pom.xml`；Chat 附件 Controller/测试。 |
| E03 | TX | `backend/himate-agenthub/src/main/java/com/hisense/himate/agent/util/TransactionHooks.java`，以及 Workbench Service 的并发写与现有事务边界。 |
| E04 | SQL | `backend/himate-user/src/main/resources/mapper/UserRoleMapper.xml`、`backend/himate-connector/src/main/resources/mapper/MessageRecordMapper.xml`、`.trellis/spec/backend/database-guidelines.md`。按 Mapper 和真实查询参数确认每次计划。 |
| E05 | DB | `backend/sql/baseline-all-20260831.sql`、`backend/sql/migration/V202610191700-agent-ui-block-registry.sql`、Cairn 的 `L3-guide-backend-sql-migration.md`。 |
| E06 | POOL | `himate-chat/src/main/resources/application-prod.yml` 的 env 默认 max/idle/borrow 为 40/10/10000ms；`himate-user/src/main/resources/application-prod.yml` 为 30/5/30000ms；`himate-workbench/src/main/resources/application.yml` 为 25/5/3000ms。均在 `backend/` 内。Trellis 数据库说明记录现有服务 schema 隔离及无 dynamic-datasource；本次受检 Java 源码未找到 `AbstractRoutingDataSource`、`HikariDataSource`、`DataSourceBuilder` 或 `DriverManager.getConnection` 的实现命中。未核实外部生效值、真实 Bean、读写分离拓扑或运行预算。 |
| E07 | CON | `himate-common` 的 `AuditLogExecutorConfig.java`、`himate-agenthub` 的 `AgentLogExecutorConfig.java`、`himate-workbench` 的 `SchedulerThreadPoolConfig.java`。 |
| E08 | MID | `himate-sync` 的 `DlqKafkaConsumer.java` / `XxlJobConfig.java`、`himate-connector` 的 `MessageKafkaConsumer.java` / `KafkaRetryConfiguration.java`、`himate-chat` 的 `RedisConfig.java`。 |
| E09 | SEC | `himate-gateway` 的 `UserAuthFilter.java` / `AdminAuthFilter.java`、`himate-workbench` 的 `ShortLinkSecurityConfig.java`、`himate-agenthub` 的 `FeedbackPullAuthFilter.java`。 |
| E10 | OBS | `himate-chat` 的 `MdcScope.java` 及测试，使用实际模块 POM确认 Actuator 依赖与监控 profile。 |
| E11 | TEST | `himate-chat` 的 `AguiUpstreamUiBlockRoundTripTest.java`、`ChatAttachmentControllerTest.java`；`himate-agenthub` 的 `AgentLogExecutorConfigTest.java`。 |
| E12 | FE、CSS | `frontend/apps/{pc,mobile}/src/utils/request.ts` 与 `src/styles/globals.css`，`apps/admin/src/api/request.ts` 与 `src/styles/global.css`，`packages/api-client/src/client.ts`、`packages/chat-transport`、UI Kit 主题、各 app 的 Router 与 store。 |
| E13 | PY | `himate-dispatcher/.importlinter`、`app/bootstrap/lifespan.py` 的客户端回收、`app/api/routes/dispatch.py` 的背压与取消、`app/api/sse/bridge.py` 和 `app/agents/dispatcher/{builder,state}.py`。 |
| E14 | API | `docs/contracts/agui-v1/{10-event-map,20-event-payload,30-ui-blocks,40-inbound,90-known-gaps}.md`、Chat `sse/agui/`、Dispatcher SSE bridge、前端 `chat-transport` 与两端 UI Block 解析。 |
