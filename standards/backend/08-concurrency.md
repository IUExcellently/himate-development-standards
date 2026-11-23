# 并发、线程池与异步

适用 Java ExecutorService、CompletableFuture、@Async、线程上下文、事件循环及异步回调，以 JDK 21 和 Spring 6.2 为准。证据 [E07](../../references/coding-evidence.md)。

- CON-01 MUST。按工作性质隔离线程池，明确并发上限、队列容量、拒绝语义和超时预算。池由容器或明确生命周期管理；避免逐请求建池或使用无保护无界队列。调用者执行策略须证明不会阻塞 Gateway 事件循环或扩大事务时长。
- CON-02 MUST。CompletableFuture 显式选择合适 executor、处理异常、超时和取消。@Async 经代理入口并显式传播所需的 MDC/身份副本，结束时清理；不要依赖请求 ThreadLocal 或把事务对象跨线程传递。异步执行前明确提交时序与丢失后的补偿。
- CON-03 SHOULD。共享变量使用不可变快照、原子操作、并发集合或窄锁；跨多个字段的不变量单独保护。核对任务中断、停止接受任务、排空/取消及资源释放。反例为在任务内吞掉 InterruptedException 或让异步失败无消费者。
- CON-04 REVIEW。Java 21 虚拟线程适用于测过的阻塞 I/O；保留 DB、外部服务、内存或文件配额并发上限，验证 JDK 21 pinning、上下文和实际吞吐。线程数、队列长度与限流均用工作负载测量。全局切换执行模型须另做兼容评审及范围确认。
