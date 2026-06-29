# 生成任务状态 WebSocket 实时同步实施计划

## 范围

本轮只实现生成任务后台执行和 WebSocket 状态同步，不实现取消、暂停、重试、多进程队列或任务中断恢复。

## 前置阅读

- `AGENTS.md`
- `.trellis/spec/guides/index.md`
- `.trellis/spec/guides/cross-layer-thinking-guide.md`
- `.trellis/spec/backend/index.md`
- `.trellis/spec/backend/database-guidelines.md`
- `.trellis/spec/backend/error-handling.md`
- `.trellis/spec/backend/quality-guidelines.md`
- `.trellis/spec/frontend/index.md`
- `.trellis/spec/frontend/service-bridge-real-backend.md`

## 实施步骤

1. 后端增加任务事件广播管理器。
   - 在 `app/api/server.py` 中引入 `WebSocket`、`WebSocketDisconnect` 和必要并发工具。
   - 管理按 `projectId` 分组的连接集合。
   - 提供线程安全广播入口，将完整 `GenerationJob` 快照调度到 FastAPI 事件循环发送。

2. 后端新增 WebSocket 订阅端点。
   - 路径：`/api/projects/{project_id}/generation-jobs/ws`。
   - 连接后发送当前项目已有任务快照。
   - 断开时清理连接。

3. 后端改造生成任务创建。
   - 保留请求校验和任务创建逻辑。
   - 保存 `queued` 后广播。
   - 可执行阶段提交后台执行，并尽快返回当前任务快照。
   - 后台执行保存并广播 `running` 和最终 `done/failed`。
   - 未接入阶段保存“等待执行器接入”日志并广播，不启动后台线程。

4. 调整后端测试。
   - 更新现有生成任务测试，不再要求 `POST` 响应直接是最终状态。
   - 增加等待详情接口最终状态的辅助函数。
   - 增加 WebSocket 接收任务更新的 API 测试。
   - 覆盖失败路径：后台执行异常或执行器返回 failed 后能持久化并推送失败快照。

5. 前端扩展 service bridge。
   - 增加 WebSocket URL 推导。
   - 增加 `subscribeGenerationJobs(projectId, onJob)`，解析 `generationJobUpdated`。
   - 支持断线后有限重连；unsubscribe 后停止重连。
   - 不提供 mock 写入或 mock 实时事件。

6. 前端扩展 generation store。
   - 新增 `upsertJob`。
   - 新增订阅/取消订阅 action。
   - `createJob` 改为 upsert HTTP 返回快照，不假设任务已完成。

7. 前端接入生成任务页。
   - `onMounted` 加载项目、上下文和任务后建立订阅。
   - `onUnmounted` 取消订阅。
   - 收到已完成且影响章节/文件的阶段后刷新上下文，避免章节列表滞后。

8. 文档与项目记忆。
   - 如发现新的运行约定或接口路径，需要更新 `AGENTS.md`。
   - 如果新增重要后端/前端契约，也更新 `.trellis/spec/` 对应规范。

## 验证命令

```bash
python -m pytest tests/test_api_generation_jobs.py tests/test_api_batch_generation_jobs.py
python -m pytest tests
cd frontend && npm run typecheck
cd frontend && npm run build
```

## 回滚点

- 如果后台执行导致 API 测试大面积不稳定，先保留 WebSocket 端点和 store upsert，回退 `POST /api/generation-jobs` 同步执行语义。
- 如果 WebSocket 重连影响页面稳定性，先关闭自动重连，保留页面加载时 HTTP 列表兜底。

