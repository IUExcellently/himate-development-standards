# 前端开发

- FE-01 MUST。确认命中文件所属 app。PC/mobile 使用 React 19、Vite 8、React Router 7、Tailwind 4 与 UI Kit。Admin 使用 React 19、Vite 6、Router 6、Semi 和自己的 Axios 封装。以对应 `package.json` 和 `pnpm-lock.yaml` 解析为准。检查 `.trellis/spec/frontend/index.md` 及相关细则。
- FE-02 SHOULD。PC/mobile 保留 app 层路由、交互和容器差异。跨端纯逻辑先查 `frontend/packages` 的 API client、chat transport、协议、流式呈现及表单核心。按已有包边界提供共享类型，避免 app 直接互相引用。组件遵循现有 PascalCase/本地文件命名，组合逻辑复用现有 hook。
- FE-03 MUST。API 调用用当前端请求包装保留鉴权、超时、取消、错误映射和缓存键。PC/mobile 请求入口各自为 `src/utils/request.ts`，Admin 为 `src/api/request.ts`。对未验证外部值做收窄，明确缺省/空值与大整数 ID 的 wire 类型。状态使用现有 Zustand store 和稳定 selector，避免从 render 写 store、复制派生状态或丢失并发更新。核对请求竞态、loading/error/empty 与卸载后的清理。
- FE-04 SHOULD。沿用现有 i18n key 与中英文资源。交互用语义元素与可辨识标签，检查键盘焦点、键盘关闭弹层、触控和 reduced motion。性能变化用实际 bundle、订阅频率或长列表测量验证。保留已有移动端 WebView、断点和大字体退化处理。
- FE-05 SHOULD。按 app 运行已存在的 typecheck、lint、Vitest 或源码契约/外部浏览器验证。使用现有测试能力核对 UI Block、取消、重复事件和错误边界。运行脚本前检查写入范围。
