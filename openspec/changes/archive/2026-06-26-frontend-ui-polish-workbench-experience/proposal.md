## Why

前端已经完成真实本地后端接入，项目配置、章节文件、生成任务、知识库、角色库和 WebDAV 等能力可以通过 `serviceBridge` 使用。但当前页面仍主要按功能堆叠表单和操作区：设置页信息密度高，知识库页把知识文件、剧情要点和角色库混在同一视图，生成页的任务创建、批量参数、任务列表和日志缺少稳定操作面板，各页面也各自处理加载、错误、成功和确认状态。

现在需要在不改变业务契约的前提下，把前端从“功能已接入”推进到“可长期使用的写作工作台”：主流程更清晰，页面结构更稳定，常见 UI 片段可复用，状态反馈一致。

## What Changes

- 统一前端信息架构，让项目、工作台、章节、生成、知识库和设置之间形成更清楚的写作流程。
- 抽出通用 UI 组件，包括表单区、状态提示、操作栏、确认区、文件/章节列表和长文本编辑器。
- 重构设置页，将项目参数、LLM、Embedding、代理、阶段模型和 WebDAV 拆成配置分组或 tabs，降低单屏密度。
- 重构知识库页，用 tabs 区分知识文件、剧情要点和角色库，并保留现有真实后端操作入口。
- 重构生成页，把任务创建、批量参数、任务列表和日志组织成稳定的操作面板。
- 统一错误、成功、加载、空状态和确认状态的展示模式，减少页面各自实现的重复逻辑。

## Non-Goals

- 不重写真实后端接口，不改变 `app/api/server.py` 已有业务契约。
- 不改变 `serviceBridge` 对外的核心方法语义；必要调整只限于 UI 状态适配。
- 不引入大型 UI 框架，不替换 Vue 3、Pinia、Vite 或现有轻量样式方案。
- 不处理 Tauri 打包体验、自动启动本地 API 或安装器流程。
- 不删除旧 `customtkinter` GUI，不改变 `python main.py` 的生产入口地位。
- 不改变现有输出目录文件名、配置字段或生成任务阶段含义。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `novel-workbench-ui`: 扩展工作台信息架构、通用 UI 组件和页面状态模式要求。
- `frontend-project-config-management`: 扩展设置页配置分组或 tabs 的前端呈现要求。
- `frontend-generation-operations`: 扩展生成页稳定操作面板、批量参数和日志展示要求。
- `frontend-knowledge-role-webdav-tools`: 扩展知识库页 tabs 信息架构要求。
- `frontend-backend-service-bridge`: 扩展统一加载、成功、错误和确认反馈要求。

## Impact

- 主要影响 `frontend/src/components/`、`frontend/src/pages/`、`frontend/src/layouts/`、`frontend/src/styles/` 和少量 store 使用方式。
- 可能新增共享组件目录，例如 `components/ui/`、`components/workbench/` 或按现有约定命名的通用组件。
- 需要保持页面和 store 继续通过 `frontend/src/services/serviceBridge.ts` 访问真实后端。
- 验证重点为 `npm run typecheck`、`npm run build`，以及设置、知识库、生成、章节和工作台页面的基础交互检查。
