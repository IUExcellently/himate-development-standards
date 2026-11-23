# 代码与工作流分析

文件级清点覆盖工作树中的跟踪、未跟踪和忽略项，包含项目级 AI 配置、构建描述、文档和业务源码。语义分析按模块入口、构建清单、配置、协议边界与代表性实现交叉核对。关键证据见 [证据索引](../references/coding-evidence.md)，未逐行审计所有业务实现。

1. 前端是三 app 的 React workspace。共享业务协议、请求底层和流处理由现有 packages 承担，各端继续保留 UI、路由和请求包装差异。
2. Java 由单 Maven 聚合管理，模块角色和依赖不同。Spring Boot 3.5.16 / Java 21，使用 MyBatis-Plus、Feign、PostgreSQL。已读源码显示 Gateway 鉴权、模块特定异常处理、服务事务回调以及 Kafka / XXL-Job，规则按行为加载。
3. 部分服务的 Hikari 配置差异明显，数据库 schema 与服务边界对应。部署拓扑、生产连接预算和实际配置仍待运行条件下查证。生产容量不套统一值。
4. Dispatcher 固定 LangGraph/DeepAgents 版本，同步和异步依赖、DI、资源释放由现有分层约束。背压、取消、检查点和流输出必须作为修改后的验证点。
5. 协议以 AG-UI V1 与真实转换链为准，具体旧资料的现行/归档属性按 README。跨端演进需测试真实事件与消费者解码。
6. Trellis / Cairn 历史和工作区 Hooks 只读。历史文档中的测试基建、性能指标和生产运行值应在变更时重新定位证据。
