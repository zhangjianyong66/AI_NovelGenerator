# 补齐前端真实创作能力

## Goal

让新前端从“单章真实创作闭环”继续推进到更完整的真实创作工具，优先补齐两个仍未完成的关键能力：

- 批量生成真实执行：批量任务不再只是 `queued` 记录，而是按章节范围执行真实草稿/定稿链路并记录每章结果。
- 项目级配置隔离：切换项目时，项目参数和必要配置不再相互污染，减少多个小说项目共用根目录 `config.json` 导致的误写风险。

这两个能力可独立验收，计划拆成父任务下的子任务推进：先完成批量生成真实执行最小闭环，再进入项目级配置隔离。

## Confirmed Facts

- `docs/feature-map-and-acceptance.md` 记录：设定、目录、单章草稿、单章定稿、一致性审校、知识库向量化和项目管理最小闭环已完成；批量生成和项目配置隔离仍是后续真实能力。
- `app/api/server.py` 当前在 `POST /api/generation-jobs` 中只把 `architecture`、`directory`、`draft`、`finalization`、`consistency` 交给 `run_generation_job(...)`；`batch` 走 `else` 分支，只追加“任务已创建，等待执行器接入”。
- `tests/test_api_batch_generation_jobs.py` 当前断言批量接口创建批量任务、记录章节范围和参数、校验无效范围、校验缺失章节，但没有真实执行断言。
- `frontend/src/pages/GenerationPage.vue` 当前明确提示“批量阶段仍处于后续接入范围，当前只创建任务记录”，并在前端校验批量范围内章节文件存在。
- `app/services/generation_executor.py` 当前 `GenerationStage` 不包含 `batch`，但已有 `_run_draft(...)`、`_run_finalization(...)` 和章节同步工具，可作为批量执行的基础。
- `app/api/server.py` 当前项目配置、模型设置、WebDAV、知识库、章节和生成任务均围绕根目录 `config.json` 的 `other_params.filepath` 和当前输出路径工作；项目切换会直接修改根目录 `config.json.other_params.filepath`。
- `.local/state.sqlite3` 当前保存生成任务历史和最近项目索引，不保存项目参数、模型配置或密钥。

## Requirements

- R1: 批量生成真实执行应从前端现有批量参数触发，使用 `startChapter`、`endChapter`、`targetWords`、`minimumWords`、`autoEnrich`。
- R2: 批量任务应为每个章节写入可读日志，包含开始、成功、失败、跳过原因和最终汇总。
- R3: 批量任务第一版执行“批量定稿”最小闭环：要求范围内 `chapter_X.txt` 已存在且非空，逐章复用单章 `finalization` 链路；不在第一版自动生成缺失草稿。
- R4: 批量任务遇到单章失败时继续处理后续章节；最终日志汇总成功/失败章节，存在任一失败则任务整体标记为 `failed`。
- R5: 项目级配置隔离应避免切换项目时覆盖其他项目的题材、类型、章节数、当前章节、写作约束等项目参数。
- R6: 项目级配置隔离第一版只隔离项目参数和输出目录；LLM、Embedding、代理、WebDAV、API Key 继续全局共享并保存在根目录 `config.json`。
- R7: 实现必须继续兼容旧 Python GUI 使用根目录 `config.json` 的方式，不能破坏 `python main.py`。
- R8: 真实写操作仍必须通过本地后端完成；后端不可用时前端保持离线预览和写入禁用。

## Acceptance Criteria

- [ ] 批量生成任务不再停留在 `queued`/“等待执行器接入”；有效配置下会进入 `running` 并最终变为 `done` 或 `failed`。
- [ ] 批量任务日志包含章节范围、目标字数、最低字数、自动扩写设置和逐章执行结果。
- [ ] 批量任务会逐章执行真实定稿链路，范围内成功章节的 `chapter_X.txt`、`global_summary.txt`、`character_state.txt` 按现有定稿逻辑更新。
- [ ] 批量任务部分章节失败时，后续章节仍会尝试执行；任务最终状态为 `failed`，错误摘要说明成功章节和失败章节。
- [ ] 批量任务缺少 LLM 配置、缺少目录、缺少章节文件、章节为空等前置条件失败时返回中文错误并持久化到任务日志。
- [ ] 前端生成页不再提示批量阶段只创建任务记录，并能展示批量真实执行状态。
- [ ] 项目切换后，项目 A 和项目 B 的项目参数互不覆盖；切回项目 A 能读回 A 自己的参数。
- [ ] 模型配置、密钥、代理和 WebDAV 不做项目级隔离；切换项目后仍读取全局配置。
- [ ] 根目录 `config.json` 仍可作为旧 GUI 的当前活动配置使用。
- [ ] 新增或调整的后端行为有 pytest 覆盖；前端服务桥或页面边界有轻量契约测试覆盖。

## Out of Scope

- 不在本任务内实现完整后台队列、并发执行、暂停/恢复或任务重试。
- 不在本任务内重写旧 GUI。
- 不提交 `config.json`、API Key、真实账号、真实 WebDAV 密码、向量库或大体积小说输出。

## Open Questions

- 无。
