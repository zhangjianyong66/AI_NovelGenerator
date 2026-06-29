# 生成任务状态 WebSocket 实时同步

## Goal

让前端生成任务状态保持实时更新：任务创建后无需刷新页面，任务状态、进度、日志、错误和完成结果能在后端状态变化时立即同步到任务列表、任务详情和全局项目状态栏。

用户价值：长时间生成章节、批量生成或审校时，用户可以停留在当前页面观察真实执行状态，不需要手动刷新或重新进入页面确认任务是否完成。

## Confirmed Facts

- 本地 API 位于 `app/api/server.py`。
- 当前生成任务创建接口为 `POST /api/generation-jobs`，列表接口为 `GET /api/projects/{project_id}/jobs`，详情接口为 `GET /api/generation-jobs/{job_id}`。
- `app/api/server.py:1153` 的 `create_generation_job` 会先保存 `queued` 任务，再把已接入阶段置为 `running`，随后在同一个 HTTP 请求中同步调用 `run_generation_job(...)`，最后保存并返回 `done` 或 `failed`。
- 前端生成任务状态集中在 `frontend/src/stores/generation.ts`，当前只有 `loadJobs(projectId)` 和 `createJob(request)` 两个状态入口。
- 前端真实 API 访问统一经过 `frontend/src/services/serviceBridge.ts`，写操作不能降级写入 mock。
- `frontend/src/pages/GenerationPage.vue` 在页面加载时拉取任务列表，创建任务后把 HTTP 返回的任务写入 store；没有轮询或 WebSocket 订阅。
- 全局项目状态栏通过 `AppLayout.vue` 读取同一个 `generationStore`，因此 store 收到实时更新后可同步影响生成页和全局状态栏。
- 前端类型中任务状态已有 `queued | running | paused | done | failed`，任务数据结构已有 `id/projectId/title/stage/status/progress/startedAt/log/error`，不需要为了首版实时同步新增展示字段。
- 项目使用 FastAPI 0.128 和 uvicorn 0.38，后端具备原生 WebSocket 支持基础。

## Requirements

- R1：后端提供生成任务状态 WebSocket 订阅端点，前端可按当前项目订阅任务更新。
- R2：后端在任务进入 `queued`、`running`、最终 `done` / `failed` 时广播完整任务快照，避免前端拼接局部补丁造成状态不一致。
- R3：`POST /api/generation-jobs` 改为创建任务后尽快返回持久化任务快照，真实生成在后端后台执行；旧 HTTP 接口路径和响应结构保持兼容。
- R4：前端通过 `serviceBridge` 或其下属服务边界建立 WebSocket 连接，页面和 store 不直接绕过统一后端边界调用 mock。
- R5：前端收到任务更新后按 `job.id` upsert 到 `generationStore.jobs`，保持最新任务靠前，并保留当前选中任务。
- R6：WebSocket 断开时前端不能破坏现有 HTTP 读写能力；应允许重新连接，并至少能回退到现有 HTTP 加载任务列表。
- R7：非真实后端模式下不应尝试执行写操作；WebSocket 不应让 mock 模式产生伪实时写入。
- R8：任务完成后，如果任务阶段会改变章节或核心项目文件，前端应沿用现有刷新上下文机制，确保章节列表/工作台读取到最新落盘内容。
- R9：后台执行只覆盖当前已接入真实执行器的生成阶段；未接入阶段保持可创建但不启动真实执行器，状态语义不得误导用户。
- R10：任务状态持久化仍以 `.local/state.sqlite3` 为事实来源，WebSocket 只推送已保存或即将保存的完整任务快照。

## Acceptance Criteria

- [x] 打开生成任务页并连接本地后端后，前端建立当前项目的任务状态 WebSocket 订阅。
- [x] 创建生成任务后，HTTP 响应尽快返回 `queued` 或 `running` 任务，任务列表和任务详情无需刷新页面即可显示后续状态、进度、日志和错误。
- [x] 后端任务最终保存为 `done` 或 `failed` 时，前端能通过 WebSocket 更新同一条任务记录，而不是新增重复记录。
- [x] 任务创建请求返回后，即使用户停留在生成页或只看全局状态栏，也能在后端完成时看到最新状态。
- [x] WebSocket 断开或后端重启后，前端不崩溃；恢复连接或手动/页面触发 `loadJobs` 后能拿到持久化任务状态。
- [x] 现有 HTTP 生成任务创建、列表、详情接口保持兼容，旧调用方不需要改动即可继续工作。
- [x] 后端单元/API 测试覆盖后台任务创建后立即返回、后台完成后持久化为 `done`/`failed`，以及 WebSocket 能收到任务快照。
- [x] `.venv/bin/python -m pytest tests` 通过。
- [x] `cd frontend && npm run typecheck` 通过。
- [x] `cd frontend && npm run build` 通过。

## Out of Scope

- 不新增远程多人协作或跨机器消息队列。
- 不引入 Redis、Celery 等外部任务系统。
- 不改变旧 GUI `python main.py` 的运行路径。
- 不实现任务取消、暂停、重试等新控制能力。

## Notes

- 已确认采用后台执行：`POST /api/generation-jobs` 创建任务后尽快返回，前端通过 WebSocket 获得 `running` 和最终 `done` / `failed`。
- 首版不追求多进程共享广播；如果生产部署改为多 worker，需要后续引入跨进程消息通道或强制单 worker。
