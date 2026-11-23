# Java 测试与审查

适用受影响模块测试、跨层回归和交付检查。使用项目已有 Maven、JUnit/Mockito 与相关测试配置，见 [E11](../../references/coding-evidence.md)。

| 规则 | 级别 | 验证 |
|---|---|---|
| TEST-01 | SHOULD | Service 业务规则、异常、幂等与并发；Controller 验证输入、权限、错码与序列化；数据访问检查过滤、NULL、稳定分页、约束、批量和真实驱动行为。选择针对变更的一组，必要时使用真实 PostgreSQL 隔离环境验证 SQL 方言和事务。 |
| TEST-02 | SHOULD | 事务回滚、唯一约束、同键并发写、锁等待与死锁重试在隔离 PG 测试。慢 SQL 留计划与规模证据。连接池验证获取超时、归还、上限、断连恢复、长事务占用、多实例预算及关闭释放。 |
| TEST-03 | MUST | 未授权禁止生产压测、生产 DDL 或接触真实敏感数据。保留既有失败基线，报告实际命令和未验证项。优先按模块及既有 profile 运行，禁止用全量重构来解决局部基线问题。 |
| TEST-04 | REVIEW | 先检查项目已有 Maven 门禁、Checkstyle、PMD、SpotBugs、P3C 或 SQL 分析设施，再决定是否应用。引入工具走依赖审批；静态工具无法替代事务拓扑、执行计划、连接预算和兼容审查。 |

完成后按路由复核实际 diff。Mapper 查绑定/WHERE/计划/索引/事务，Controller 查契约/校验/授权，DataSource 查池生命周期与事务，Kafka 查幂等、offset 和跨边界一致性。
