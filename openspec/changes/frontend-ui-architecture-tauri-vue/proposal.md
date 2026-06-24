## Why

当前项目的 `customtkinter` GUI 已能支撑基础小说生成流程，但界面结构以 Tab 和回调函数为中心，难以承载后续项目管理、章节编辑、生成任务状态、知识库与配置中心等更复杂的工作台体验。

本变更先建立 Tauri + Vue 下一代前端 UI 架构，让新界面可以与现有 Python GUI 并行演进；本轮不修改后端服务、生成逻辑或现有 `python main.py` 入口。

## What Changes

- 新增 Tauri + Vue + TypeScript 前端工程骨架，用于承载下一代桌面 UI。
- 新增前端应用壳层、路由、页面目录、状态管理和 mock API 边界。
- 建立小说生成器的工作台式信息架构，包括项目页、工作台页、章节编辑页、生成任务页、配置页和知识库页。
- 定义前端侧核心数据类型，包括项目、章节、生成任务、模型配置等 UI 所需结构。
- 保留现有 `customtkinter` GUI 和后端生成逻辑，不做功能替换。
- 不接入真实后端服务；初期页面使用 mock 数据表达未来接口需求。

## Capabilities

### New Capabilities

- `tauri-vue-frontend-shell`: 定义 Tauri + Vue 下一代前端工程壳层、路由、布局、状态管理和 mock 数据边界。
- `novel-workbench-ui`: 定义小说工作台 UI 的页面结构、导航模型和核心工作区布局。

### Modified Capabilities

无。

## Impact

- 新增前端目录，例如 `frontend/`，包含 Vue、Vite、TypeScript、Tauri 配置与源文件。
- 新增 Node/Tauri 相关开发依赖和启动脚本；不影响现有 Python 依赖。
- 现有 `main.py`、`ui/`、`novel_generator/`、`config_manager.py` 保持行为不变。
- 后续后端服务化完成后，可将 mock API 替换为本地 FastAPI 或 Tauri command 调用。
