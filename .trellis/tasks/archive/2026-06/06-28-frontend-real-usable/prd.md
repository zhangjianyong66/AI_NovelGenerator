# 前端项目真实可用

## Goal

让已重构的 Tauri/Vue 前端从“可编辑工作台 + 生成任务壳层”推进到“可真实触发小说生成”的本地创作工具。首轮应优先完成最小真实生成闭环：用户在前端配置项目和 LLM 后，可以创建“生成小说设定”和“生成章节目录”任务，后端真实调用生成逻辑并把结果写入输出目录。

用户价值：用户不再需要回到旧 Python GUI 才能完成最前置的创作流程；前端至少能从空项目参数推进到可编辑的小说设定和章节目录。

## Confirmed Facts

- 新前端已经能通过 `frontend/src/services/serviceBridge.ts` 真实读写本地 API；读类接口允许 mock fallback，保存/导入/生成等写操作要求真实后端。
- 本地 API 入口是 `app/api/server.py`，当前 `POST /api/generation-jobs` 只创建 in-memory `queued` 任务，并写入“等待执行器接入”日志，不会调用 LLM 或修改小说文件。
- 前端生成页 `frontend/src/pages/GenerationPage.vue` 已明确提示当前生成任务尚未接入真实 LLM 执行器。
- 现有旧生成模块包含可复用函数：
  - `novel_generator/architecture.py::Novel_architecture_generate(...)`
  - `novel_generator/blueprint.py::Chapter_blueprint_generate(...)`
- 旧架构生成函数当前最终写入 `Novel_architecture.txt`，并生成 `character_state.txt`；新前端核心项目文件接口当前固定读取 `Novel_setting.txt`、`Novel_directory.txt`、`character_state.txt`、`global_summary.txt`。
- `Chapter_blueprint_generate(...)` 依赖输出目录已有非空 `Novel_architecture.txt`，并写入 `Novel_directory.txt`。
- 项目已有路线文档 `docs/feature-map-and-acceptance.md`，其中“新前端真实可用开发顺序”把真实生成执行器最小闭环列为第一优先级。
- 当前工作区已有未提交文档变更：`AGENTS.md` 和 `docs/feature-map-and-acceptance.md`，内容是记录前端真实可用开发顺序。
- 用户已确认本轮只实现“生成小说设定 + 生成章节目录”的同步真实执行闭环，先不做章节生成和任务持久化。

## Scope For This Task

本任务整体目标较大，需要按 milestone 执行。本轮只覆盖 Milestone 1：真实生成执行器最小闭环。

Milestone 1 包含：

- “生成小说设定”任务真实执行，并写入前端可读取的设定文件。
- “生成章节目录”任务真实执行，并写入 `Novel_directory.txt`。
- 生成任务状态不再永远停留在 `queued`，至少能在同步执行完成后返回 `done`，失败时返回 `failed` 和中文错误日志。
- 前端生成页移除或改写“尚未接入真实执行器”的绝对提示，改为根据阶段/状态呈现真实能力边界。
- 保持旧 GUI `python main.py` 可运行。

后续 milestone 暂不在本轮实现，但应在设计中预留边界：

- 章节草稿与定稿闭环。
- 任务持久化与可恢复工作流。
- 知识库真实向量化与检索。
- 项目管理能力。
- 章节生命周期补齐。

## Requirements

- R1. 真实生成任务必须继续通过 `POST /api/generation-jobs` 创建，前端不直接调用旧生成函数。
- R2. API 层不得复制 LLM 调用细节；应通过小的执行器/service 边界封装从 legacy `config.json` 到旧生成函数参数的映射。
- R3. 生成小说设定必须使用当前项目配置中的输出目录、题材、类型、章节数、每章字数、用户指导和已选阶段模型配置。
- R4. 生成章节目录必须在设定生成完成后可执行；如果缺少所需设定文件，应返回清晰中文错误，而不是静默生成空任务。
- R5. 生成结果必须能被前端现有工作台/核心文件接口读到。若旧函数继续产出 `Novel_architecture.txt`，必须明确是否同步/复制到 `Novel_setting.txt`。
- R6. 任务日志必须说明真实执行开始、输出路径、目标文件、完成或失败原因。
- R7. 无有效 LLM 配置或缺少 API Key 时，任务应失败并返回可操作中文错误，不应假装成功。
- R8. 测试必须覆盖成功路径的执行器调度边界和关键错误路径；真实外部 LLM 调用应可通过 monkeypatch/fake executor 隔离。
- R9. 不提交 `config.json`、API Key、私有 Base URL、生成小说正文、`vectorstore/` 或前端构建产物。

## Acceptance Criteria

- [x] 创建 `architecture` 生成任务时，后端会调用真实执行器边界；测试中可用 fake 函数证明输出文件被写入，任务状态为 `done`。
- [x] 创建 `directory` 生成任务时，后端会在存在设定文件的前提下调用目录生成边界；测试中可证明 `Novel_directory.txt` 被写入，任务状态为 `done`。
- [x] 缺少 LLM 配置、缺少 API Key、缺少设定文件等错误会返回 `failed` 任务或 4xx 错误，并带中文日志/提示。
- [x] 前端生成页不再把所有生成任务都描述为“只创建排队任务”；对已接入的设定/目录阶段展示真实执行状态，对未接入阶段保留边界提示。
- [x] `cd frontend && npm run typecheck` 通过。
- [x] `cd frontend && npm run build` 通过。
- [x] `python -m pytest tests` 通过，或记录明确的环境阻塞。
- [x] 文档更新后，`docs/feature-map-and-acceptance.md` 能区分已接入真实执行器的阶段和仍未接入的阶段。

## Out Of Scope For Milestone 1

- 不实现章节草稿、章节定稿、一致性审校和批量生成的真实 LLM 执行。
- 不引入 SQLite 任务持久化。
- 不实现后台异步队列、Celery、Redis、Temporal 或跨进程任务恢复。
- 不实现知识库真实向量化。
- 不替换或删除旧 Python GUI。
- 不重做前端视觉结构。

## Notes

- 本任务属于复杂任务，进入实现前必须补充 `design.md` 和 `implement.md`，并经用户确认后再 `task.py start`。
