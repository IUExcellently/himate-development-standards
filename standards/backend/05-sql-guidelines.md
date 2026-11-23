# PostgreSQL SQL 与索引

适用 SQL、MyBatis XML/注解、Wrapper 查询及性能审查。对照 MyBatis 3.5 系列、PG 目标版本及 P3C，见 [E04](../../references/coding-evidence.md)。

- SQL-01 MUST。值经 JDBC PreparedStatement、MyBatis `#{value}` 或现有安全 Wrapper 绑定。SQL 标识符或排序方向由服务端固定映射。反例为 `${userSort}`、拼接请求字符串，或仅依赖前端校验。更新/删除核对访问范围、WHERE 条件与预期行数，维护任务的全表写入须明确授权。
- SQL-02 SHOULD。显式列、明确 NULL 与空值语义，避免类型隐转和索引列无意包函数。分页使用稳定 ORDER BY 和唯一后缀，例如 `created_at DESC, id DESC`；大 OFFSET 评估游标、稳定快照及一致性。排查 N+1、重复 DISTINCT、冗余排序/子查询、COUNT(*)、JOIN 基数、数据搬运与大结果内存峰值。全量投影或顺序扫描有数据证据时可接受。稳定游标需同时约定唯一排序后缀及空值位置。
- SQL-03 MUST。风险查询优先从 `EXPLAIN` 和隔离数据集着手。对获准可执行的查询再看 `EXPLAIN (ANALYZE, BUFFERS)`，对比估计/实际行数、loops、Seq/Index/Bitmap Scan、Nested Loop/Hash/Merge Join、sort、临时 I/O 和统计信息。ANALYZE 会执行语句，含副作用的查询和 DML 禁未经授权执行；回滚不能消除所有外部副作用。
- SQL-04 REVIEW。按真实过滤、排序、选择性、频次和更新开销评估主键/唯一、复合顺序、部分索引谓词、表达式索引、INCLUDE 与外键关联索引。核对已有索引覆盖、写放大、大小和执行计划。PG 外键引用端不会因此自动建索引；避免无差别建索引、限制 JOIN 数或要求每次命中索引。
- SQL-05 SHOULD。批量插入、更新、删除按参数量、锁、往返、内存、恢复和业务原子性决定分批。使用既有连接和批处理能力，避免循环逐条建连或无边界拉取。回填需明确进度、重跑和失败处理。DDL 按 [数据库结构](06-database-schema.md) 审查。
