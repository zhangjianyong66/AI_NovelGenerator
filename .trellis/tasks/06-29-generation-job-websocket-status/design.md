# 生成任务状态 WebSocket 实时同步设计

## 目标

生成任务创建后立即在前端显示任务记录和运行状态；后端后台执行真实生成器，并在任务状态变化时通过 WebSocket 推送完整任务快照。任务持久化仍使用现有 SQLite 状态库，HTTP 查询接口继续作为恢复和兜底路径。

## 方案取舍

推荐方案：单进程内后台线程执行 + FastAPI WebSocket 广播。

- 优点：不引入 Redis、Celery 或额外服务，符合当前本地桌面/本地 API 架构；实现范围可控；HTTP 列表/详情接口仍能从 SQLite 恢复状态。
- 代价：广播连接只在当前 uvicorn 进程内有效，多 worker 或多进程部署无法共享实时事件。当前项目本地开发脚本和 Tauri 使用单本地后端，接受该限制。

备选方案 1：前端轮询 `GET /api/projects/{project_id}/jobs`。

- 优点：后端改动少。
- 缺点：不满足用户明确要求的 WebSocket；实时性和资源消耗不可控。

备选方案 2：引入外部队列/消息总线。

- 优点：更适合多进程和可恢复后台任务。
- 缺点：显著扩大部署复杂度，偏离当前本地应用需求，首版不采用。

## 后端边界

### 任务执行

在 `app/api/server.py` 中将 `create_generation_job` 拆成两段：

1. 请求校验、任务对象创建、保存 `queued`。
2. 对已接入真实执行器的阶段，提交后台执行函数；HTTP 立即返回当前任务快照。

后台执行函数负责：

- 将任务更新为 `running/progress=5`，保存并广播。
- 调用 `run_generation_job(...)`。
- 将结果更新为 `done` 或 `failed`，保存并广播。
- 捕获未预期异常，写入 `failed/progress=100/error/log`，保存并广播。

未接入真实执行器的阶段不提交后台执行，保留“等待执行器接入”日志并广播保存后的快照。

### WebSocket 合约

新增端点：

```http
WS /api/projects/{project_id}/generation-jobs/ws
```

连接建立后：

- 后端接受连接，并可立即发送当前项目任务列表中的最新快照，降低“先创建后订阅”或重连时漏事件的风险。
- 后续仅向同一 `project_id` 的连接广播任务更新。
- 消息格式为 JSON：

```json
{
  "type": "generationJobUpdated",
  "job": {
    "id": "job-...",
    "projectId": "current",
    "title": "生成章节草稿",
    "stage": "draft",
    "status": "running",
    "progress": 5,
    "startedAt": "2026-06-29 12:00:00",
    "log": ["..."],
    "error": null
  }
}
```

首版只定义 `generationJobUpdated`，不新增心跳消息；断线恢复由前端重连和 HTTP `loadJobs` 兜底处理。

### 并发与线程模型

- 使用 `ThreadPoolExecutor` 或 `threading.Thread` 执行阻塞的旧生成函数，避免阻塞 HTTP 响应。
- SQLite 每次保存仍通过 `GenerationJobStore.save_job(...)` 新建连接，适合线程内调用。
- WebSocket 发送运行在事件循环中；后台线程不能直接 `await`，需要通过线程安全方式把广播调度回应用事件循环。
- `app.state` 可保存广播管理器、后台执行器和主事件循环引用，保持 `create_app(...)` 测试实例隔离。

## 前端边界

### Service Bridge

在 `frontend/src/services/serviceBridge.ts` 或邻近服务文件中增加 WebSocket URL 构造和订阅方法：

```ts
subscribeGenerationJobs(projectId: string, onJob: (job: GenerationJob) => void): () => void
```

要求：

- 基于 `VITE_API_BASE_URL` 推导 `ws://` 或 `wss://`。
- 只负责连接、解析消息、重连和关闭，不写 mock 数据。
- 返回 unsubscribe 函数，页面卸载或项目切换时关闭连接。

### Store

`frontend/src/stores/generation.ts` 增加：

- `upsertJob(job: GenerationJob)`：按 `id` 合并任务，最新任务靠前。
- `subscribeToJobUpdates(projectId: string)`：调用 service bridge 订阅，并在收到 job 时更新 store。
- `unsubscribeFromJobUpdates()`：关闭旧连接，避免项目切换或页面重复挂载造成多连接。

创建任务后不再假设 HTTP 返回最终状态，只把返回快照 upsert；后续状态由 WebSocket 更新。

### 页面

`GenerationPage.vue` 在加载当前项目任务后启动订阅，页面卸载时取消订阅。收到 `done/failed` 且阶段属于现有 `refreshChapterStages` 时，触发 `loadGenerationContext()` 刷新章节/项目文件上下文。为避免重复刷新，可记录已处理完成态的 job id。

全局 `AppLayout.vue` 读取同一个 store，因此不需要单独实现 WebSocket。

## 兼容与恢复

- HTTP API 路径、请求体和响应模型不变；差异是可执行阶段的创建响应可能是 `queued` 或 `running`，不是最终 `done/failed`。
- 刷新页面、WebSocket 重连或后端重启后，前端通过现有 `loadJobs(projectId)` 从 SQLite 获取最终状态。
- 后端重启不会恢复正在执行的内存线程；已持久化为 `running` 的任务恢复策略首版不处理，后续可增加启动时标记为 `failed` 或 `interrupted`。当前任务不引入新状态。

## 风险

- 旧测试可能断言 `POST /api/generation-jobs` 立即返回 `done`，需要调整为等待后台完成后再通过详情或列表断言最终状态。
- WebSocket 测试需要确保后台假执行器足够快，避免时序不稳定。
- 如果生成函数长时间阻塞，后台线程数量需要限制，避免连续点击创建大量任务。首版可设置较小 `max_workers`，不实现队列可视化。

