# 生成任务真实边界和日志体验 - 技术设计

## Scope

本设计覆盖生成任务页 Milestone 2：任务创建参数、章节缺失错误、`queued` 语义、日志详情和验收文档。范围集中在 `frontend/src/pages/GenerationPage.vue`、`frontend/src/features/generation/`、`frontend/src/stores/generation.ts`、必要的类型/helper，以及已有后端生成任务接口的小幅校验或测试补强。

不接入真实 LLM 执行器，不实现后台任务调度，不持久化任务。

## Approach

采用“前端前置校验 + 后端错误兜底 + 日志详情解释”的方案。

- 前端根据项目配置和章节列表推导目标章节与批量范围风险，先给出可操作提示。
- 后端仍是最终事实来源，接口返回的错误继续展示给用户。
- `queued` 状态在任务列表和详情中解释为“已记录，等待执行器接入”，避免被误认为已生成成功或任务卡住。
- 成功任务详情保留原始后端日志，同时增加结构化元信息，便于用户检查输出路径、章节范围和字数参数。

该方案比扩展后端执行器更小，符合 Milestone 2 的边界，也能让当前真实后端壳层更容易验收。

## Data Flow

1. 进入生成页：
   - `projectsStore.loadProjects()` 加载当前项目。
   - `generationStore.loadJobs(activeProjectId)` 加载现有 in-memory 任务。
   - 新增或复用读路径加载项目配置与章节列表，用于显示当前章节号和批量缺章提示。
2. 创建核心任务：
   - `architecture` / `directory` 不需要章节文件。
   - `draft` / `finalization` / `consistency` 使用项目配置 `chapterNum` 作为目标章节。
   - 前端在章节号无效或章节列表不包含该章节时阻止提交并展示提示。
   - 提交后端时仍带 `chapterNumber`，后端缺章错误继续兜底。
3. 创建批量任务：
   - 前端校验 `startChapter`、`endChapter`、`targetWords`、`minimumWords`。
   - 前端基于已加载章节列表列出缺失章节；存在缺失时阻止提交或明确提示。
   - 后端成功返回的日志中保留章节范围、字数和自动扩写设置。
4. 展示任务：
   - `GenerationJobList` 继续负责列表和状态标签。
   - `GenerationJobDetail` 负责结构化元信息、状态解释、错误、日志。

## Frontend Boundaries

### `GenerationPage.vue`

- 作为编排层：加载项目配置、章节列表、任务列表，持有批量表单和页面级错误。
- 不直接操作 `mockApi`。
- 非 `backend` 模式下沿用 `serviceBridge.canWrite()` 禁用创建入口。
- 提供清晰的 `validationMessage`，区分前端参数错误和后端请求错误。

### `features/generation`

- `GenerationActions` 可继续只接收 `disabled`，也可以扩展为按动作禁用/提示，但优先保持 API 简洁。
- `GenerationJobList` 增加 queued 的副信息或 tooltip 文案时，应保持卡片高度稳定，避免列表跳动。
- `GenerationJobDetail` 增加状态说明、项目/开始时间等元信息和日志空态，不承接网络请求。

### `generation` Store

- 继续只负责 `listGenerationJobs` 和 `createGenerationJob`。
- 如需要刷新单个任务，可封装 `getGenerationJob`，但本任务不需要轮询。

## Backend Boundaries

`app/api/server.py` 当前已有本任务所需的核心校验。后端改动只在必要时进行：

- 保持 `queued`、`progress=0`、等待执行器接入日志。
- 保持章节缺失和批量范围错误的中文 `detail`。
- 如前端需要更稳定的错误展示，可补充测试而不是改变响应 schema。

## UI Behavior

- 顶部 warning 继续说明“尚未接入真实 LLM 执行器”。
- 任务创建区域显示当前目标章节：
  - 有效：例如“章节类任务将使用 chapter_1.txt”。
  - 无效：例如“当前章节号为空或不是正整数，请先在设置页填写当前章节”。
  - 缺章：例如“当前输出目录没有 chapter_3.txt，请先在章节编辑或旧 GUI 中准备章节文件”。
- 批量参数区域显示范围检查结果：
  - 成功：展示将覆盖的章节范围。
  - 缺章：展示缺失章节号。
  - 参数错误：展示具体字段问题。
- 任务详情在 `queued` 时展示说明：任务已记录在本地后端内存队列，等待未来执行器接入；当前不会自动推进或写文件。

## Error Handling

- 前端校验错误不发请求。
- 写操作不可用错误使用 `serviceBridge.getWriteUnavailableMessage()`。
- 后端错误优先展示 `detail`，再回退到 `message` 或默认“创建任务失败”。
- 对常见后端错误给出行动建议：
  - `章节文件不存在`：准备对应 `chapter_X.txt`。
  - `批量生成章节范围无效`：检查起止章节。
  - `不支持的生成阶段`：这是前端/后端版本不匹配，需要报告。

## Validation

- `python -m pytest tests/test_api_generation_jobs.py tests/test_api_batch_generation_jobs.py`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`
- 本地冒烟：
  - 临时输出目录含 `chapter_1.txt`。
  - 设置当前章节为 `1`，创建草稿任务，确认 `queued` 和等待执行器日志。
  - 设置当前章节为不存在章节，确认前端或后端显示缺章错误。
  - 批量 `1-1` 成功，批量 `1-2` 在缺 `chapter_2.txt` 时显示缺章错误。
  - 停止后端或使用不可用 API 地址，确认生成入口禁用。

## Rollback

- 前端改动集中在生成页和生成 feature 组件，可单独回退。
- 后端如果只补测试，无运行时回滚风险。
- 不修改数据文件格式、配置 schema 或真实生成流程。
