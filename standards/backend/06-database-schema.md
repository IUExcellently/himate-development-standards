# PostgreSQL 结构与迁移

适用 schema、约束、DDL 与回填。根 README 指定基线 `backend/sql/baseline-all-20260831.sql` 和后续 `backend/sql/migration/`。具体项目约定读取 Cairn 的 `L3-guide-backend-sql-migration.md`，见 [E05](../../references/coding-evidence.md)。

- DB-01 MUST。沿用目标服务 schema、表命名及键类型。依据领域语义设计 NOT NULL、DEFAULT、UNIQUE、FK、CHECK、枚举/状态、长度和精度。关键完整性与业务幂等使用数据库约束或等价持久保证；应用校验保留友好拒绝。显式处理未知默认值，避免用空值或任意数字掩盖缺数据。
- DB-02 REVIEW。按访问形态选择主键与时间类型，明确 instant、业务当地时间和精度。JSONB 用于确有可变结构、可验证和可查询的负载，核心字段用可约束列。大字段考虑读写成本和外置策略。跨 schema 外键与其他服务数据依赖先评审所有权和发布兼容。
- DB-03 MUST。新增迁移遵循当期 Cairn 命名、schema 限定/`search_path`、幂等策略与回滚注释；不重写已发布迁移。脚本说明部署顺序、数据回填、锁影响、失败修复和不可逆步骤。幂等分支核对实际结构，避免 `IF NOT EXISTS` 掩盖已有错误定义。生产 DDL 须明确授权。
- DB-04 REVIEW。大表变更评审锁级别、耗时、读写兼容与回填数据量。考虑 expand → 回填 → 切换 → 收缩、`NOT VALID` 后分段验证及并发建索引。PG `CREATE INDEX CONCURRENTLY` 必须在事务块外，先核对运行器并与当前项目迁移模板协调。存在实质冲突时按优先级请用户裁决。
- DB-05 SHOULD。在目标 PG 主版本的隔离实例用独立数据检查上线顺序、重复执行、错误路径、约束和回退；记录可能的 invalid index 和修复流程。验收报告中的 PG 18 是测试证据，README 14+ 是兼容声明，部署主版本须另查。
