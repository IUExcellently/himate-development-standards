# Squad 继承与交接

官方 Squad 由一个 Lead 和成员组成。任务先唤起 Lead。Squad Instructions 和成员描述给 Lead 作分发上下文，成员 Agent 各自运行，角色描述不授予工具或项目权限。单 Agent 可直接承担工作，现有 Squad 可复用原有角色。可选四步为 Lead 规划 → Engineer 实施 → Reviewer 独立审查 → 用户验收。实际派发和状态始终遵守 Multica 的运行协议。

Lead 经官方分配或结构化 @mention 交接任务；普通文本中的名字不触发 Agent。只在获准的 Issue、子任务或评论中留下必要信息。避免复制规范全文和记录凭证、直接路径或未脱敏日志。

| 交接对象 | 要传递的可复核信息 |
|---|---|
| Lead → Engineer | Issue、受审 Skill 版本与提交/哈希、Scope、验收标准、路由建议、授权范围和待用户裁决项。 |
| Engineer → Reviewer | 最终范围、实际 diff 与测试结果、接口/依赖变化、使用过的规则路径与用户授权证据。 |
| Reviewer → Lead/用户 | 独立路由、问题位置与证据、待决问题、测试缺口和是否具备验收条件。 |

每个 Agent 新会话独立执行项目和版本检查。会话内按规则路径去重，换 Runtime、工作树、Skill 版本或新 Agent 时复核。Lead、Engineer 和 Reviewer 都不代替用户审批。若当前 Issue 支持受阻状态，按用户已授权的流程报告阻塞和决策请求。向用户提出依赖或冲突申请时说明影响范围，未决只暂停相关步骤。官方行为见 [Squads](https://multica.ai/docs/squads) 和 [Issues](https://multica.ai/docs/issues)。
