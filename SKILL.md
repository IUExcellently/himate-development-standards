---
name: himate-development-standards
description: 在已登记的 HiMate 工作树执行前端、Java、SQL、Python 调度器和 AG-UI 的开发、调试与审查时，按任务加载匹配规范。
---

# HiMate 开发规范

1. 以此文件所在目录为规范根。用本机 Python 3.10+ 执行该根下的 `scripts/detect_project.py --cwd <工作区>`，参数按当前 shell 安全传递，脚本位置不以工作区推断。入口已验证同一工作区时可复用结果。仅在 `active=true` 时继续。
2. 首次命中读取 [核心约束](standards/core.md) 和 [冲突裁决](standards/priority.md)。涉及新增、升级或替换依赖时加载 [依赖审批](standards/dependency-policy.md)。
3. 同一规范根下运行 `scripts/resolve_rules.py`。传入 `--cwd`、已知文件（重复 `--path`）、简短摘要（`--task`）或显式语义（重复 `--tag`）。用重复 `--loaded` 传入本会话已读规范的相对路径，包括前一步的核心规则。只读取返回的 `rules`，范围扩展后重新解析增量。包含敏感内容时用路径与标签。
4. 以真实仓库规则、现行接口契约、Trellis 专项索引和相关 Cairn 知识核对适用条件。证据不足时按需查阅 [代码证据](references/coding-evidence.md) 与 [官方规范](references/official-references.md)。实质冲突暂停受影响步骤并请求用户裁决。记录客户端实际读到的文件和执行结果。
