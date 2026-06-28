# 生成任务真实边界和日志体验

## Goal

完成旧任务 `06-27-frontend-ui-real-backend` 后续 Milestone 2：强化新前端“生成任务”页的真实后端边界、任务参数、章节缺失错误、`queued` 日志和任务详情体验，让用户明确知道当前前端只创建本地后端排队任务，不会调用真实 LLM，也不会修改小说文件。

本任务只处理生成任务壳层体验，不接入真实 LLM 执行器。

## Confirmed Facts

- 旧任务 `06-27-frontend-ui-real-backend` 已完成并归档，Milestone 2 规划为“强化任务创建参数、章节缺失错误、queued 日志和任务详情体验；不接入真实 LLM 执行器”。
- 前端生成页位于 `frontend/src/pages/GenerationPage.vue`，业务组件位于 `frontend/src/features/generation/`，状态由 `frontend/src/stores/generation.ts` 管理。
- 前端数据访问应继续通过 `frontend/src/services/serviceBridge.ts`；页面和 store 不应直接调用 `mockApi`。
- `app/api/server.py` 已提供 `POST /api/generation-jobs`、`GET /api/projects/{project_id}/jobs`、`GET /api/generation-jobs/{job_id}`。
- 生成任务接口支持 `architecture`、`directory`、`draft`、`finalization`、`consistency` 和 `batch`，返回 in-memory `queued` 任务与日志，尚未接入真实执行器。
- 后端对章节类任务已有校验：`draft`、`finalization`、`consistency` 需要目标 `chapter_X.txt` 存在，否则返回 `400 章节文件不存在`。
- 后端对批量任务已有校验：起止章节无效返回 `400 批量生成章节范围无效`，范围内缺章节返回 `400 章节文件不存在：N`。
- 现有生成页已显示“尚未接入真实 LLM 执行器”的 warning，并在 mock/断线模式下禁用创建任务。
- 现有生成页创建草稿/定稿/审校时使用项目配置中的 `chapterNum`，但页面没有把目标章节、章节文件存在性和后端错误前置成明确表单体验。
- 现有任务详情只展示阶段、进度、状态、错误和日志，缺少对 `queued` 状态含义、请求参数和不可执行边界的结构化说明。
- 验收文档 `docs/feature-map-and-acceptance.md` 已说明生成任务一直 `queued` 是当前预期行为。

## Requirements

- 生成页必须继续保留并强化当前能力边界：创建任务成功不等于真实生成成功，任务不会调用 LLM，不会修改小说文件。
- 创建草稿、定稿、审校任务前，页面应明确展示当前目标章节号，并在章节号缺失、无效或章节列表中不存在时给出可理解提示。
- 批量任务参数应在前端做基础校验：起始章节必须大于等于 1，结束章节不能小于起始章节，目标字数和最低字数不能为负数。
- 批量任务创建前应尽量基于当前章节列表提示范围内缺失的章节；最终以后端返回为准。
- 后端返回的生成任务错误应被翻译成用户可读消息，尤其是“不支持的生成阶段”“章节文件不存在”“批量生成章节范围无效”“章节文件不存在：N”。
- 任务列表和任务详情应让 `queued` 状态的含义更清楚：当前只是本地队列记录，等待未来执行器接入，不代表失败，也不会自动推进。
- 任务详情应展示和日志相关的关键上下文，例如阶段、状态、进度、项目、开始时间、错误和原始日志；如果后端日志包含输出路径、章节范围、字数参数，应保持可见。
- 保持生成任务写操作守卫：非 `backend` 模式下不能创建任务，不新增 mock 写入 fallback。
- 优先复用 `components/ui/` 与 `features/generation/` 现有组件；避免把任务卡片、日志、状态标签逻辑重复散落在页面内。
- 如页面行为或验收步骤变化，更新 `docs/feature-map-and-acceptance.md`。如发现新的可复用项目约定，更新根目录 `AGENTS.md`。

## Acceptance Criteria

- [x] 生成页显示当前执行边界：任务只会创建 `queued` 记录，尚未接入真实 LLM 执行器，不会生成或修改小说文件。
- [x] 草稿、定稿、审校任务创建前能看到目标章节号；章节号缺失、无效或章节文件不存在时，前端给出清晰提示，不让用户误解为生成失败。
- [x] 批量参数在前端有基础校验；起止章节无效、负数字数或范围缺章时显示清晰错误。
- [x] 真实后端下创建设定/目录任务仍能返回 `queued` 任务，并在详情日志中看到等待执行器接入的信息。
- [x] 真实后端下创建章节类任务时，缺失章节的错误展示为可理解中文提示。
- [x] 真实后端下创建批量任务时，成功任务详情能展示章节范围、目标字数、最低字数、自动扩写和后端日志。
- [x] mock/断线模式下生成任务创建入口不可用或提前提示不可写，不写入 mock。
- [x] `cd frontend && npm run typecheck` 通过。
- [x] `cd frontend && npm run build` 通过。
- [x] 后端生成任务相关测试通过，至少覆盖 `tests/test_api_generation_jobs.py` 和 `tests/test_api_batch_generation_jobs.py`。
- [x] 用临时输出目录完成生成页冒烟：设定/目录 queued、章节缺失错误、批量成功或缺章错误、离线禁写。

## Out of Scope

- 接入真实 LLM 生成执行器。
- 后台异步任务队列、轮询执行进度、暂停/恢复/取消任务。
- 修改旧 Python GUI 的生成流程。
- 改变 `config.json` schema 或小说输出文件格式。
- 将生成任务持久化到磁盘或数据库；当前仍使用后端 in-memory registry。
