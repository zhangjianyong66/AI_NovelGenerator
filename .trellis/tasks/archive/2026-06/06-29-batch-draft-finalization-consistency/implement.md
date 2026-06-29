# 支持批量草稿定稿审校实现计划

## 执行范围

本轮只实现批量草稿、批量定稿、批量审校的最小闭环，不做后台 worker、任务重试、章节状态持久化。

## 步骤

- [x] 确认批量草稿遇到已有章节文件时的默认策略：跳过并记录日志，不覆盖正文。
- [x] 扩展后端 stage 常量和请求处理：
  - 新增 `batchDraft`、`batchFinalization`、`batchConsistency`。
  - 保留 `batch` 兼容为批量定稿。
  - 提取批量范围校验和缺章节校验 helper。
- [x] 扩展执行器：
  - 新增通用批量循环 helper。
  - 实现批量草稿调用 `_run_draft`。
  - 将现有批量定稿迁移到通用 helper。
  - 实现批量审校调用 `_run_consistency`。
- [x] 扩展后端测试：
  - 批量草稿成功创建缺失章节文件。
  - 批量草稿部分失败后继续。
  - 批量定稿继续兼容旧 `batch`，新增 `batchFinalization`。
  - 批量审校成功写入日志且不修改项目文件。
  - 批量审校缺章节返回中文 400。
- [x] 扩展前端类型和动作组件：
  - `GenerationStage` 增加三个明确批量 stage。
  - 生成动作组件显示 `批量草稿`、`批量定稿`、`批量审校`。
  - 任务详情 stage 标签增加新阶段。
- [x] 调整生成任务页：
  - 批量参数标题和说明改为通用文案。
  - 批量草稿不因缺章节文件阻止提交。
  - 批量定稿/审校保持缺章节提示。
  - 批量草稿/定稿完成后刷新章节上下文。
- [x] 更新文档：
  - `docs/feature-map-and-acceptance.md`
  - `AGENTS.md`
  - 必要时更新 Trellis spec 中生成任务合同。
- [x] 验证：
  - `python -m pytest tests/test_api_generation_jobs.py tests/test_api_batch_generation_jobs.py tests/test_frontend_service_bridge_contract.py`
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run build`
  - 如时间允许，运行 `python -m pytest tests`

## 风险与回滚点

- `app/api/server.py` 当前已有未提交改动，实现前必须重新读取并只做最小补丁，避免覆盖用户改动。
- 批量草稿如果默认覆盖已有章节，误操作风险高；建议默认跳过已有章节。
- 同步执行器仍会阻塞请求，批量章节范围过大时前端等待时间会很长；这属于后续“后台任务执行”范围。
