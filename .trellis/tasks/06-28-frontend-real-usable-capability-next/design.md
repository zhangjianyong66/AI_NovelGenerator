# 前端真实可用能力续建 - Design

## Architecture

本轮沿用已有同步执行器架构：`POST /api/generation-jobs` 创建任务并持久化初始状态，进入 `app/services/generation_executor.py::run_generation_job(...)` 执行真实阶段，执行结果再回写 `GenerationJobStore`。`consistency` 只加入同一执行器边界，不新增路由、不新增响应字段、不新增数据库表。

审校结果先作为任务日志保存。这样能复用当前前端任务详情的日志展示与 SQLite 持久化，避免本轮为了一个只读审校结果扩展新表、新文件或前端数据契约。

## Data Flow

1. 前端生成页创建 `stage: "consistency"` 任务，继续传当前章节号。
2. API 层校验阶段名和目标章节文件是否存在；章节不存在仍返回 `400 章节文件不存在`。
3. API 创建 `queued` 任务并保存请求参数；如果阶段属于可执行集合，则改为 `running` 并调用 `run_generation_job(...)`。
4. 执行器读取当前输出目录：
   - 小说设定：优先 `Novel_setting.txt`，兼容 `Novel_architecture.txt`。
   - 章节正文：根部 `chapter_X.txt`，必须非空。
   - 角色状态、全局摘要、剧情要点：分别读取 `character_state.txt`、`global_summary.txt`、`plot_arcs.txt`，缺失视为空。
5. 执行器用 `choose_configs.consistency_review_llm` 查找 LLM 配置，调用 `check_consistency(...)`。
6. 执行器把审校结果追加到日志，返回 `done`；失败则返回 `failed` 和中文错误。
7. API 持久化最终任务，前端现有任务详情显示日志。

## Contracts

- `GenerationStage` 扩展为包含 `"consistency"`。
- `EXECUTABLE_GENERATION_STAGES` 扩展为包含 `"consistency"`。
- `consistency` 使用的配置键为 `consistency_review_llm`，阶段标签为“一致性审校”。
- 审校结果不作为单独字段返回；任务日志是本轮唯一跨层展示载体。
- `character_state.txt`、`global_summary.txt`、`plot_arcs.txt` 可缺失；`Novel_setting.txt` / `Novel_architecture.txt` 和 `chapter_X.txt` 不能为空。

## Compatibility

旧 GUI 的审校函数不被修改。新前端仍读取根部章节文件，和当前章节接口保持一致。任务历史存储仍使用现有 `GenerationJobStore` 的 `log_json` 字段；后端重启后可通过已有详情接口读到审校结果。

## Error Handling

API 前置错误保持用于“请求本身不可成立”的场景：阶段不支持、章节号无效或章节文件不存在。

执行器错误用于“任务可创建但执行失败”的场景：小说设定为空、章节正文为空、审校 LLM 未选择、配置缺 API Key、配置缺模型名、审校函数返回空白或抛异常。这些错误应变成 `failed` 任务并写入日志，便于用户在任务历史中回看失败原因。

## Trade-Offs

- 选择任务日志承载审校结果：实现小、兼容现有 UI 和持久化；代价是后续如果要做结构化冲突列表，需要再新增审校结果模型。
- 选择同步执行：与设定、目录、草稿、定稿保持一致；代价是长 LLM 请求仍会阻塞 HTTP 请求。后台队列留给后续统一任务执行改造。
- 选择只读审校：避免把审校与正文修订、剧情要点更新耦合；代价是用户需要手动根据审校结果修改章节。

## Rollback

若审校接入导致任务创建回归，可从 `EXECUTABLE_GENERATION_STAGES` 移除 `"consistency"` 并保留 `GenerationStage` 类型回退，任务会恢复为 queued 壳任务。前端文案和文档需同步回退。
