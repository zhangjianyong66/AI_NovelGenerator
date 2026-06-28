# 前端任务持久化与可恢复工作流

## Goal

继续把新 Tauri/Vue 前端从“能触发核心生成流程”推进到“真实创作时更可恢复、更可信”的本地工具。上一轮已完成设定/目录生成和单章草稿/定稿真实执行，本轮聚焦任务持久化与最小可恢复工作流：后端重启后仍能查看生成任务历史、日志、输入参数和失败原因。

用户价值：用户在前端进行真实创作时，遇到服务重启、任务失败、章节不存在、知识导入后无法检索等情况，不再只看到临时 UI 状态，而是能继续恢复、定位问题或推进下一步。

## Confirmed Facts

- 当前仓库无未提交变更，最近两个相关任务已归档：
  - `06-28-frontend-real-usable`：完成小说设定和章节目录真实生成执行器。
  - `06-28-frontend-chapter-generation-real-usable`：完成单章草稿和单章定稿真实执行器。
- `docs/feature-map-and-acceptance.md` 的“新前端真实可用开发顺序”中，已完成前两个优先项；后续顺序是任务持久化与可恢复工作流、知识库真实向量化与检索、项目管理能力、章节生命周期补齐。
- `app/api/server.py` 当前仍使用 `generation_jobs: dict[str, GenerationJob] = {}` 保存任务；后端重启后任务历史和日志会丢失。
- `POST /api/generation-jobs` 当前已对 `architecture`、`directory`、`draft`、`finalization` 走真实执行器；`consistency` 和 `batch` 仍只创建任务记录。
- `frontend/src/stores/generation.ts` 和生成页已经通过 `serviceBridge` 调用本地 API，但任务列表只来自当前进程内存状态。
- `frontend/src/services/serviceBridge.ts` 是前端真实/Mock 数据访问和写操作守卫的统一入口；页面不应新增对 `mockApi` 的直接依赖。
- 本项目已有旧架构重构计划提到 SQLite 项目状态与任务仓储，但当前本地 API 仍是单文件最小服务边界。
- 用户已确认本轮按“任务持久化与可恢复工作流最小闭环”执行，不优先做知识库真实向量化、项目管理或章节生命周期。

## Requirements

- R1. 本轮只实现任务持久化与最小可恢复工作流，避免一次展开多个方向。
- R2. 仍保持新前端通过本地 FastAPI 边界访问能力；前端不得直接调用 Python legacy 生成函数。
- R3. 新增能力必须兼容旧 Python GUI，不破坏 `python main.py`。
- R4. 真实写操作必须继续通过 `serviceBridge` 的后端模式和写操作守卫控制。
- R5. 不提交 `config.json`、API Key、私有 Base URL、真实小说正文、`vectorstore/` 或前端构建产物。
- R6. 后端必须把生成任务持久化到本地状态文件中，至少保存任务 ID、项目 ID、阶段、标题、状态、进度、开始时间、日志、错误和创建请求参数。
- R7. 状态文件必须与 `config.json`、输出目录和旧 GUI 数据分离；不得迁移或改写现有小说输出文件格式。
- R8. `create_app(config_file=...)` 测试隔离入口必须能指定或推导隔离的任务状态存储位置，测试不得读写真实用户状态。
- R9. 服务重启后，`GET /api/projects/{project_id}/jobs` 必须能返回之前创建的任务，`GET /api/generation-jobs/{job_id}` 必须能读取该任务详情。
- R10. 创建任务时必须先持久化接收记录，再在同步执行完成或失败后更新同一条任务记录，避免只返回响应但不落盘。
- R11. 失败任务必须保留中文错误、完整日志和原始请求参数，支持用户刷新后继续定位问题。
- R12. 本轮只预留重试所需的数据结构，不实现“重试按钮”、后台异步队列、轮询进度、跨进程取消或暂停。
- R13. 前端生成页应说明任务历史来自本地状态存储，并在刷新或重新进入页面后展示已持久化任务；不需要新增大规模 UI 结构。
- R14. 任务列表排序应稳定，最新任务优先；同项目过滤必须继续按 `projectId` 生效。

## Acceptance Criteria

- [ ] 规划阶段产出收敛后的 `prd.md`、`design.md` 和 `implement.md`。
- [ ] 后端新增本地任务状态存储，默认不会提交到 git，测试可使用临时路径隔离。
- [ ] 创建 `consistency` 或 `batch` 这类 queued 任务后，重新创建一个 app/client 仍能通过列表和详情接口读回任务。
- [ ] 创建 `architecture`、`directory`、`draft` 或 `finalization` 这类同步执行任务后，执行结果 `done` / `failed`、进度、日志和错误会持久化。
- [ ] 失败任务刷新后仍保留中文错误和日志；测试覆盖缺 API Key 或缺章节目录等失败路径之一。
- [ ] 前端生成页能加载持久化任务历史；刷新或重新进入页面后列表仍展示后端返回的历史记录。
- [ ] `python -m pytest tests` 通过，或记录明确环境阻塞。
- [ ] `cd frontend && npm run typecheck` 通过，或记录明确环境阻塞。
- [ ] `cd frontend && npm run build` 通过，或记录明确环境阻塞。
- [ ] `docs/feature-map-and-acceptance.md`、`AGENTS.md` 和必要的 `.trellis/spec/` 规范更新任务持久化边界。

## Out Of Scope

- 不实现知识库真实向量化与检索。
- 不实现项目新建、打开、切换或最近项目。
- 不实现章节生命周期数据库或章节状态管理。
- 不实现一致性审校真实执行。
- 不实现批量章节真实执行。
- 不实现后台异步队列、进度轮询、暂停、取消或跨进程恢复正在运行的任务。
- 不实现前端重试按钮；仅保存可供后续重试使用的请求参数。
- 不重做生成页视觉结构。

## Notes

- 本任务属于复杂任务，进入实现前必须补充 `design.md` 和 `implement.md`，并经用户确认后再 `task.py start`。
