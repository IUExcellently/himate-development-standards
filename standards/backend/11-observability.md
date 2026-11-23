# 日志与可观测性

适用 Java 日志、跨服务链路与运行指标。基于 Boot 3.5 Actuator/Micrometer（仅已启用模块）、SLF4J/Logback 与 [E10](../../references/coding-evidence.md)。

- OBS-01 MUST。沿用 SLF4J 参数化日志及服务现有日志框架。按模块边界关联 traceId/requestId 与允许披露的业务标识；在线程、SSE 或消息边界传播必要上下文并清理 MDC。日志包含事件、结果与诊断所需 cause，避免重复印栈、循环大量 INFO 或完整响应。
- OBS-02 SHOULD。选择与用户体验相关的指标，例如入口耗时、流首字和错误、远程调用超时、事务时长、锁等待、慢 SQL、Kafka lag/DLQ、Redis 时延或热点。池指标见 [连接池](07-connection-pool.md)。标签保持低基数，用户或会话 ID 用获准的日志/trace 关联。
- OBS-03 MUST。审查凭证、用户消息、SQL 参数和异常对象泄露风险。使用已有脱敏和采样设施，并验证外部平台配置与日志保留受授权。新增分析 SDK、Exporter 或监控依赖走审批。紧急临时排障日志需限定范围与生命周期。
