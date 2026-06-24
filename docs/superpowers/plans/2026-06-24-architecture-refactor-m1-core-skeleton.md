# Milestone 1 后端核心骨架与配置边界 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立新的 `app/` 后端核心骨架，把配置、领域类型、模型 Provider 接口从 GUI 和旧模块中分离出来。

**Architecture:** 新代码先以适配层方式接入旧实现，不立即删除 `llm_adapters.py`、`config_manager.py`。Milestone 1 只建立边界和测试，使后续数据库、工作流、API 能依赖稳定接口。

**Tech Stack:** Python、Pydantic、pytest、现有模型适配代码。

---

## 文件结构

- Create: `app/__init__.py`
- Create: `app/domain/__init__.py`
- Create: `app/domain/models.py`
- Create: `app/config/__init__.py`
- Create: `app/config/settings.py`
- Create: `app/providers/__init__.py`
- Create: `app/providers/llm.py`
- Create: `tests/test_app_settings.py`
- Create: `tests/test_domain_models.py`
- Create: `tests/test_llm_provider.py`
- Modify: `AGENTS.md`

## Task 1: 创建领域模型

**Files:**
- Create: `app/domain/models.py`
- Test: `tests/test_domain_models.py`

- [ ] **Step 1: 写失败测试**

```python
from app.domain.models import ChapterStatus, ChapterDraft, GenerationJobStatus


def test_chapter_draft_requires_positive_chapter_number():
    try:
        ChapterDraft(project_id="p1", chapter_number=0, title="起点", content="")
    except ValueError as exc:
        assert "chapter_number" in str(exc)
    else:
        raise AssertionError("chapter_number=0 should fail")


def test_chapter_status_values_are_stable():
    assert ChapterStatus.DRAFT.value == "draft"
    assert ChapterStatus.FINALIZED.value == "finalized"
    assert GenerationJobStatus.RUNNING.value == "running"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_domain_models.py -v`

Expected: FAIL，提示 `ModuleNotFoundError: No module named 'app'` 或模型不存在。

- [ ] **Step 3: 实现最小领域模型**

```python
from dataclasses import dataclass
from enum import Enum


class ChapterStatus(str, Enum):
    PLANNED = "planned"
    OUTLINED = "outlined"
    DRAFT = "draft"
    FINALIZED = "finalized"


class GenerationJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True)
class ChapterDraft:
    project_id: str
    chapter_number: int
    title: str
    content: str
    status: ChapterStatus = ChapterStatus.DRAFT

    def __post_init__(self):
        if self.chapter_number < 1:
            raise ValueError("chapter_number must be >= 1")
        if not self.project_id.strip():
            raise ValueError("project_id must not be empty")
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_domain_models.py -v`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add app/domain tests/test_domain_models.py
git commit -m "feat(domain): 新增小说章节领域模型"
```

## Task 2: 建立配置读取边界

**Files:**
- Create: `app/config/settings.py`
- Test: `tests/test_app_settings.py`

- [ ] **Step 1: 写失败测试**

```python
import json

from app.config.settings import load_app_settings


def test_load_app_settings_reads_existing_config(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({
        "llm_configs": {
            "Local": {
                "api_key": "test-key",
                "base_url": "http://localhost:11434/v1",
                "model_name": "qwen2.5",
                "temperature": 0.2,
                "max_tokens": 4096,
                "timeout": 30,
                "interface_format": "OpenAI"
            }
        },
        "embedding_configs": {},
        "other_params": {"filepath": "/tmp/novel"}
    }), encoding="utf-8")

    settings = load_app_settings(config_path)

    assert settings.default_llm_name == "Local"
    assert settings.llm_configs["Local"].model_name == "qwen2.5"
    assert settings.output_path == "/tmp/novel"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_app_settings.py -v`

Expected: FAIL，提示 `app.config.settings` 不存在。

- [ ] **Step 3: 实现配置模型**

```python
import json
from pathlib import Path
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    api_key: str = ""
    base_url: str = ""
    model_name: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 600
    interface_format: str = "OpenAI"


class AppSettings(BaseModel):
    default_llm_name: str = ""
    llm_configs: dict[str, LLMConfig] = Field(default_factory=dict)
    output_path: str = ""


def load_app_settings(config_path: str | Path) -> AppSettings:
    path = Path(config_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    llm_configs = {
        name: LLMConfig(**value)
        for name, value in data.get("llm_configs", {}).items()
    }
    default_llm_name = next(iter(llm_configs), "")
    output_path = data.get("other_params", {}).get("filepath", "")
    return AppSettings(
        default_llm_name=default_llm_name,
        llm_configs=llm_configs,
        output_path=output_path,
    )
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_app_settings.py -v`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add app/config tests/test_app_settings.py
git commit -m "feat(config): 新增应用配置读取边界"
```

## Task 3: 建立 LLM Provider 协议和旧适配器桥接

**Files:**
- Create: `app/providers/llm.py`
- Test: `tests/test_llm_provider.py`

- [ ] **Step 1: 写失败测试**

```python
from app.providers.llm import LLMRequest, LegacyLLMProvider


class FakeLegacyAdapter:
    def __init__(self):
        self.prompt = None

    def invoke(self, prompt):
        self.prompt = prompt
        return "生成结果"


def test_legacy_provider_invokes_adapter():
    adapter = FakeLegacyAdapter()
    provider = LegacyLLMProvider(adapter)

    response = provider.generate(LLMRequest(prompt="写第一章"))

    assert adapter.prompt == "写第一章"
    assert response.text == "生成结果"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_llm_provider.py -v`

Expected: FAIL，提示 Provider 不存在。

- [ ] **Step 3: 实现 Provider 协议**

```python
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LLMRequest:
    prompt: str


@dataclass(frozen=True)
class LLMResponse:
    text: str


class LLMProvider(Protocol):
    def generate(self, request: LLMRequest) -> LLMResponse:
        ...


class LegacyLLMProvider:
    def __init__(self, adapter):
        self.adapter = adapter

    def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(text=self.adapter.invoke(request.prompt))
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_llm_provider.py -v`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add app/providers tests/test_llm_provider.py
git commit -m "feat(provider): 新增模型调用统一接口"
```

## Task 4: 更新项目协作说明

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: 写入架构计划位置说明**

在 `AGENTS.md` 的“项目说明”中追加：

```markdown
- 架构重构计划放在 `docs/superpowers/plans/`；主计划为 `2026-06-24-architecture-refactor.md`，执行时先读取主计划和对应 milestone 子计划。
```

- [ ] **Step 2: 检查说明**

Run: `rg "architecture-refactor" AGENTS.md docs/superpowers/plans`

Expected: 能看到主计划和 AGENTS 说明。

- [ ] **Step 3: 运行当前测试**

Run: `python -m pytest tests -v`

Expected: PASS。

- [ ] **Step 4: 提交**

```bash
git add AGENTS.md docs/superpowers/plans/2026-06-24-architecture-refactor*.md
git commit -m "docs(architecture): 新增重构主计划和第一阶段计划"
```

## Milestone 1 验收

- `app/domain`、`app/config`、`app/providers` 初始边界存在。
- 新代码有单元测试。
- 不影响 `python main.py`。
- 旧模型适配器仍可通过桥接方式复用。
