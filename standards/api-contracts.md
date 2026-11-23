# API 与跨端契约

- API-01 MUST。对话链路核对 `docs/contracts/agui-v1/` 与真实 producer/consumer。入口为前端 → Gateway → Chat → AgentHub → Dispatcher，命中领域时接 Adapter。按实际路由与协议校核返回路径。现行 API 以 Controller/DTO 及对应实现为准。根 README 指定的历史归档只作背景，`chat-link-open-mode.md` 按 README 保持现行使用。
- API-02 MUST。修改字段、状态码、枚举、ID 格式、错误语义、时间、身份/租户或事件前列出生产者、消费端、保留期和回放影响。保留旧字段缺省与明确 null 的差异，验证 Java 序列化、Python 模型和 TypeScript 解析。协商契约版本、部署顺序、降级、兼容与回滚，跨端同步受本轮授权约束。
- API-03 MUST。SSE 按现行帧定义核对请求/响应头、事件顺序、标识关联、重复、心跳、错误、停止、终止与重连；明确开始流之前的 HTTP/JSON 错误及流开始后的事件错误。检查断开后的取消传播和资源清理。UI Block 按现行信封、注册及转换协议检查真实帧、版本退化、未知类型、持久化/回放和回流，避免把历史信封字段当新实现依据。
- API-04 SHOULD。测试至少采一组真实输出通过下一跳解析。单独验证授权拒绝、异常、终态和历史回放。涉及跨端现状与文档漂移时列出实际代码和契约出处，按优先级处理。
