# 前端真实可用能力续建

## Goal

继续把新 Tauri/Vue 前端推进为真实创作工具。本轮聚焦“一致性审校真实执行”最小闭环：用户在前端为当前章节创建审校任务时，后端不再只保存 queued 任务记录，而是复用旧 `consistency_checker.py::check_consistency(...)` 调用 LLM，读取当前项目设定、角色状态、全局摘要、剧情要点和章节正文，把审校结果写入任务日志并持久化到 `.local/state.sqlite3`。

用户价值：用户完成草稿或定稿后，可以直接在新前端检查章节与设定、角色状态、前文摘要和未解决剧情要点是否冲突，不必回到旧 Python GUI 才能完成基础审校。

## Confirmed Facts

- `docs/feature-map-and-acceptance.md` 记录当前真实能力边界：设定、目录、单章草稿、单章定稿、任务持久化、知识向量化、项目管理和章节生命周期最小闭环已完成；一致性审校和批量生成仍只创建任务记录。
- `app/api/server.py` 当前支持 `architecture`、`directory`、`draft`、`finalization`、`consistency` 和 `batch` 任务阶段。
- `app/api/server.py` 中 `EXECUTABLE_GENERATION_STAGES` 仅包含 `architecture`、`directory`、`draft`、`finalization`；`consistency` 当前通过章节存在性校验后保存 queued 任务，并追加“等待执行器接入”日志。
- `app/services/generation_executor.py` 已封装真实执行器边界，当前 `GenerationStage` 只覆盖 `architecture`、`directory`、`draft`、`finalization`。
- `consistency_checker.py::check_consistency(...)` 接收 `novel_setting`、`character_state`、`global_summary`、`chapter_text`、`plot_arcs` 和 LLM 参数，返回审校文本，不修改小说文件。
- 模型设置中已有 `choose_configs.consistency_review_llm`，前端设置页也已有“一致性审校”阶段模型选择。
- 前端 `GenerationPage.vue` 已把 `consistency` 作为章节类任务，要求当前章节号有效且根部 `chapter_X.txt` 存在。
- 前端生成页当前提示“审校和批量阶段仍处于后续接入范围，当前只创建任务记录”。
- 生成任务历史、日志、错误和创建请求参数已通过 `GenerationJobStore` 持久化到本地 SQLite 状态库，后端重启后仍可读取。

## Requirements

- R1. `consistency` 任务必须继续通过 `POST /api/generation-jobs` 创建，前端不直接调用旧审校函数。
- R2. 后端应把 `consistency` 纳入 `app/services/generation_executor.py` 的真实执行器边界，保持 API 层负责请求校验、任务状态、日志和持久化。
- R3. 审校任务必须读取当前输出目录下的 `Novel_setting.txt`，若不存在可兼容读取 `Novel_architecture.txt`；还应读取 `character_state.txt`、`global_summary.txt`、`plot_arcs.txt` 和根部 `chapter_X.txt`，缺失的辅助文件按空文本传入，章节正文必须非空。
- R4. 审校任务必须使用 `choose_configs.consistency_review_llm` 选择 LLM 配置，并沿用现有 LLM 配置校验：配置不存在、API Key 为空、模型名为空或接口格式为空时返回 failed 任务和中文错误。
- R5. 审校任务成功后状态为 `done`、进度为 `100`，任务日志必须包含目标章节、读取上下文说明和审校结果摘要或全文；审校结果需能在任务详情中查看。
- R6. 审校任务不应修改 `chapter_X.txt`、`global_summary.txt`、`character_state.txt`、`plot_arcs.txt` 或 `vectorstore/`。
- R7. 章节号缺失、章节文件不存在继续返回清晰 4xx；章节文件存在但内容为空时应创建任务并得到 `failed` 状态与中文错误，便于持久化错误日志。
- R8. 前端生成页文案必须更新为：设定、目录、草稿、定稿和审校已接入真实执行器；批量仍处于后续接入范围。
- R9. 任务日志与前端展示不新增新的 API 响应字段，避免扩大跨层契约；审校结果先作为 log 条目保存。
- R10. 本轮不引入后台队列、轮询进度、任务重试按钮或新的审校结果文件。
- R11. 测试必须隔离真实外部 LLM 调用，通过 monkeypatch/fake 函数覆盖成功路径和关键错误路径。
- R12. 不提交 `config.json`、API Key、私有 Base URL、生成小说正文、`vectorstore/`、`.local/` 或前端构建产物。

## Acceptance Criteria

- [ ] 创建 `consistency` 任务时，后端会调用真实审校执行边界，读取当前章节和上下文文件，成功后任务状态为 `done`、进度为 `100`、错误为空。
- [ ] 审校结果出现在任务日志中，并能通过 `GET /api/generation-jobs/{job_id}` 和重启后的任务详情读取。
- [ ] `Novel_setting.txt` 缺失但 `Novel_architecture.txt` 存在时，审校仍可执行；两者都缺失时任务 `failed` 并提示需要先准备小说设定。
- [ ] `chapter_X.txt` 缺失时仍返回 `400 章节文件不存在`；`chapter_X.txt` 为空时返回 `200` 的 failed 任务并记录中文失败原因。
- [ ] 缺少 `consistency_review_llm` 选择、缺少 API Key 或缺少模型名时，审校任务 `failed` 并记录中文错误。
- [ ] 审校成功路径不会修改章节正文、摘要、角色状态或剧情要点文件。
- [ ] 前端生成页不再提示审校未接入；批量仍明确显示为后续接入范围。
- [ ] `python -m pytest tests` 通过，或记录明确环境阻塞。
- [ ] `cd frontend && npm run typecheck` 通过。
- [ ] `cd frontend && npm run build` 通过。
- [ ] `docs/feature-map-and-acceptance.md` 与必要的 `AGENTS.md` 更新审校真实可用边界。

## Out Of Scope

- 不实现 `batch` 真实批量生成。
- 不新增审校结果文件、审校历史表、冲突状态字段或章节生命周期数据库。
- 不实现后台异步队列、轮询进度、任务取消或重试。
- 不修改旧 GUI 的审校入口。
- 不调整审校 prompt 或设计新的多 Agent 审校流程。
- 不扩大前端视觉重构范围。
