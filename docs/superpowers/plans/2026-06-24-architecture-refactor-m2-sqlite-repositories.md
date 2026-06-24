# Milestone 2 SQLite 项目状态与仓储层 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 引入 SQLite 作为项目状态事实来源，管理项目、章节、摘要、角色状态和生成任务。

**Architecture:** 使用仓储层隔离 SQLite 细节，旧文本文件继续作为导入/导出格式。Milestone 2 不改变 GUI 行为，只为后续工作流和 API 提供稳定持久化能力。

**Tech Stack:** SQLite、SQLModel 或 SQLAlchemy、pytest、tempfile。

---

## 文件结构

- Create: `app/repositories/__init__.py`
- Create: `app/repositories/database.py`
- Create: `app/repositories/schema.py`
- Create: `app/repositories/project_repository.py`
- Create: `app/repositories/chapter_repository.py`
- Create: `app/repositories/job_repository.py`
- Create: `tests/test_project_repository.py`
- Create: `tests/test_chapter_repository.py`
- Create: `tests/test_job_repository.py`

## Task 1: 建立数据库连接和表结构

**Files:**
- Create: `app/repositories/database.py`
- Create: `app/repositories/schema.py`
- Test: `tests/test_project_repository.py`

- [ ] **Step 1: 写失败测试**

```python
from app.repositories.database import create_session_factory, init_database
from app.repositories.project_repository import ProjectRepository


def test_create_project_roundtrip(tmp_path):
    db_path = tmp_path / "state.sqlite3"
    session_factory = create_session_factory(db_path)
    init_database(session_factory)
    repo = ProjectRepository(session_factory)

    project = repo.create_project(name="测试小说", output_path=str(tmp_path / "out"))

    loaded = repo.get_project(project.id)
    assert loaded is not None
    assert loaded.name == "测试小说"
    assert loaded.output_path.endswith("out")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_project_repository.py -v`

Expected: FAIL，提示仓储模块不存在。

- [ ] **Step 3: 实现数据库基础设施和项目表**

使用 SQLModel 时实现：

```python
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session


def create_session_factory(db_path: str | Path):
    engine = create_engine(f"sqlite:///{Path(db_path)}")

    def factory():
        return Session(engine)

    factory.engine = engine
    return factory


def init_database(session_factory):
    SQLModel.metadata.create_all(session_factory.engine)
```

```python
from datetime import datetime
from sqlmodel import Field, SQLModel


class ProjectRecord(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    output_path: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

- [ ] **Step 4: 实现 ProjectRepository**

```python
from uuid import uuid4
from sqlmodel import select
from app.repositories.schema import ProjectRecord


class ProjectRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def create_project(self, name: str, output_path: str) -> ProjectRecord:
        record = ProjectRecord(id=str(uuid4()), name=name, output_path=output_path)
        with self.session_factory() as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    def get_project(self, project_id: str) -> ProjectRecord | None:
        with self.session_factory() as session:
            return session.exec(select(ProjectRecord).where(ProjectRecord.id == project_id)).first()
```

- [ ] **Step 5: 运行测试确认通过**

Run: `python -m pytest tests/test_project_repository.py -v`

Expected: PASS。

- [ ] **Step 6: 提交**

```bash
git add app/repositories tests/test_project_repository.py
git commit -m "feat(storage): 新增 SQLite 项目仓储"
```

## Task 2: 建立章节仓储

**Files:**
- Modify: `app/repositories/schema.py`
- Create: `app/repositories/chapter_repository.py`
- Test: `tests/test_chapter_repository.py`

- [ ] **Step 1: 写失败测试**

```python
from app.repositories.database import create_session_factory, init_database
from app.repositories.project_repository import ProjectRepository
from app.repositories.chapter_repository import ChapterRepository


def test_save_and_load_chapter(tmp_path):
    session_factory = create_session_factory(tmp_path / "state.sqlite3")
    init_database(session_factory)
    project = ProjectRepository(session_factory).create_project("测试小说", str(tmp_path))
    repo = ChapterRepository(session_factory)

    repo.save_chapter(project.id, 1, "第一章", "正文", status="draft")

    chapter = repo.get_chapter(project.id, 1)
    assert chapter.title == "第一章"
    assert chapter.content == "正文"
    assert chapter.status == "draft"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_chapter_repository.py -v`

Expected: FAIL。

- [ ] **Step 3: 增加章节表和仓储**

```python
class ChapterRecord(SQLModel, table=True):
    id: str = Field(primary_key=True)
    project_id: str = Field(index=True)
    chapter_number: int = Field(index=True)
    title: str = ""
    outline: str = ""
    content: str = ""
    status: str = "planned"
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

```python
from datetime import datetime
from uuid import uuid4
from sqlmodel import select
from app.repositories.schema import ChapterRecord


class ChapterRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def save_chapter(self, project_id: str, chapter_number: int, title: str, content: str, status: str):
        with self.session_factory() as session:
            record = session.exec(
                select(ChapterRecord).where(
                    ChapterRecord.project_id == project_id,
                    ChapterRecord.chapter_number == chapter_number,
                )
            ).first()
            if record is None:
                record = ChapterRecord(
                    id=str(uuid4()),
                    project_id=project_id,
                    chapter_number=chapter_number,
                )
            record.title = title
            record.content = content
            record.status = status
            record.updated_at = datetime.utcnow()
            session.add(record)
            session.commit()

    def get_chapter(self, project_id: str, chapter_number: int):
        with self.session_factory() as session:
            return session.exec(
                select(ChapterRecord).where(
                    ChapterRecord.project_id == project_id,
                    ChapterRecord.chapter_number == chapter_number,
                )
            ).first()
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_chapter_repository.py -v`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add app/repositories tests/test_chapter_repository.py
git commit -m "feat(storage): 新增章节仓储"
```

## Task 3: 建立生成任务仓储

**Files:**
- Modify: `app/repositories/schema.py`
- Create: `app/repositories/job_repository.py`
- Test: `tests/test_job_repository.py`

- [ ] **Step 1: 写失败测试**

```python
from app.repositories.database import create_session_factory, init_database
from app.repositories.job_repository import JobRepository


def test_job_status_transition(tmp_path):
    session_factory = create_session_factory(tmp_path / "state.sqlite3")
    init_database(session_factory)
    repo = JobRepository(session_factory)

    job = repo.create_job(project_id="p1", job_type="chapter_draft", payload={"chapter_number": 1})
    repo.mark_running(job.id)
    repo.mark_succeeded(job.id, result={"chapter_number": 1})

    loaded = repo.get_job(job.id)
    assert loaded.status == "succeeded"
    assert loaded.result["chapter_number"] == 1
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_job_repository.py -v`

Expected: FAIL。

- [ ] **Step 3: 增加 Job 表和仓储**

```python
class GenerationJobRecord(SQLModel, table=True):
    id: str = Field(primary_key=True)
    project_id: str = Field(index=True)
    job_type: str
    status: str = "pending"
    payload_json: str = "{}"
    result_json: str = "{}"
    error: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

仓储对外暴露 `payload` 和 `result` 字典，内部使用 `json.dumps/json.loads`。

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_job_repository.py -v`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add app/repositories tests/test_job_repository.py
git commit -m "feat(storage): 新增生成任务仓储"
```

## Milestone 2 验收

- SQLite 可创建项目、保存章节、保存任务状态。
- 所有仓储测试使用临时数据库，不污染项目目录。
- 旧 txt 输出仍未被移除。
