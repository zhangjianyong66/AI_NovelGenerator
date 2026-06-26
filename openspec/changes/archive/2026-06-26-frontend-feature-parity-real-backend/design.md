## Context

当前仓库同时存在两条 UI 线：稳定生产入口 `python main.py` 的 `customtkinter` GUI，以及 `frontend/` 中新建的 Tauri 2 + Vue 3 + TypeScript 工作台骨架。前端骨架已有路由、页面、Pinia store 和 `mockApi`，但不读取 `config.json`、不访问输出目录、不调用 `novel_generator/`、不操作向量库，也不能执行角色库或 WebDAV 流程。

项目已有架构重构计划指向“本地优先、服务化核心、可恢复工作流、结构化存储、可替换 UI”：`app/api/` 作为本地 FastAPI 边界，`app/services/` 承载应用服务，`app/workflows/` 承载生成流程，`app/repositories/` 承载 SQLite、文件和向量库访问。此前前端架构变更也明确把真实后端接入留作后续工作。本变更正是填补这段迁移空白。

## Goals / Non-Goals

**Goals:**

- 将前端页面从 mock 展示推进为可调用真实本地服务的桌面工作台。
- 建立前端 API 客户端与服务边界，集中处理后端地址、健康检查、错误、加载状态和 mock fallback。
- 补齐旧 GUI 中用户高频使用的核心能力：项目/输出路径、配置管理、章节文件编辑、生成任务、知识库导入、向量库清理、基础角色库和 WebDAV。
- 保持业务逻辑位于 Python 后端服务层，Vue 只负责 UI 状态、表单、展示和用户交互。
- 在迁移期间保持 `python main.py` 和现有 `customtkinter` GUI 可用。

**Non-Goals:**

- 不要求一次性删除旧 GUI 或让 Tauri 前端立即成为唯一入口。
- 不在 Vue 中重新实现小说生成、模型调用、向量库切分、WebDAV 协议或角色分析逻辑。
- 不强制一次性完成所有角色库高级功能；复杂分类、批量导入和 LLM 分析可在基础能力之后继续扩展。
- 不改变现有输出目录文件名和文件格式，先兼容 `Novel_setting.txt`、`Novel_directory.txt`、`chapter_X.txt` 等既有文件。
- 不提交用户本地配置、API Key、私有 Base URL、小说正文、向量库和备份文件。

## Decisions

### 使用本地后端服务作为真实能力边界

前端通过 `frontend/src/services/` 下的真实 API client 调用本地服务。优先复用架构重构计划中的 FastAPI 路线；若 Tauri command 更适合启动/探测本地进程，可以把 Tauri command 限定为“启动、健康检查、打开路径、选择文件”等桌面壳能力，不承载生成业务。

备选方案是 Vue 直接调用 Tauri Rust command，再由 Rust 调 Python 脚本。这个方案会让 Rust/Tauri 成为业务中转层，增加调试复杂度，也不利于现有 Python 测试复用。

### `mockApi` 降级为开发 fallback

页面和 store 不应继续直接依赖 `mockApi`。新增服务入口，例如 `apiClient` 或 `workspaceService`，由该入口根据运行模式选择真实本地 API 或 mock fallback。真实 API 不可用时，界面必须明确显示离线/mock 状态，避免用户误以为操作已写入真实项目。

备选方案是直接删除 mock。保留 fallback 更利于前端独立开发和 UI 回归，但必须在 UI 上明确标识，防止混淆。

### 先覆盖核心生成链路，再扩展外围工具

迁移优先级按用户价值排序：项目/配置和文件编辑是生成前置条件，生成任务是核心价值，知识库与向量库是生成质量支撑，角色库和 WebDAV 属于复杂外围工具。实现时应按 milestone 分批交付，每批都能独立验证。

备选方案是按旧 GUI Tab 逐页复刻。逐页复刻容易把旧回调式结构带入新前端，也会让“能看到页面”先于“能完成流程”，不利于真实替换。

### 前端编辑模型保留文件兼容性

章节和设定编辑在前端呈现为工作台文档，但后端必须继续读写旧输出目录文件：`Novel_setting.txt`、`Novel_directory.txt`、`global_summary.txt`、`character_state.txt`、`chapter_X.txt`、`outline_X.txt`、`plot_arcs.txt`。后续引入 SQLite 时，可把 SQLite 作为索引和状态来源，文本文件仍作为兼容导入/导出格式。

备选方案是立即切换到数据库为唯一事实来源。这样会影响用户已有目录和旧 GUI，迁移风险偏高。

### 生成任务使用可查询状态模型

前端发起生成操作后不应阻塞页面等待结果。后端返回任务 ID，前端通过轮询或事件订阅获取状态、进度、日志、错误和产物路径。第一阶段可使用轮询；若后续需要实时日志，可增加 SSE 或 WebSocket。

备选方案是同步 HTTP 请求等待生成完成。章节生成和批量生成可能耗时较长，同步请求会造成超时、不可取消和错误反馈差。

## Risks / Trade-offs

- 本地 API 与现有架构重构计划存在先后依赖 → 实现时先完成最小 API 和服务层，再接前端；不要让前端绕过服务层直接调用旧模块。
- 真实配置包含敏感信息 → API 响应默认脱敏 API Key 和密码，保存时只传用户显式修改的字段。
- 前端 mock fallback 可能误导用户 → 顶栏和操作结果必须展示后端连接状态，mock 模式禁止显示“已保存到真实项目”。
- 生成任务耗时长且可能失败 → 任务状态必须包含 running/succeeded/failed/cancelled/needs_review，并保留错误消息和日志。
- 文件和数据库并存可能产生一致性问题 → 初期以现有输出目录文件为兼容事实来源，数据库只做状态索引；需要明确同步时机。
- 角色库功能面很大 → 第一阶段只覆盖列表、查看、编辑、保存、导入入口和选择角色，复杂分类删除和 LLM 分析可分后续任务。

## Migration Plan

1. 建立本地后端最小 API 和前端 API client，包括健康检查、错误模型、运行模式和 mock fallback。
2. 接入项目/配置管理，支持加载和保存 `config.json` 中旧 GUI 已有的核心字段。
3. 接入文件编辑工作区，支持输出目录核心文本文件和章节文件的加载、保存、字数统计。
4. 接入生成任务，支持设定、目录、草稿、定稿、批量生成、一致性审校的任务创建、状态查询和日志展示。
5. 接入知识库、向量库、剧情要点、角色库基础能力和 WebDAV 常用能力。
6. 每阶段运行对应 Python 测试、前端 typecheck/build，并确认 `python main.py` 仍可启动。

Rollback 策略：保留 `customtkinter` GUI 作为生产入口；若前端真实接入出现问题，可切回 mock fallback 或禁用 Tauri 前端真实操作，不影响 `python main.py`。

## Open Questions

- 本地 API 进程由 Tauri 自动启动，还是由用户/开发者单独启动，需要在实现前确认桌面打包策略。
- API 鉴权是否需要本机 token 或随机端口绑定，取决于后续是否允许浏览器访问同一 API。
- 角色库高级能力是否纳入本变更后半段，还是拆成独立 `frontend-role-library-parity` 变更。
- 生成任务实时日志采用轮询、SSE 还是 WebSocket，可在最小轮询可用后再决策。
