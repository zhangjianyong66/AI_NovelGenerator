## Context

当前应用是 Python `customtkinter` 桌面 GUI，主入口为 `main.py`，界面拆分在 `ui/` 目录下。现有 GUI 以 Tab、控件变量和回调函数组织，生成逻辑仍直接调用 `novel_generator/`、`config_manager.py` 和文件工具函数。

本变更的重点不是后端服务化，而是为下一代桌面 UI 建立并行的前端技术架构。新前端初期只提供工程骨架、页面结构、状态管理和 mock API，现有 Python GUI 继续作为稳定入口。

## Goals / Non-Goals

**Goals:**

- 建立 Tauri + Vue + TypeScript + Vite 前端工程骨架。
- 建立可扩展的前端目录结构，包括路由、布局、页面、组件、状态、服务和类型定义。
- 建立小说生成器工作台式 UI 信息架构，支持后续逐步迁移项目、章节、生成、配置、知识库等功能。
- 使用 mock API 表达前端所需数据形状，避免本轮修改 Python 后端。
- 保持现有 `python main.py`、`customtkinter` GUI 和生成逻辑行为不变。

**Non-Goals:**

- 不迁移真实生成流程。
- 不修改 `novel_generator/`、`config_manager.py` 或现有 Python GUI 功能逻辑。
- 不引入 SQLite、工作流状态机或后端服务层。
- 不要求 Tauri + Vue 前端替代当前 `customtkinter` GUI。
- 不接入真实 FastAPI、本地服务或 Tauri command。

## Decisions

### 使用 `frontend/` 作为新前端根目录

新前端放在项目根目录的 `frontend/` 下，与现有 Python 代码并行。这样可以避免打乱当前桌面应用入口，也便于后续独立运行、打包和测试。

备选方案是把新前端放入 `ui_next/` 或 `apps/desktop/`。`frontend/` 更直观，且与 Python `ui/` 目录区分清晰。

### 使用 Tauri + Vue + TypeScript + Vite

Tauri 提供轻量桌面壳，Vue 适合表单和工作台型应用，TypeScript 用于稳定前端数据契约，Vite 用于开发体验和构建速度。

备选方案包括 Electron + React 或继续扩展 `customtkinter`。Electron 资源占用更高；继续扩展 `customtkinter` 难以承载复杂编辑器和任务面板体验。

### 前端初期使用 mock API

本轮只调整前端 UI 架构，不修改后端服务。前端通过 `services/mockApi.ts` 和 `services/types.ts` 表达未来接口需求，页面和 store 使用 mock 数据跑通布局与交互。

备选方案是直接接入现有 Python 函数或启动本地 HTTP API。直接接 Python 会让新前端过早绑定旧实现；本地 HTTP API 需要先完成后端服务化，超出本变更范围。

### 工作台布局优先于 Tab 复刻

新 UI 不照搬当前 `customtkinter` Tab 结构，而采用工作台布局：左侧导航、中央编辑/查看区域、右侧上下文面板、底部或侧栏日志任务区。

备选方案是逐个复刻旧 Tab。复刻迁移成本低，但会保留旧信息架构的问题，难以体现项目、章节、任务之间的关系。

### 业务逻辑不得进入前端

前端可以定义 UI 状态、mock 数据和展示逻辑，但不得实现小说生成、配置持久化、向量库操作或模型调用逻辑。后续真实接入时，业务逻辑仍应位于 Python 后端服务层。

## Risks / Trade-offs

- 新前端与旧 GUI 并行会短期增加目录和工具链复杂度 → 通过明确启动命令和文档边界降低混淆。
- mock API 可能与未来真实 API 不一致 → 在类型定义中只表达 UI 必需字段，并在后端服务化时把 mock 类型作为接口讨论输入。
- Tauri 开发环境依赖 Node、Rust 和系统 WebView → 在任务中加入环境检查和 README 说明。
- 前端架构先行可能产生不可用的空壳 → 每个页面至少使用 mock 数据展示关键区域，保证架构可运行、可评审。

## Migration Plan

1. 新增 `frontend/` 工程，不修改现有 Python GUI。
2. 建立路由、应用壳层、页面骨架、状态管理和 mock API。
3. 让新前端可以独立以开发模式启动。
4. 在项目说明中记录新旧 GUI 并行关系和启动方式。
5. 后续后端服务化完成后，再将 mock API 替换为真实本地 API 或 Tauri command。

Rollback 策略：删除或忽略 `frontend/` 目录即可，不影响 `python main.py`。

## Open Questions

- 最终真实接入方式使用本地 FastAPI，还是 Tauri command 调用 Python 后端进程，需要在后端服务化设计阶段确定。
- 是否引入组件库，如 Naive UI、Element Plus 或自研轻量组件，需要在 UI 视觉方向确认后决定。
- 编辑器是否需要 Markdown、富文本或纯文本增强能力，后续章节编辑器迁移时再定。
