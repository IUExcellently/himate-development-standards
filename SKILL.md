---
name: himate-development-standards
description: 为登记的 HiMate 工作树按任务选择前端、Java、SQL、Python 调度器和跨端契约规范。用于该工作树的设计、开发、故障分析与审查。
---

# HiMate 开发规范

1. 若本轮入口尚未校验工作目录，从当前工作目录运行 `python3 -B /Users/yanzu/Documents/ai-skills/himate-development-standards/scripts/detect_project.py --cwd "$PWD"`。仅在 `active=true` 时继续。识别失败或命令不可用时，保持当前平台和工作区的工作流。不要为识别扫描其他仓库，也不要改权限。
2. 首次命中时读取 `standards/core.md` 和 `standards/priority.md`。以本目录为基准解析后续路径。
3. 运行 `python3 -B /Users/yanzu/Documents/ai-skills/himate-development-standards/scripts/resolve_rules.py --cwd "$PWD" --loaded standards/core.md --loaded standards/priority.md`，传入任务摘要（`--task`）、已知/拟改文件（重复 `--path`）和可准确判定的语义标签（重复 `--tag`）。若摘要可能含敏感信息，改用本地文件路径与标签。只读返回的规则，按规范顺序应用。路径未定时先按任务分类，定位后重新路由。以返回的相对路径作为会话去重键，使用 `--loaded` 传递已读路径。未解析到领域时，补充真实路径或标签再继续。
4. 变更范围扩展时补读新增规则，并按现行仓库契约、Trellis 专项索引及相关 Cairn L2/L3 核对。加载建议和实际读取须分别记录。依赖或跨端契约涉及权限时，先处理授权和兼容性。
5. 实质冲突按 `standards/priority.md` 给出证据与选项。保留用户裁决及未决影响范围，不改变平台真实指令优先级。

运维入口见 [README](README.md)。运行时只加载此页和路由命中的正文，证据与来源按需查阅。
