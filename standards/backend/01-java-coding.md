# Java 21 编码

适用所有 Java 模块。版本与证据见 [JDK、P3C、Google](../../references/official-references.md) 和 [E01](../../references/coding-evidence.md)。

| 规则 | 级别 | 执行与审查 |
|---|---|---|
| JAVA-01 命名与封装 | SHOULD | 按 `com.hisense.himate.<模块>`、UpperCamelCase 类型、lowerCamelCase 方法与变量、UPPER_SNAKE_CASE 常量。沿用 Controller、Service、Mapper、DTO/VO/Entity 的边界命名。以最窄可见性设计，方法围绕一个业务意图拆分，按概念使用配置、常量或枚举。大型方法按职责评审，避免固定行数、无用途继承、只有一个实现又无明确边界的抽象。 |
| JAVA-02 类型与空值 | MUST | 区分缺失、空列表、0 与 false。优先明确泛型和边界校验，避免 raw type、盲目强转及包装类型拆箱 NPE。金额使用 `BigDecimal` 并明确精度、舍入、货币单位，例如用 `new BigDecimal("0.1")` 代替 `new BigDecimal(0.1)`。时间使用 `java.time`，跨端明确时区及区间端点，优先半开区间；保留现有 wire 类型。 |
| JAVA-03 领域类型 | SHOULD | `Optional` 用于可缺失返回值，DTO 字段、参数及持久化类型沿用既有序列化约定。优先不可变值。重写 equals 同时保持 hashCode 合规，避免以可变属性作为 Map key。 |
| JAVA-04 集合与流 | SHOULD | 按容量证据选择集合，区分 Map 缺键与 null。迭代修改用迭代器或安全收集方式，审查大结果内存、重复遍历及跨线程复合操作。Stream 用于可读纯转换，避免共享副作用和默认引入 parallelStream。 |
| JAVA-05 异常与资源 | MUST | 区分业务和系统异常，包装保留 cause，集中映射并避免重复记栈；避免空 catch、业务捕获 Throwable、finally 覆盖结果和把栈发给客户。显式捕获 InterruptedException 后传播或恢复中断。自行获得的 Closeable 用 try-with-resources，框架托管资源遵循其生命周期。 |

JAVA-06 MAY。已固定 API 和字段语义的包内纯值类型可采用 record，验证调用方、序列化及持久化映射。例外须与模块邻近实现兼容。格式建议按需采用 P3C 和 Google Style，禁止借此全局格式化、改公共契约或安装工具。
