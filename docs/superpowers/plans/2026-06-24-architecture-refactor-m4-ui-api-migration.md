# Milestone 4 GUI 服务化迁移与本地 API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 引入本地 FastAPI API，并让现有 GUI 的关键操作逐步调用服务层，而不是直接调用生成函数。

**Architecture:** FastAPI 作为本地后端边界，当前 `customtkinter` GUI 暂时保留。GUI 先迁移配置测试、项目查询、生成任务创建这些低风险入口，再迁移章节生成和定稿。

**Tech Stack:** FastAPI、Uvicorn、pytest、httpx/TestClient、现有 customtkinter。

---

## 文件结构

- Create: `app/api/__init__.py`
- Create: `app/api/main.py`
- Create: `app/api/dependencies.py`
- Create: `app/api/routes_projects.py`
- Create: `app/api/routes_generation.py`
- Create: `app/client/__init__.py`
- Create: `app/client/local_api_client.py`
- Create: `tests/test_api_projects.py`
- Create: `tests/test_api_generation.py`
- Modify: `ui/generation_handlers.py`
- Modify: `requirements.txt`

## Task 1: 建立 FastAPI 应用和健康检查

**Files:**
- Create: `app/api/main.py`
- Test: `tests/test_api_projects.py`
- Modify: `requirements.txt`

- [ ] **Step 1: 写失败测试**

```python
from fastapi.testclient import TestClient
from app.api.main import create_app


def test_health_check():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_api_projects.py::test_health_check -v`

Expected: FAIL，提示 FastAPI 或 API 模块不存在。

- [ ] **Step 3: 添加依赖**

在 `requirements.txt` 增加：

```text
fastapi
uvicorn
httpx
```

- [ ] **Step 4: 实现 API 应用**

```python
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="AI Novel Generator Local API")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 5: 运行测试确认通过**

Run: `python -m pytest tests/test_api_projects.py::test_health_check -v`

Expected: PASS。

- [ ] **Step 6: 提交**

```bash
git add app/api tests/test_api_projects.py requirements.txt
git commit -m "feat(api): 新增本地 FastAPI 健康检查"
```

## Task 2: 提供项目 API

**Files:**
- Create: `app/api/routes_projects.py`
- Modify: `app/api/main.py`
- Test: `tests/test_api_projects.py`

- [ ] **Step 1: 写失败测试**

```python
from fastapi.testclient import TestClient
from app.api.main import create_app


def test_create_project_api(tmp_path):
    client = TestClient(create_app(database_path=tmp_path / "state.sqlite3"))

    response = client.post("/projects", json={"name": "测试小说", "output_path": str(tmp_path / "out")})

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "测试小说"
    assert body["output_path"].endswith("out")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_api_projects.py::test_create_project_api -v`

Expected: FAIL。

- [ ] **Step 3: 实现项目路由**

```python
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel
from app.repositories.database import create_session_factory, init_database
from app.repositories.project_repository import ProjectRepository


class CreateProjectRequest(BaseModel):
    name: str
    output_path: str


def create_projects_router(database_path: str | Path):
    router = APIRouter()
    session_factory = create_session_factory(database_path)
    init_database(session_factory)
    repo = ProjectRepository(session_factory)

    @router.post("/projects")
    def create_project(request: CreateProjectRequest):
        project = repo.create_project(request.name, request.output_path)
        return {"id": project.id, "name": project.name, "output_path": project.output_path}

    return router
```

`create_app(database_path=None)` 中注册该 router，默认数据库位置使用项目根目录 `.local/state.sqlite3`。

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_api_projects.py -v`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add app/api tests/test_api_projects.py
git commit -m "feat(api): 新增项目管理接口"
```

## Task 3: 提供生成任务 API

**Files:**
- Create: `app/api/routes_generation.py`
- Modify: `app/api/main.py`
- Test: `tests/test_api_generation.py`

- [ ] **Step 1: 写失败测试**

```python
from fastapi.testclient import TestClient
from app.api.main import create_app


def test_create_chapter_draft_job_api(tmp_path):
    client = TestClient(create_app(database_path=tmp_path / "state.sqlite3"))

    response = client.post("/generation/chapter-drafts", json={"project_id": "p1", "chapter_number": 2})

    assert response.status_code == 200
    body = response.json()
    assert body["job_type"] == "chapter_draft"
    assert body["status"] == "pending"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_api_generation.py -v`

Expected: FAIL。

- [ ] **Step 3: 实现生成任务路由**

```python
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel
from app.repositories.database import create_session_factory, init_database
from app.repositories.job_repository import JobRepository
from app.services.generation_service import GenerationService


class CreateChapterDraftJobRequest(BaseModel):
    project_id: str
    chapter_number: int


def create_generation_router(database_path: str | Path):
    router = APIRouter()
    session_factory = create_session_factory(database_path)
    init_database(session_factory)
    service = GenerationService(JobRepository(session_factory))

    @router.post("/generation/chapter-drafts")
    def create_chapter_draft_job(request: CreateChapterDraftJobRequest):
        job = service.create_chapter_draft_job(request.project_id, request.chapter_number)
        return {"id": job.id, "project_id": job.project_id, "job_type": job.job_type, "status": job.status}

    return router
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_api_generation.py -v`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add app/api tests/test_api_generation.py
git commit -m "feat(api): 新增章节生成任务接口"
```

## Task 4: GUI 接入本地 API 客户端

**Files:**
- Create: `app/client/local_api_client.py`
- Modify: `ui/generation_handlers.py`
- Test: `tests/test_local_api_client.py`

- [ ] **Step 1: 写客户端测试**

```python
from app.client.local_api_client import LocalAPIClient


class FakeHTTP:
    def __init__(self):
        self.last_json = None

    def post(self, path, json):
        self.last_json = json
        return type("Response", (), {
            "raise_for_status": lambda self: None,
            "json": lambda self: {"id": "job-1", "status": "pending"},
        })()


def test_local_api_client_creates_chapter_job():
    http = FakeHTTP()
    client = LocalAPIClient(http)

    result = client.create_chapter_draft_job("p1", 1)

    assert http.last_json == {"project_id": "p1", "chapter_number": 1}
    assert result["id"] == "job-1"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_local_api_client.py -v`

Expected: FAIL。

- [ ] **Step 3: 实现客户端**

```python
class LocalAPIClient:
    def __init__(self, http_client):
        self.http_client = http_client

    def create_chapter_draft_job(self, project_id: str, chapter_number: int):
        response = self.http_client.post(
            "/generation/chapter-drafts",
            json={"project_id": project_id, "chapter_number": chapter_number},
        )
        response.raise_for_status()
        return response.json()
```

- [ ] **Step 4: 在 GUI 中只迁移低风险入口**

先在 `ui/generation_handlers.py` 新增可选调用路径：当 `gui.local_api_client` 存在时，生成章节按钮先创建任务并记录日志；否则沿用旧同步生成逻辑。

- [ ] **Step 5: 运行测试**

Run: `python -m pytest tests -v`

Expected: PASS。

- [ ] **Step 6: 提交**

```bash
git add app/client ui/generation_handlers.py tests/test_local_api_client.py
git commit -m "feat(ui): 新增本地 API 客户端接入点"
```

## Milestone 4 验收

- 本地 API 有健康检查、项目创建、章节生成任务创建。
- GUI 仍可运行，且保留旧逻辑兜底。
- `python -m pytest tests` 通过。
- 后续可选择继续迁移章节生成、定稿、审校到 API。
