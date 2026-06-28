# 前端真实可用能力续建 - Implementation Plan

## Checklist

- [x] 读取相关规格：backend、frontend、跨层指南和代码复用指南。
- [x] 扩展后端审校执行器：
  - [x] 在 `app/services/generation_executor.py` 引入 `check_consistency`。
  - [x] 将 `GenerationStage` 扩展到 `"consistency"`。
  - [x] 新增 `_run_consistency(...)`，读取设定、上下文和章节正文，调用旧审校函数并写日志。
  - [x] 增加只读文件读取 helper，避免重复散落 `Path.exists/read_text` 逻辑。
- [x] 扩展 API 调度：
  - [x] 将 `consistency` 加入 `EXECUTABLE_GENERATION_STAGES`。
  - [x] 保留章节不存在的 400 校验。
  - [x] 确认请求参数持久化和任务状态流转仍一致。
- [x] 更新前端生成页：
  - [x] 修改顶部状态提示，说明审校已接入真实执行器、批量仍待接入。
  - [x] 修改章节目标提示，让审校与定稿一样要求已有章节正文。
- [x] 更新测试：
  - [x] 为生成配置 helper 加入 `consistency_review_llm`。
  - [x] monkeypatch `check_consistency` 覆盖成功路径。
  - [x] 覆盖审校结果持久化、设定文件兼容、空章节失败、缺少审校 LLM 配置或 API Key 失败、只读不改文件。
  - [x] 调整旧 queued 审校断言为 done。
- [x] 更新文档：
  - [x] `docs/feature-map-and-acceptance.md` 中当前边界和开发顺序改为审校已接入、批量仍待接入。
  - [x] `AGENTS.md` 同步项目级可复用说明。
  - [x] `.trellis/spec/` 同步生成任务后端/前端执行器合同。
- [x] 运行验证：
  - [x] `PYTHONPATH=. .venv/bin/pytest tests -q`
  - [x] `cd frontend && npm run typecheck`
  - [x] `cd frontend && npm run build`

## Risky Files

- `app/api/server.py`：生成任务状态流转和执行阶段集合。
- `app/services/generation_executor.py`：真实执行器共享边界，错误处理会影响多个阶段。
- `tests/test_api_generation_jobs.py`：既有 queued 审校假设需要更新。
- `frontend/src/pages/GenerationPage.vue`：生成页文案和章节校验提示。

## Validation Notes

测试必须避免真实网络请求。所有审校 LLM 调用用 monkeypatch 替换 `app.services.generation_executor.check_consistency`。

## Rollback Points

- 如果审校执行器失败面过大，先只回退 `EXECUTABLE_GENERATION_STAGES` 中的 `"consistency"`，使 API 恢复 queued 行为。
- 如果前端文案导致验收混乱，同步回退 `GenerationPage.vue`、`docs/feature-map-and-acceptance.md` 和 `AGENTS.md`。
