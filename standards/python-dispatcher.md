# Python 调度器

- PY-01 MUST。遵循 `.importlinter` 的依赖方向及 `app.bootstrap.container` 例外。按 `pyproject.toml` 的 Ruff py312、100 列及启用规则和 PEP 8 写新代码。公共边界保留明确类型、Pydantic schema 与序列化语义，局部适配第三方时收敛 `Any`。配置经 bootstrap 校验，环境覆盖及密钥按现有设施注入。
- PY-02 MUST。异步入口使用现有 HTTP 池和 lifespan，外部 I/O 有 deadline，避免事件循环阻塞。背压槽、HTTP 流和取消中的工具配对在 `finally` 清理，传播取消并追踪后台任务。保持 `app/api/routes/dispatch.py` 的饱和错误契约与释放时机，禁止用宽捕获吞掉取消或错误。
- PY-03 MUST。LangGraph 状态迁移核对 `thread_id`、checkpoint namespace、reducer 和旧检查点恢复。路由、澄清、Adapter 调用、停止与重入是独立边界；按现有 tool schema 和允许清单校验身份、参数和副作用，取消/重试可重复安全执行。按固定版本及现有 `builder.py`、`state.py` 和测试确认 DeepAgents 钩子，涉及远程工具或高影响动作时遵循鉴权和授权。
- PY-04 SHOULD。重用 `app/core` 统一日志、异常、masking、指标和 ContextVar；确保任务结束重置上下文，保留错误类型和 cause。避免记录模型提示、完整用户消息与工具敏感返回。会话 checkpoint 按现有所有权、加密、TTL、清理策略评审。
- PY-05 SHOULD。用已有 pytest、pytest-asyncio、hypothesis 和 import-linter。以干净本地 fake 或获准的隔离环境测取消、重入、故障、序列化、路由与流式回归。具体 SLA 和工具配置读现行 Trellis 与源码。
