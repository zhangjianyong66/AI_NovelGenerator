# 前端任务持久化与可恢复工作流设计

## 目标边界

本轮只把生成任务从进程内存字典持久化到本地状态存储，让用户在后端重启、前端刷新或重新进入生成页后仍能查看任务历史、日志、错误和创建参数。当前同步执行模型保持不变：`architecture`、`directory`、`draft`、`finalization` 仍在 `POST /api/generation-jobs` 请求内同步执行；`consistency` 和 `batch` 仍是 queued 任务记录边界。

不迁移 `config.json`、小说输出目录、章节文件、角色库或向量库；不替换旧 GUI；不引入后台队列。

## 推荐方案

采用标准库 `sqlite3` 实现一个小型任务仓储，存储在本地状态目录下。推荐默认路径为项目根目录 `.local/state.sqlite3`，并把 `.local/` 加入 `.gitignore`。测试中由 `create_app(config_file=tmp_path / "config.json")` 推导为同目录的 `.local/state.sqlite3`，或通过新增可选参数显式传入临时数据库路径。

选择 SQLite 的原因：

- 任务历史是结构化数据，后续会自然扩展重试、阶段、日志过滤和项目状态。
- 标准库即可实现，不需要新增 ORM 或迁移工具。
- 相比 JSON 文件，SQLite 更适合按项目 ID 和任务 ID 查询，也更容易保证单条任务更新的一致性。

备选方案及取舍：

- JSONL：实现最小，但列表和详情需要重放日志，后续修改任务状态会变成追加事件模型，当前代码改动不一定更小。
- JSON 文件数组：易读，但并发和原子更新复杂，任务日志变大后每次写全量文件不合适。

## 数据模型

表名：`generation_jobs`

字段：

- `id TEXT PRIMARY KEY`
- `project_id TEXT NOT NULL`
- `title TEXT NOT NULL`
- `stage TEXT NOT NULL`
- `status TEXT NOT NULL`
- `progress INTEGER NOT NULL`
- `started_at TEXT NOT NULL`
- `log_json TEXT NOT NULL`
- `error TEXT`
- `request_json TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

`log_json` 存储 `GenerationJob.log` 的 JSON 数组。`request_json` 存储 `GenerationJobCreateRequest` 的 JSON 对象，用于后续重试，不在本轮直接消费。响应模型暂不增加 `request` 字段，避免前端类型面扩大；仓储内部保留数据即可。

索引：

- `idx_generation_jobs_project_updated`：`project_id, updated_at`

## 数据流

创建任务：

1. API 校验 `stage`、章节范围和输出路径。
2. 构造 `GenerationJob`，日志包含接收请求和输出路径。
3. 调用仓储 `save(job, request)` 持久化接收记录。
4. 如果阶段已接入真实执行器，将状态改为 `running` 并再次保存。
5. 同步执行 `run_generation_job(...)`。
6. 将 `done` 或 `failed`、进度、日志和错误写回同一任务 ID。
7. 返回最终任务响应。

读取任务列表：

1. `GET /api/projects/{project_id}/jobs` 从 SQLite 按 `project_id` 查询。
2. 转回现有 `GenerationJob` Pydantic model。
3. 最新任务优先。

读取任务详情：

1. `GET /api/generation-jobs/{job_id}` 从 SQLite 按 ID 查询。
2. 不存在返回 `404 detail="任务不存在"`。

## 模块边界

新增 `app/services/generation_job_store.py`：

- 拥有 SQLite schema 初始化。
- 拥有 `GenerationJob` 与数据库行之间的转换。
- 暴露 `save_job(job, request_payload)`、`list_jobs(project_id)`、`get_job(job_id)`。
- 只依赖标准库和 `app.api.server` 的模型会造成循环依赖，因此实现时应避免从 store 反向 import API module。更稳妥的做法是让 store 读写普通 dict，API 层负责把 Pydantic model 转为 dict、再从 dict 还原模型。

`app/api/server.py`：

- 保持 API handler 是薄层。
- 用仓储替换 `generation_jobs: dict[str, GenerationJob] = {}`。
- `create_app` 增加可选 `state_db_file: str | Path | None = None`；未传入时按配置文件位置推导状态库路径。

前端：

- `frontend/src/stores/generation.ts` 继续调用 `serviceBridge.listGenerationJobs()` 和 `createGenerationJob()`。
- 生成页可增加一条简短信息：任务历史保存在本地状态库，后端重启后仍可查看。
- 不新增直接 mock 写入或绕过 `serviceBridge` 的调用。

## 兼容与迁移

- 旧 GUI 不读取 `.local/state.sqlite3`，因此不受影响。
- 旧的进程内任务不会迁移；本功能上线前已经存在于内存中的任务在重启后仍会丢失，这是可接受边界。
- `.local/` 必须忽略提交。
- SQLite schema 采用 `CREATE TABLE IF NOT EXISTS` 和 `CREATE INDEX IF NOT EXISTS`，不引入迁移框架。

## 错误处理

- 数据库初始化或读写失败不应伪装成任务成功。创建任务时如果接收记录无法持久化，应返回 500，由 FastAPI 暴露开发错误。
- 任务执行失败仍返回 `GenerationJob(status="failed")`，并把中文错误和日志写入数据库。
- 读取不存在的任务继续返回 `404`。

## 测试策略

- API 测试使用临时 `config.json` 和临时 SQLite 路径，不能读写真实 `.local/state.sqlite3`。
- 覆盖 queued 任务跨 app/client 重建后可读。
- 覆盖真实执行阶段成功结果持久化。
- 覆盖真实执行阶段失败结果持久化。
- 前端至少跑 `npm run typecheck` 和 `npm run build`；如有文案/状态改动，补充源码契约测试。

## 回滚策略

本轮改动集中在任务仓储和生成任务 API。若出现问题，可回退到内存字典实现，不影响 `config.json`、输出目录和旧 GUI。用户本地 `.local/state.sqlite3` 是附加状态文件，删除后只会丢失任务历史，不会删除小说正文。
