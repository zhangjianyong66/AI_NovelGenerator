# 工作台布局折叠优化实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: 本轮由 Codex inline 执行，不使用 subagent。步骤使用 checkbox 记录。

**Goal:** 优化工作台页面布局，支持全局左侧主导航与右侧项目状态栏折叠，并消除工作台横向滚动。

**Architecture:** 全局布局折叠状态放在 `AppLayout.vue`，通过 `localStorage` 持久化；工作台内部布局继续由 `WorkbenchLayout` 和全局 CSS 控制，窄宽度下右侧工作台栏下移，编辑区优先。

**Tech Stack:** Vue 3、TypeScript、Vite、CSS Grid、localStorage、lucide-vue。

---

- [x] 修改 `frontend/src/layouts/AppLayout.vue`，增加左右栏折叠状态、顶部图标按钮、持久化和响应式布局类。
- [x] 修改 `frontend/src/styles/global.css` 与 `frontend/src/pages/WorkspacePage.vue`，压缩工作台栏宽、避免内容溢出、提升编辑区优先级。
- [x] 运行 `npm run typecheck`。
- [x] 启动前端并用浏览器检查 `/workspace`，确认截图宽度下无横向滚动条，折叠按钮可用。
