# Database Guidelines

当前项目只有一个最小 SQLite 状态库用于保存前端生成任务历史和最近项目索引；核心业务数据仍由本地 `config.json`、输出目录文本文件、角色库目录、WebDAV 配置备份和 Chroma `vectorstore/` 承载。项目没有 ORM 或迁移系统。

## 当前真实状态

- 不存在 SQLAlchemy、Alembic、Django ORM、Prisma 或迁移系统。
- `app/services/generation_job_store.py` 使用标准库 `sqlite3` 管理 `generation_jobs` 表，仅保存生成任务状态、日志、错误和创建请求参数。
- `app/services/project_store.py` 使用同一个 SQLite 文件管理 `recent_projects` 表，仅保存最近项目索引；当前项目和项目参数仍以 `config.json` 为准。
- 默认任务状态库为项目根目录 `.local/state.sqlite3`，`.local/` 已被 `.gitignore` 忽略。
- `app/api/server.py` 的 `create_app(config_file=...)` 通过可注入配置文件支持测试隔离。
- `app/api/server.py` 的 `create_app(state_db_file=...)` 通过可注入数据库路径支持任务状态测试隔离。
- API 和旧 GUI 都读写 legacy `config.json`，但 API 对前端暴露 camelCase Pydantic model。
- 章节、设定、目录、角色库、剧情要点都是输出目录下的 UTF-8 文本文件。
- 向量库是当前输出目录下的 `vectorstore/`，不是关系型数据库。

## 示例

测试隔离入口来自 `app/api/server.py`：

```python
def create_app(
    config_file: str | Path | None = None,
    state_db_file: str | Path | None = None,
) -> FastAPI:
    app = FastAPI(title="AI Novel Generator Local API")
    config_path = Path(config_file) if config_file is not None else DEFAULT_CONFIG_FILE
```

API 测试应使用临时配置文件，例如 `tests/test_api_project_config.py`：

```python
config_file = tmp_path / "config.json"
state_db_file = tmp_path / "state.sqlite3"
client = TestClient(create_app(config_file=str(config_file), state_db_file=str(state_db_file)))
```

章节文件路径仍按 legacy 文件名拼接：

```python
def _chapter_file_path(output_path: Path, chapter_number: int) -> Path:
    return output_path / f"chapter_{chapter_number}.txt"
```

## 扩大数据库范围前的要求

如果后续 milestone 要把 SQLite 从“最近项目索引”扩大到完整项目配置、章节、知识库或其他业务数据，必须先更新设计文档和本规范，并明确：

- 数据库文件位置、备份和 `.gitignore` 规则。
- schema owner、迁移工具和迁移执行入口。
- legacy `config.json` 与输出目录文本文件的迁移或双写策略。
- `python main.py` 旧 GUI 的兼容边界。
- API 测试如何创建临时数据库并避免污染真实用户数据。

在上述设计落地前，不要新增空壳迁移目录、伪 ORM 层或只在文档里存在的 repository 抽象。

## Scenario: Generation Job SQLite Store

### 1. Scope / Trigger

- Trigger: 前端生成任务历史需要在后端重启后可恢复。
- Scope: 仅 `POST /api/generation-jobs`、`GET /api/projects/{project_id}/jobs`、`GET /api/generation-jobs/{job_id}` 使用 SQLite 状态库。
- Out of scope: 不把项目配置、章节正文、角色库、知识库或向量库迁移到 SQLite。

### 2. Signatures

- Store module: `app/services/generation_job_store.py`
- Store class: `GenerationJobStore(db_file: str | Path)`
- Save: `save_job(job: dict[str, Any], request: dict[str, Any]) -> None`
- List: `list_jobs(project_id: str) -> list[dict[str, Any]]`
- Detail: `get_job(job_id: str) -> dict[str, Any] | None`
- App factory: `create_app(config_file: str | Path | None = None, state_db_file: str | Path | None = None)`

### 3. Contracts

- Default database path: `.local/state.sqlite3` under the project root for normal app use.
- Test database path: pass `state_db_file=tmp_path / "state.sqlite3"` to isolate state.
- Table: `generation_jobs`
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
- `log_json` is the JSON array backing `GenerationJob.log`.
- `request_json` stores the original `GenerationJobCreateRequest` payload for future retry work; current API responses do not expose it.

### 4. Validation & Error Matrix

- Unknown `job_id` -> API returns HTTP `404` with `detail="任务不存在"`.
- SQLite read/write failure during task creation -> do not pretend the task succeeded; allow the request to fail loudly.
- Executable generation failure -> persist `GenerationJob(status="failed")`, `error`, and full log.
- Unsupported stage / invalid batch range / missing chapter validation remains owned by `app/api/server.py` before store writes.

### 5. Good/Base/Bad Cases

- Good: Create a `consistency` task with a fake审校 executor, rebuild `TestClient(create_app(..., state_db_file=same_path))`, then read `status == "done"` and the persisted审校 result log.
- Good: Create an `architecture` task with fake executor, then rebuild the app and read `status == "done"`, `progress == 100`, and completion log.
- Base: Create a `draft` task without `Novel_directory.txt`, then rebuild the app and read `status == "failed"` plus Chinese error.
- Bad: Keeping task state only in a process-local dict; the frontend appears usable until the backend restarts, then history disappears.
- Bad: Storing task history in `config.json`; that risks mixing transient execution logs with user configuration and WebDAV backup data.

### 6. Tests Required

- API tests must pass both `config_file` and `state_db_file` with temporary paths.
- Required assertions:
  - queued `batch` jobs survive app/client reconstruction.
  - done `consistency` jobs survive app/client reconstruction with审校 result log.
  - done jobs survive app/client reconstruction with progress, log, and null error.
  - failed jobs survive app/client reconstruction with Chinese error and log.
  - existing in-request list/detail behavior still works.
- Full regression command: `.venv/bin/python -m pytest tests`.

### 7. Wrong vs Correct

#### Wrong

```python
generation_jobs: dict[str, GenerationJob] = {}
generation_jobs[job.id] = job
```

This loses all task history when the FastAPI process restarts.

#### Correct

```python
job_store = GenerationJobStore(state_db_file)
job_store.save_job(job.model_dump(), request.model_dump())
return [GenerationJob(**job) for job in job_store.list_jobs(project_id)]
```

The API keeps the existing response model while the store owns durable task history.
