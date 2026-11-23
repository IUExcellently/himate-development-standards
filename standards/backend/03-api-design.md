# Java API 设计

适用 Java Controller、DTO、VO、Feign 与错误映射。优先 [跨端契约](../api-contracts.md) 的联动约束，代码证据 [E02](../../references/coding-evidence.md)。

- JAPI-01 MUST。确认现行路由、版本前缀、HTTP 方法及 status、业务 code 和响应结构。沿用该模块已有 `Result` 与异常处理。SSE、下载和内部协议维持其专用响应语义。新 API 按资源选择 HTTP verb，GET 保持无业务写副作用；禁止为统一风格随手更改既有状态码或错误响应。
- JAPI-02 MUST。使用输入 DTO/Bean Validation 与服务校验，区分传输格式、业务约束和权限，字段白名单映射至持久层，外发 VO 避免泄露内部字段。分页设合理上界和稳定排序，排序字段采用允许清单。明确缺省/null/空、日期时间和 Long 字段的 wire 表示。
- JAPI-03 MUST。明确写入重试语义、幂等键范围和冲突响应。批量接口说明原子或逐项处理、重复项、失败结果和容量。对已有客户端支持必要的兼容字段和部署顺序。涉及契约变化须获得相应授权。
- JAPI-04 MUST。上传校验尺寸、内容、名称和所有权；下载核对授权和响应头，流必须及时释放。配置请求时限及客户端重试预算，避免放大下游。授权和错误输出按 [后端安全](10-security.md)。
- JAPI-05 SHOULD。样例为覆盖真实 Gateway 路由与 Controller 序列化后由消费者解析。反例为只测试 DTO 类结构、只改 Java 字段而忽略 TypeScript/Python、或将异常栈当作兼容错误契约。
