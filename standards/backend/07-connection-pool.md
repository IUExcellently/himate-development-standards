# HikariCP 与连接生命周期

适用 JDBC、DataSource、连接池、数据库路由与运行参数。依据 Boot 3.5、HikariCP 6.3.3、JDBC 21 与 PG 目标版本。代码证据见 [E06](../../references/coding-evidence.md)。

- POOL-01 MUST。先按服务、profile、外部配置确认数据访问框架、实际 DataSource 类型、池数量、手动连接、事务管理器、部署副本、数据库节点及连接预算。POM 与 YAML 是配置证据，运行时参数来自获准环境。默认用容器托管 DataSource 与已有自动配置，保持每个已定义数据源一套明确生命周期。禁止按请求、SQL 或业务方法创建 HikariDataSource。
- POOL-02 MUST。自行获取的 ResultSet、Statement、Connection 用 try-with-resources，及时归还池。Spring 托管访问走 Mapper/JdbcTemplate 或匹配的 DataSourceUtils 获取/释放，避免直接关闭事务绑定底层连接。连接失效遵循驱动与池机制。长 I/O、等待和异步工作避免无必要持有连接。泄漏检测用于诊断，不能替代关闭。
- POOL-03 REVIEW。每个 DB 节点的应用预算 = max_connections − 管理/维护预留 − 其他应用占用 − 非池连接。用各服务峰值实例（含扩容/滚动发布）× 每实例指向该节点的各池上限求和，计及迁移与 REQUIRES_NEW 附加占用。再结合事务并发、连接持有时间、DB CPU/I/O、等待和吞吐测量选值。禁止把预算上限或当前模块默认值当通用最优值。

| 参数 | 调整原则 |
|---|---|
| maximumPoolSize / minimumIdle | 分清上限与空闲目标；按峰值、冷启动和预算确定。Hikari 未指定 minimumIdle 时与 max 相同是基线行为，宜先确认实际配置。 |
| connectionTimeout / validationTimeout | 分别是借用与验证预算；validationTimeout 小于 connectionTimeout；与接口 deadline、驱动及数据库语句超时分别配置并联调。 |
| idleTimeout / maxLifetime | idleTimeout 在可缩池时起作用；maxLifetime 对照数据库、中间件与网络层的连接时限并留裕量，在用连接归还后才退役。 |
| keepaliveTime / leakDetectionThreshold | keepalive 仅用于空闲连接且小于非零 maxLifetime；按真实网络空闲终止行为定。泄漏阈值结合连接持有分布，仅用于诊断。 |
| initializationFailTimeout / poolName | 根据启动策略确定失败/延迟恢复方式与 readiness；用可追踪的稳定池名区分服务与数据源。 |
| autoCommit / readOnly | 明确连接默认值与框架事务重设关系；readOnly 不能替代授权、写保护验证或路由决策。 |

- POOL-04 REVIEW。只有实际多数据源、主从或读写分离时应用相应规则。核对写入、锁定读、事务内数据源固定、读己之写、复制延迟、主从切换与故障降级，禁止仅按 `readOnly=true` 推断可路由副本。
- POOL-05 SHOULD。复用已有监控看 active、idle、pending、borrow latency、创建失败、超时、事务时长、慢 SQL、锁等待、实例数。调优记录当前配置和预算、压测/指标、候选、风险、回滚及复测；缺遥测时只给候选与验证法。新增监控依赖走审批。现存大池值、无边界等待与每次新建连接都需按受影响场景评审。
