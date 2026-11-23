# 版本适用的资料

## Java、Spring 与数据库

- Java 21 与 JDBC 资源、事务、只读语义。[Java SE 21 Connection](https://docs.oracle.com/en/java/javase/21/docs/api/java.sql/java/sql/Connection.html) · [Java SE 21 API](https://docs.oracle.com/en/java/javase/21/docs/api/index.html)
- Spring Boot 3.5 的依赖管理和数据访问，以仓库 3.5.16 的管理值为准。[Boot 3.5 BOM](https://docs.spring.io/spring-boot/3.5/appendix/dependency-versions/coordinates.html) · [Boot 3.5 数据访问](https://docs.spring.io/spring-boot/3.5/reference/data/sql.html)
- Spring Framework 6.2 的代理、异常与事务边界。仅验证 Spring Security 6.5 文档在引入组件的模块适用。[事务注解](https://docs.spring.io/spring-framework/reference/6.2/data-access/transaction/declarative/annotations.html) · [事务传播](https://docs.spring.io/spring-framework/reference/6.2/data-access/transaction/declarative/tx-propagation.html) · [Security 6.5](https://docs.spring.io/spring-security/reference/6.5/index.html)
- Maven BOM、依赖解析与模块边界。[Maven 依赖机制](https://maven.apache.org/guides/introduction/introduction-to-dependency-mechanism.html) · [MyBatis 3 映射](https://mybatis.org/mybatis-3/sqlmap-xml.html)
- PostgreSQL 14 最低声明与 18 测试口径。根据目标环境确认版本再使用新增语法。[PG 14 计划](https://www.postgresql.org/docs/14/using-explain.html) · [PG 18 隔离](https://www.postgresql.org/docs/18/transaction-iso.html) · [PG 18 索引](https://www.postgresql.org/docs/18/sql-createindex.html) · [PG 18 连接配置](https://www.postgresql.org/docs/18/runtime-config-connection.html)
- HikariCP 6.3.3 容量和参数，按该 tag 查询默认、边界和行为。[HikariCP 6.3.3](https://github.com/brettwooldridge/HikariCP/tree/HikariCP-6.3.3)
- Kafka 客户端基线 3.9.2，broker 行为按部署核对。Redis 官网滚动内容仅使用 Redis 7 可验证语义。XXL-Job 项目依赖为 2.3.0，定制部署行为仍需查本仓。[Kafka 3.9](https://kafka.apache.org/39/documentation.html) · [Redis 文档](https://redis.io/docs/latest/develop/) · [XXL-Job 2.3.0](https://github.com/xuxueli/xxl-job/tree/2.3.0)
- 社区实践的原始来源。P3C README 可验证黄山版入口。缺乏证据支持将其他网传版本当成官方现行结论。Google Style 与 P3C 用于命名、边界、资源与审查建议，按项目样例落地。[阿里巴巴 P3C](https://github.com/alibaba/p3c) · [Google Java Style](https://google.github.io/styleguide/javaguide.html)

## 前端与 Python

- React 19 组件及 Hooks、TypeScript 5.9、pnpm 10 workspace 和 Vite 对应代际。[React](https://react.dev/reference/react) · [TypeScript 5.9](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-9.html) · [pnpm 10](https://pnpm.io/10.x/workspaces) · [Vite 8](https://vite.dev/guide/) · [Vite 6](https://v6.vite.dev/guide/)
- Tailwind 4 使用 v4 文档中的现有样式能力，patch 版本以锁文件为准。Semi 和 Zustand API 的具体行为以已安装声明及源版本核对。[Tailwind 4](https://tailwindcss.com/docs/styling-with-utility-classes) · [Semi](https://semi.design/) · [Zustand](https://zustand.docs.pmnd.rs/)
- Python 以 3.12 语义和项目 Ruff 配置为准。[asyncio 3.12](https://docs.python.org/3.12/library/asyncio-task.html) · [PEP 8](https://peps.python.org/pep-0008/) · [Ruff](https://docs.astral.sh/ruff/configuration/)
- LangGraph 1.2.4 和 DeepAgents 0.6.7 的机制用滚动文档作背景，具体 API、事件版本、配置与钩子以固定发布及真实调用为准。[LangGraph 持久化](https://docs.langchain.com/oss/python/langgraph/persistence) · [DeepAgents 概览](https://docs.langchain.com/oss/python/deepagents/overview) · [LangGraph 1.2.4](https://pypi.org/project/langgraph/1.2.4/) · [DeepAgents 0.6.7](https://pypi.org/project/deepagents/0.6.7/)
