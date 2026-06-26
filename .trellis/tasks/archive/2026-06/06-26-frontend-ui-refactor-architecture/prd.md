# 前端 UI 重构技术架构规划

## Goal

为 AI Novel Generator 的下一代前端 UI 重构制定可执行的技术架构方案，明确重构边界、推荐技术栈、页面/组件分层、状态与服务接入策略、设计系统方向、验收标准和后续实施拆分。

本阶段只做规划和方案收敛，不直接修改前端业务代码。

## Confirmed Facts

- 当前前端工程位于 `frontend/`，是与现有 Python `customtkinter` GUI 并行演进的 Tauri 2 + Vue 3 + TypeScript + Vite 工程。
- 当前依赖包含 `vue`、`vue-router`、`pinia`、`@tauri-apps/api`、`@lucide/vue`，尚未引入第三方组件库、CSS 框架或设计系统工具链。
- 当前前端已有主布局 `frontend/src/layouts/AppLayout.vue`，页面包括项目、工作台、章节编辑、生成任务、知识库、设置。
- 当前已有通用 UI 组件目录 `frontend/src/components/ui/`，包括页面标题、操作栏、状态提示、表单分组、Tabs、长文本编辑和确认面板。
- 当前真实/Mock 服务访问通过 `frontend/src/services/serviceBridge.ts` 统一进入；项目文档说明真实 API 默认是 `http://127.0.0.1:8000`。
- 当前全局样式集中在 `frontend/src/styles/global.css`，已定义基础色彩、字体、按钮、面板、tabs、状态提示等样式 token 和通用类。
- 当前 `frontend/README.md` 的“只使用 mock 数据”说明已落后于代码和项目说明，后续文档更新应纳入计划。
- 项目根 `AGENTS.md` 要求前端新增页面优先复用 `frontend/src/components/ui/` 组件，并按写作流程组织主导航：项目 → 工作台 → 章节编辑 → 生成任务 → 知识库 → 设置。

## Requirements

- 推荐方案必须尊重现有 Tauri 2 + Vue 3 + TypeScript + Vite 基础，不在没有充分收益的情况下推倒重来。
- UI 重构采用保守增强路线：保留现有 Vue/Tauri 架构，不引入大型第三方 UI 组件库，优先建设项目内轻量设计系统和业务组件层。
- UI 重构以写作工作台优先：先围绕核心创作闭环打磨工作台的信息架构、业务组件和交互，再将沉淀出的组件与样式推广到其他页面。
- 工作台主体验采用章节编辑器中心：中间区域优先服务章节正文/项目文件编辑，生成任务作为辅助轨道而非主界面中心。
- 第一阶段编辑器内核继续使用增强版 `textarea`，通过 `WritingEditor` 适配层封装能力与事件，暂不引入 TipTap、ProseMirror 或 Monaco，并为后续替换底层编辑器预留边界。
- 前端源码采用轻量 feature 分层：在保留 `components/ui/`、`layouts/`、`services/`、`router/`、`styles/` 等全局基础目录的同时，逐步引入 `features/writing/`、`features/generation/`、`features/knowledge/` 等业务模块目录。
- 第一阶段状态管理继续使用 Pinia + `serviceBridge`，不引入 Vue Query / TanStack Query；需要规范化 store 内的 async state、错误状态、加载状态和保存状态。
- 第一阶段轻量设计系统只覆盖基础组件和样式 token，不做完整可配置主题系统；重点补齐按钮、图标按钮、字段、选择器、开关、分栏、工具栏、空状态、加载状态和保存状态。
- 响应式目标是桌面优先，并支持窗口缩窄到约 900px 时可用降级；不做手机端完整创作体验。当前 Tauri `minWidth` 为 1080px，后续设计应评估是否调整到降级目标附近。
- 实施拆分按架构层先后推进，并以工作台作为首个落地页面；先沉淀 token、基础 UI、feature 边界和 `WritingEditor`，再重构工作台，最后推广到其他页面。
- 推荐方案必须支持桌面应用体验，重点优化复杂写作工作流、长文本编辑、生成任务状态、知识库和设置表单，而不是做营销型页面。
- 推荐方案必须明确 UI 分层：应用壳层、页面、业务组件、通用 UI 组件、样式 token、服务接入与状态管理。
- 推荐方案必须明确是否引入第三方 UI 组件库、CSS 框架、图标/动效/虚拟滚动等依赖，并说明收益与代价。
- 推荐方案必须能按 milestone 分阶段实施，每个 milestone 可独立验证、独立提交、可恢复执行。
- 推荐方案必须保留真实 API 与 Mock fallback 的服务桥边界，页面和 store 不应直接耦合 mock 实现。

## Acceptance Criteria

- [ ] 明确前端 UI 重构的目标用户体验和非目标。
- [ ] 明确推荐技术架构，并给出不推荐选项及理由。
- [ ] 明确组件、样式、状态、路由、服务接入的边界和目录约定。
- [ ] 明确至少 2-4 个可独立实施的 milestone。
- [ ] 明确每个 milestone 的验证方式，例如 `npm run typecheck`、`npm run build`、关键页面手动验收。
- [ ] 形成 `design.md` 和 `implement.md`，并在进入实现前由用户确认。

## Decisions

- UI 重构路线选择“保守增强现有 Vue/Tauri 架构”，不引入大型第三方 UI 组件库。
- UI 重构主线选择“写作工作台优先”，再推广到其他页面。
- 工作台主体验选择“章节编辑器中心”，生成流水线作为辅助轨道。
- 第一阶段继续使用增强版 `textarea`，通过 `WritingEditor` 适配层预留后续编辑器内核替换能力。
- 代码组织采用轻量 feature 分层，同时保留现有全局基础目录。
- 第一阶段继续使用 Pinia + `serviceBridge`，不引入 Vue Query，但要规范化 async state 模式。
- 轻量设计系统第一阶段只做基础组件和样式 token，不做完整主题系统。
- 响应策略选择桌面优先，约 900px 可用降级，不做手机端完整体验。
- 实施拆分选择按架构层先后推进，并以工作台作为首个落地页面。

## Open Questions

- 无阻塞性开放问题。进入实现前需要用户确认 `prd.md`、`design.md` 和 `implement.md`，并指定本轮执行的 milestone。
