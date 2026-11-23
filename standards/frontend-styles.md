# 前端样式

- CSS-01 MUST。跨页面重用的主题 token 归现有 UI Kit `theme.css`，PC/mobile 各用 `src/styles/globals.css` 处理应用级基础样式，Admin 用 `src/styles/global.css` 和 Semi 主题接口。共享样式先证实所有使用方需要，避免新增全局入口、静默改 reset、随意覆盖第三方内部结构及将 Admin token 套进聊天端。
- CSS-02 SHOULD。局部变化优先组件 props、现有 token 或 Tailwind class。复杂覆盖在组件共址的独立 CSS、已有 CSS Modules 或框架提供的局部作用域下编写，按文件邻居命名并由组件 import。仅在当前工具链已有 Less 时选择 Less。使用组件根类或弹层提供的容器类限定作用域。示例 `.registry-editor .editor-footer`，反例全局 `.semi-modal-footer`。Portal 需显式核对挂载点、作用域及 z-index。
- CSS-03 REVIEW。用低 specificity 和现有 cascade/layer；`!important` 仅在确认第三方边界无可用 token/prop 且普通选择器无法覆盖时局部使用，记录原因与作用域。核对亮暗、焦点、移动端 viewport/safe-area、可滚动区域、动效偏好及相邻页面。
- CSS-04 MUST。保留现有全局根节点、移动端宿主和滚动契约。涉及共享规则时按仓库授权与回归要求检查 PC/mobile/Admin 对应引用，避免把局部样式扩大影响。
