# Milestone 3 可恢复生成工作流 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把小说设定、目录、章节草稿、定稿流程封装成可恢复、可测试、可观测的工作流服务。

**Architecture:** 工作流层调用 Provider、Repository 和旧 `novel_generator` 适配函数。每个工作流步骤写入任务状态，失败时保留错误和上下文，下一次可以从最近成功步骤恢复。

**Tech Stack:** Python、pytest、SQLite 仓储、Provider 协议、旧生成模块适配。

---

## 文件结构

- Create: `app/workflows/__init__.py`
- Create: `app/workflows/state.py`
- Create: `app/workflows/context.py`
- Create: `app/workflows/architecture_workflow.py`
- Create: `app/workflows/chapter_workflow.py`
- Create: `app/services/__init__.py`
- Create: `app/services/generation_service.py`
- Create: `tests/test_workflow_state.py`
- Create: `tests/test_architecture_workflow.py`
- Create: `tests/test_chapter_workflow.py`

## Task 1: 建立工作流状态类型

**Files:**
- Create: `app/workflows/state.py`
- Test: `tests/test_workflow_state.py`

- [ ] **Step 1: 写失败测试**

```python
from app.workflows.state import WorkflowStepResult, WorkflowStepStatus


def test_step_result_serializes_status():
    result = WorkflowStepResult.succeeded(step_name="core_seed", output={"text": "ok"})

    assert result.step_name == "core_seed"
    assert result.status == WorkflowStepStatus.SUCCEEDED
    assert result.output["text"] == "ok"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_workflow_state.py -v`

Expected: FAIL。

- [ ] **Step 3: 实现状态类型**

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WorkflowStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class WorkflowStepResult:
    step_name: str
    status: WorkflowStepStatus
    output: dict[str, Any] = field(default_factory=dict)
    error: str = ""

    @classmethod
    def succeeded(cls, step_name: str, output: dict[str, Any]):
        return cls(step_name=step_name, status=WorkflowStepStatus.SUCCEEDED, output=output)

    @classmethod
    def failed(cls, step_name: str, error: str):
        return cls(step_name=step_name, status=WorkflowStepStatus.FAILED, error=error)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_workflow_state.py -v`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add app/workflows tests/test_workflow_state.py
git commit -m "feat(workflow): 新增工作流步骤状态模型"
```

## Task 2: 封装设定生成工作流

**Files:**
- Create: `app/workflows/architecture_workflow.py`
- Test: `tests/test_architecture_workflow.py`

- [ ] **Step 1: 写失败测试**

```python
from app.workflows.architecture_workflow import ArchitectureWorkflow


class FakeProvider:
    def __init__(self):
        self.prompts = []

    def generate(self, request):
        self.prompts.append(request.prompt)
        return type("Response", (), {"text": "片段"})()


def test_architecture_workflow_generates_sections(tmp_path):
    provider = FakeProvider()
    workflow = ArchitectureWorkflow(provider=provider)

    result = workflow.run(topic="星际远征", genre="科幻", number_of_chapters=10, word_number=3000)

    assert result.status.value == "succeeded"
    assert "片段" in result.output["architecture_text"]
    assert len(provider.prompts) >= 3
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_architecture_workflow.py -v`

Expected: FAIL。

- [ ] **Step 3: 实现可测试的设定工作流**

```python
from app.providers.llm import LLMRequest
from app.workflows.state import WorkflowStepResult


class ArchitectureWorkflow:
    def __init__(self, provider):
        self.provider = provider

    def run(self, topic: str, genre: str, number_of_chapters: int, word_number: int) -> WorkflowStepResult:
        sections = []
        prompts = [
            f"请为主题《{topic}》生成核心种子，类型：{genre}，章节数：{number_of_chapters}。",
            f"请为主题《{topic}》生成角色动力学。",
            f"请为主题《{topic}》生成世界观。",
            f"请为主题《{topic}》生成三幕式情节架构，每章约 {word_number} 字。",
        ]
        try:
            for prompt in prompts:
                sections.append(self.provider.generate(LLMRequest(prompt=prompt)).text)
            return WorkflowStepResult.succeeded(
                "architecture",
                {"architecture_text": "\n\n".join(sections)},
            )
        except Exception as exc:
            return WorkflowStepResult.failed("architecture", str(exc))
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_architecture_workflow.py -v`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add app/workflows/architecture_workflow.py tests/test_architecture_workflow.py
git commit -m "feat(workflow): 新增小说设定生成工作流"
```

## Task 3: 封装章节生成工作流

**Files:**
- Create: `app/workflows/chapter_workflow.py`
- Test: `tests/test_chapter_workflow.py`

- [ ] **Step 1: 写失败测试**

```python
from app.workflows.chapter_workflow import ChapterWorkflow


class FakeProvider:
    def generate(self, request):
        if "大纲" in request.prompt:
            return type("Response", (), {"text": "本章大纲"})()
        return type("Response", (), {"text": "本章正文"})()


def test_chapter_workflow_generates_outline_and_draft():
    workflow = ChapterWorkflow(provider=FakeProvider())

    result = workflow.run(
        project_context="世界观",
        chapter_number=1,
        chapter_blueprint="第一章：启程",
        user_guidance="节奏紧凑",
    )

    assert result.status.value == "succeeded"
    assert result.output["outline"] == "本章大纲"
    assert result.output["content"] == "本章正文"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_chapter_workflow.py -v`

Expected: FAIL。

- [ ] **Step 3: 实现章节工作流**

```python
from app.providers.llm import LLMRequest
from app.workflows.state import WorkflowStepResult


class ChapterWorkflow:
    def __init__(self, provider):
        self.provider = provider

    def run(self, project_context: str, chapter_number: int, chapter_blueprint: str, user_guidance: str = ""):
        try:
            outline_prompt = (
                f"基于项目上下文生成第 {chapter_number} 章大纲。\n"
                f"上下文：{project_context}\n章节蓝图：{chapter_blueprint}\n用户指导：{user_guidance}"
            )
            outline = self.provider.generate(LLMRequest(prompt=outline_prompt)).text
            draft_prompt = (
                f"基于以下大纲生成第 {chapter_number} 章正文。\n"
                f"大纲：{outline}\n章节蓝图：{chapter_blueprint}\n用户指导：{user_guidance}"
            )
            content = self.provider.generate(LLMRequest(prompt=draft_prompt)).text
            return WorkflowStepResult.succeeded(
                "chapter_draft",
                {"outline": outline, "content": content},
            )
        except Exception as exc:
            return WorkflowStepResult.failed("chapter_draft", str(exc))
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_chapter_workflow.py -v`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add app/workflows/chapter_workflow.py tests/test_chapter_workflow.py
git commit -m "feat(workflow): 新增章节草稿生成工作流"
```

## Task 4: 建立 GenerationService 编排层

**Files:**
- Create: `app/services/generation_service.py`
- Test: `tests/test_generation_service.py`

- [ ] **Step 1: 写失败测试**

```python
from app.services.generation_service import GenerationService


class FakeJobRepo:
    def __init__(self):
        self.created = []

    def create_job(self, project_id, job_type, payload):
        job = type("Job", (), {"id": "job-1"})()
        self.created.append((project_id, job_type, payload))
        return job


def test_generation_service_creates_chapter_job():
    repo = FakeJobRepo()
    service = GenerationService(job_repository=repo)

    job = service.create_chapter_draft_job("p1", 3)

    assert job.id == "job-1"
    assert repo.created[0][1] == "chapter_draft"
    assert repo.created[0][2]["chapter_number"] == 3
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_generation_service.py -v`

Expected: FAIL。

- [ ] **Step 3: 实现服务层**

```python
class GenerationService:
    def __init__(self, job_repository):
        self.job_repository = job_repository

    def create_chapter_draft_job(self, project_id: str, chapter_number: int):
        return self.job_repository.create_job(
            project_id=project_id,
            job_type="chapter_draft",
            payload={"chapter_number": chapter_number},
        )
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_generation_service.py -v`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add app/services tests/test_generation_service.py
git commit -m "feat(service): 新增生成任务编排服务"
```

## Milestone 3 验收

- 设定生成、章节生成可通过工作流对象测试。
- 工作流不依赖 GUI。
- 生成任务可以进入仓储状态管理。
- 失败结果能被表达为 `WorkflowStepResult.failed()`。
