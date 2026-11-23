# Spring 事务

适用 Service 写入、事务拓扑、并发写入与连接池变更。依据 Spring Framework 6.2/PG，见 [E03](../../references/coding-evidence.md)。

- TX-01 MUST。根据业务原子性在 Service 边界设最短可用事务。避免事务内长计算、等待、循环远程 I/O、SSE 长连接。跨服务外部副作用明确提交和失败恢复顺序。现有 `TransactionHooks` 的提交后回调不提供持久可靠投递保证。
- TX-02 MUST。代理模式经可拦截的 bean 方法调用事务入口。优先公开方法并核对代理类型，接口代理和类代理可见性能力不同。同类 self-invocation、private/final 拦截限制和异步线程不会自动继承事务。回滚缺省针对 RuntimeException/Error，项目或注解可覆盖；checked exception 需显式约定，吞异常不等于回滚。核对 propagation、isolation、timeout、readOnly 与实际事务管理器及已有事务属性。
- TX-03 REVIEW。REQUIRED 参加现有事务或创建新事务；REQUIRES_NEW 暂停外层并用独立事务，计算同时持有连接和锁等待；NESTED 检查管理器/驱动 savepoint 支持；SUPPORTS 可无事务；MANDATORY 需要现有事务；NOT_SUPPORTED 暂停事务；NEVER 遇已有事务失败。按具体拓扑选择，避免通过 REQUIRES_NEW 掩盖 rollback-only。
- TX-04 MUST。并发写入明确业务唯一键或幂等键、隔离级别及竞争结果。按业务选版本号乐观锁、条件更新、约束或必要的行锁，保持一致加锁顺序，核对锁等待、丢失更新和重复提交。死锁/序列化失败仅在外层完整、可重试且有预算的事务边界重试，避免重复非幂等副作用。
- TX-05 SHOULD。单查询按真实一致性需求决定是否建立事务。readOnly 是提示及配置语义，须验证驱动和数据库行为。多数据源显式匹配 manager、mapper 和路由。用回滚、异常、重复和并发测试验证，反例为给所有方法加写事务或给所有读取加锁。
