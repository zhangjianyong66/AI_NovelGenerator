# 补齐前端真实创作能力执行计划

## 1. 批量定稿真实执行

- [x] 更新 `app/services/generation_executor.py`：
  - [x] 将 `GenerationStage` 扩展为包含 `batch`。
  - [x] 给 `run_generation_job(...)` 增加 `start_chapter`、`end_chapter` 参数。
  - [x] 新增 `_run_batch_finalization(...)`，逐章复用 `_run_finalization(...)`。
  - [x] 单章失败继续后续章节，最终按成功/失败汇总返回。
- [x] 更新 `app/api/server.py`：
  - [x] 将 `batch` 纳入 `EXECUTABLE_GENERATION_STAGES`。
  - [x] 调用 `run_generation_job(...)` 时传入批量范围。
  - [x] 保留范围和缺失章节校验。
- [x] 更新 `tests/test_api_batch_generation_jobs.py`：
  - [x] 批量任务真实执行并变为 `done`。
  - [x] 单章失败后继续处理后续章节，最终 `failed` 且日志有汇总。
  - [x] 缺失章节和无效范围仍按现有错误返回。
- [x] 更新 `frontend/src/pages/GenerationPage.vue`：
  - [x] 删除“只创建任务记录”提示。
  - [x] 改为说明批量第一版执行已有章节定稿。
- [x] 更新前端契约测试。

## 2. 项目参数隔离

- [x] 更新 `app/services/project_store.py`：
  - [x] 增加项目参数快照 JSON 字段迁移。
  - [x] 增加保存/读取项目参数快照的方法。
  - [x] 保持已有项目列表和最近项目行为兼容。
- [x] 更新 `app/api/server.py`：
  - [x] 抽取项目参数快照序列化/合并工具。
  - [x] `GET /api/projects` 同步当前项目快照，并用非活动项目快照生成摘要。
  - [x] `POST /api/projects` 新建项目时写入该项目参数快照。
  - [x] `POST /api/projects/switch` 切换前保存当前项目参数，切换后恢复目标项目参数到根 `config.json`。
  - [x] `PUT /api/project-config` 保存根配置时同步当前项目快照。
- [x] 更新或新增 pytest：
  - [x] 项目 A/B 切换后各自题材、类型、章节数、当前章节保持隔离。
  - [x] 模型设置仍全局共享，不随项目切换改变。
  - [x] 旧配置和旧 SQLite 无快照字段时仍可启动和切换。

## 3. 文档与项目说明

- [x] 更新 `docs/feature-map-and-acceptance.md`：
  - [x] 批量生成状态从“待接入”改为“批量定稿真实执行第一版”。
  - [x] 记录项目参数隔离边界：参数隔离、模型/密钥全局共享。
- [x] 如本轮形成新的运行约定，更新根目录 `AGENTS.md`。

## 4. 验证

- [x] `.venv/bin/python -m pytest tests`
- [x] `cd frontend && npm run typecheck`
- [x] `cd frontend && npm run build`
- [x] 如类型检查依赖缺失，先报告缺失情况，不提交 `node_modules/`。本轮依赖可用，无需报告缺失。

## Rollback Points

- 批量定稿主要集中在 `generation_executor.py` 和 `server.py`，可独立回退而不影响项目参数隔离。
- 项目参数隔离涉及 SQLite 迁移和切换语义，实施前应保证批量定稿测试已通过。
- 不迁移密钥和模型配置，避免回滚时出现密钥位置不明确。
