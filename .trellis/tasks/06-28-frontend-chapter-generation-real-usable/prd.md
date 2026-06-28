# 前端章节草稿与定稿真实可用

## Goal

让新 Tauri/Vue 前端的章节类生成从“只创建任务记录”推进到“能真实生成和更新章节文件”的本地创作闭环。第一轮建议聚焦当前章节的草稿生成和定稿：用户在前端选择当前章节后，可以触发后端复用旧生成逻辑生成章节草稿，并通过定稿更新全局摘要、角色状态和向量库。

用户价值：用户完成设定和目录生成后，不必回到旧 Python GUI 才能推进到章节正文；前端至少能完成“当前章节草稿 -> 编辑 -> 定稿”的最小写作循环。

## Confirmed Facts

- 上一任务 `06-28-frontend-real-usable` 已完成设定和目录真实生成执行器，`app/services/generation_executor.py` 当前只支持 `architecture` 和 `directory`。
- `POST /api/generation-jobs` 当前支持 `architecture`、`directory`、`draft`、`finalization`、`consistency` 和 `batch`；其中只有 `architecture`、`directory` 会进入真实执行器，其余阶段只创建 `queued` 壳任务。
- API 当前要求 `draft`、`finalization`、`consistency` 的目标 `chapter_X.txt` 必须已存在；`batch` 也要求范围内章节文件已存在。这与“生成草稿时创建章节文件”的用户目标冲突。
- 新前端/API 当前读取和保存章节文件的位置是输出目录根部的 `chapter_X.txt`。
- 旧 GUI 的章节生成函数 `novel_generator.chapter.generate_chapter_draft(...)` 会写入输出目录下 `chapters/chapter_X.txt`，不是根部 `chapter_X.txt`。
- 旧 GUI 的定稿函数 `novel_generator.finalization.finalize_chapter(...)` 也读取 `chapters/chapter_X.txt`，并更新 `global_summary.txt`、`character_state.txt`，同时尝试更新 `vectorstore/`。
- 旧 GUI 的定稿入口会先把编辑器里的章节正文写入 `chapters/chapter_X.txt`，字数不足时可调用 `enrich_chapter_text(...)` 扩写，再调用 `finalize_chapter(...)`。
- 旧一致性审校逻辑在 `consistency_checker.py::check_consistency(...)`，返回审校文本，不会修改章节文件、摘要、角色状态或 `plot_arcs.txt`。
- 现有代码没有发现直接维护 `plot_arcs.txt` 的旧生成函数；README 和文档提到定稿会更新剧情要点，但当前 `finalize_chapter(...)` 未写入该文件。
- 前端 `GenerationPage.vue` 当前明确提示草稿、定稿、审校和批量仍处于后续接入范围，并在创建章节类任务前检查根部 `chapter_X.txt` 是否存在。
- 前端章节编辑页 `ChaptersPage.vue` 当前只显示输出目录根部已有的 `chapter_X.txt`。
- 前端任务创建请求类型已有 `chapterNumber`、`startChapter`、`endChapter`、`targetWords`、`minimumWords` 和 `autoEnrich`，但没有自定义提示词或直接提交当前编辑器正文的字段。

## Requirements

- R1. 章节类真实执行仍必须通过 `POST /api/generation-jobs` 进入，前端不直接调用旧生成函数。
- R2. 后端执行器边界应从现有设定/目录扩展到章节阶段，API 层继续负责请求校验、任务状态和日志。
- R3. 草稿任务应能在目标章节文件不存在时执行，并在成功后让前端章节列表和章节编辑页可读取生成结果。
- R4. 草稿任务必须使用当前项目配置中的输出目录、当前章节号、每章字数、用户指导、章节要素、草稿阶段 LLM 配置和 Embedding 配置。
- R5. 定稿任务必须以当前章节正文为输入，更新前端可读取的 `chapter_X.txt`，并复用旧定稿逻辑更新 `global_summary.txt`、`character_state.txt`，可尝试更新 `vectorstore/`。
- R6. 由于旧函数使用 `chapters/chapter_X.txt`，本任务必须明确根部 `chapter_X.txt` 与 `chapters/chapter_X.txt` 的同步策略，保证旧 GUI 和新前端都能看到同一章节结果。
- R7. 缺少目录、缺少目标章节号、缺少 LLM 配置、缺少 API Key、缺少模型名、生成结果为空等情况必须返回 `failed` 任务或清晰 4xx 错误，并带中文日志/提示。
- R8. 任务日志必须说明目标章节、输出路径、读写文件、执行阶段、完成结果或失败原因。
- R9. 本轮不应引入 SQLite、后台队列、Celery、Redis、Temporal 或跨进程任务恢复；仍保持同步执行和 in-memory job registry。
- R10. 测试必须隔离真实外部 LLM/Embedding 调用，通过 monkeypatch/fake 函数覆盖成功路径和关键错误路径。
- R11. 不提交 `config.json`、API Key、私有 Base URL、生成小说正文、`vectorstore/` 或前端构建产物。

## Scope

- 包含：单章 `draft` 真实草稿生成。
- 包含：单章 `finalization` 真实定稿，必要时支持 `autoEnrich` 触发扩写。
- 包含：生成后同步根部 `chapter_X.txt` 与旧函数目录 `chapters/chapter_X.txt`，让前端和旧 GUI 兼容。
- 包含：前端生成页文案、章节存在性校验和任务详情提示更新。
- 已确认：本轮只做单章草稿和单章定稿，一致性审校与批量生成留到后续独立任务。
- 暂不包含：`consistency` 真实审校。
- 暂不包含：`batch` 真实批量生成。
- 暂不包含：`plot_arcs.txt` 自动生成或更新，除非在设计阶段找到稳定旧函数或明确新增最小机制。
- 暂不包含：前端提示词预览/编辑弹窗。
- 暂不包含：任务持久化和后台异步执行。

## Acceptance Criteria

- [ ] 创建 `draft` 任务时，即使根部 `chapter_1.txt` 不存在，只要项目设定、目录和配置满足要求，后端会调用章节草稿执行边界并生成可被 `GET /api/projects/current/chapters` 读取的章节。
- [ ] 草稿成功后，根部 `chapter_1.txt` 和兼容目录 `chapters/chapter_1.txt` 的同步策略可被测试证明。
- [ ] 创建 `finalization` 任务时，后端会以当前章节正文执行定稿，并更新 `global_summary.txt` 和 `character_state.txt`；测试中通过 fake 函数证明任务状态为 `done`。
- [ ] 缺少章节目录、缺少草稿阶段 API Key、缺少定稿阶段 API Key、草稿生成空内容等错误会产生 `failed` 任务或清晰 4xx，并带中文错误。
- [ ] 前端生成页不再要求草稿任务预先存在 `chapter_X.txt`；定稿仍应要求目标章节有正文。
- [ ] 前端生成页能区分已接入真实执行器的草稿/定稿，以及仍未接入的审校/批量。
- [ ] `cd frontend && npm run typecheck` 通过。
- [ ] `cd frontend && npm run build` 通过。
- [ ] `python -m pytest tests` 通过，或记录明确的环境阻塞。
- [ ] `docs/feature-map-and-acceptance.md` 和必要的 `AGENTS.md` 更新章节类真实可用边界。

## Out Of Scope

- 不实现一致性审校真实执行。
- 不实现批量章节真实生成。
- 不实现任务持久化与可恢复工作流。
- 不实现后台异步队列或轮询进度。
- 不实现知识库真实向量化导入；定稿只沿用旧 `finalize_chapter(...)` 中已有的向量库更新尝试。
- 不新增项目管理、章节生命周期数据库或章节状态持久化。
- 不重做前端视觉结构。
