# Spring Boot 分层与配置

适用 Java 模块设计、装配、配置和服务调用。依据 Spring Boot 3.5、Spring Framework 6.2 和 [E01–E02](../../references/coding-evidence.md)。

- SPR-01 MUST。Controller 接收请求、校验、取身份并映射响应；Service 承担业务规则、事务与编排；Mapper 负责数据访问和映射；DTO/VO 隔离线协议与持久化 Entity。按实际模块边界使用 Common、Feign Client 与协议包。保留 Gateway 的入口职责和非阻塞链路，避免将业务编排塞进控制器或共享 Common。
- SPR-02 SHOULD。新依赖优先构造器注入，单构造器用 Spring 约定。保持单例无共享请求状态。重量级客户端交给容器管理，提高测试可替换性。反例为每次请求 new 客户端、静态取 Bean 或通过循环注入绕过职责划分。框架明确要求的注入点按官方约束处理。
- SPR-03 MUST。成组配置优先类型化 `@ConfigurationProperties`，已有绑定和 profile 优先。校验单位、范围、缺省与部署覆盖顺序。凭证走现有环境/配置系统。核对配置客户端、环境变量与生效 profile 后描述真实值。新增外部服务或迁移配置须在用户授权内。
- SPR-04 SHOULD。远程调用沿用现有 Feign 与超时预算，评估失败映射、幂等边界和降级语义。变更 shared DTO/Bean 之前核对消费者。Feign 与 JDBC 阻塞调用离开 Gateway 响应式线程。
- SPR-05 REVIEW。按 pom.xml 和模块启动类识别 WebMVC/WebFlux、安全、数据访问及组件组合。不同模块可以沿用不同实现。新架构迁移须获得用户授权，避免全局套用 DDD、CQRS、JPA 或 Spring Security。

推荐链路为 Controller → Service → Mapper，或 Service → 已有 Feign 协议接口。对特殊回调、适配器、内部协议保持当前边界。
