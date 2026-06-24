# 小说生成器最佳架构重构 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将当前 `customtkinter` 单体桌面应用逐步重构为“本地优先、服务化核心、可恢复工作流、结构化存储、可替换 UI”的长期可维护架构。

**Architecture:** 采用渐进式重构：先建立独立后端核心与测试边界，再引入 SQLite 项目状态、工作流状态机、模型供应商接口，最后将 GUI 改为调用应用服务。旧 GUI 在迁移期间继续可运行，避免一次性大爆炸重写。

**Tech Stack:** Python 3.10-3.12、FastAPI、Pydantic、SQLModel/SQLAlchemy、SQLite、pytest、现有 LangChain/OpenAI/Gemini 依赖、后续可选 Tauri + React/Vue。

---

## 执行原则

- 本计划是总计划，只描述目标、顺序和验收标准；具体执行步骤见 milestone 子计划。
- 默认每轮只执行用户指定的 milestone，不要在未确认的情况下连续执行全部重构。
- 每个 milestone 完成后运行对应测试，并独立提交一次中文 Conventional Commit。
- 迁移期间保持 `python main.py` 仍可启动，除非用户明确批准切换入口。
- 不提交 `config.json`、真实 API Key、私有 Base URL、生成小说正文、向量库数据。

## Milestone 执行顺序

1. [Milestone 1: 后端核心骨架与配置边界](./2026-06-24-architecture-refactor-m1-core-skeleton.md)
2. [Milestone 2: SQLite 项目状态与仓储层](./2026-06-24-architecture-refactor-m2-sqlite-repositories.md)
3. [Milestone 3: 可恢复生成工作流](./2026-06-24-architecture-refactor-m3-workflows.md)
4. [Milestone 4: GUI 服务化迁移与本地 API](./2026-06-24-architecture-refactor-m4-ui-api-migration.md)

## 目标架构

```text
ui/ 或 frontend/
  ↓
app/api/                 # FastAPI 本地 API，供 GUI 或未来 Web/Tauri 调用
  ↓
app/services/            # 应用服务：项目、章节、配置、生成任务
  ↓
app/workflows/           # 可恢复状态机：设定、目录、章节、定稿、审校
  ↓
app/domain/              # 领域模型：项目、章节、角色状态、摘要、任务状态
  ↓
app/repositories/        # SQLite、文件导入导出、向量库访问
  ↓
app/providers/           # LLM / Embedding Provider 统一接口
```

## 非目标

- Milestone 1-4 不要求一次性替换所有 `customtkinter` 界面。
- 不在第一轮引入 Celery、Temporal、云端数据库或用户系统。
- 不强制删除旧 `novel_generator/`，先通过适配层逐步迁移。
- 不改变用户已有输出目录格式，先提供兼容导入/导出。

## 总体验收标准

- `python main.py` 在迁移期间仍能启动。
- `python -m pytest tests` 通过。
- 新增核心模块有单元测试覆盖。
- 章节生成流程的关键状态可持久化、可查询、可恢复。
- 模型调用、配置读取、文件存储、向量库访问不再直接散落在 GUI 回调中。

## 自检记录

- 计划已按 4 个 milestone 拆分，每个 milestone 2-4 个任务。
- 本主计划不包含超过 12 个任务，详细步骤下沉到子计划。
- 所有 milestone 都能独立测试和独立提交。
