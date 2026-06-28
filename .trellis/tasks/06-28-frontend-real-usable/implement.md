# 前端项目真实可用实施计划

## Scope

本轮只执行 Milestone 1：真实生成执行器最小闭环。

不要继续实现：

- 章节草稿/定稿/审校真实执行。
- 任务 SQLite 持久化。
- 后台队列或可恢复工作流。
- 知识库真实向量化。
- 项目管理和章节生命周期。

## Pre-Implementation Checklist

- [x] 用户审阅并确认 `prd.md`、`design.md`、`implement.md`。
- [x] 运行 `git status --short`，确认当前未提交变更范围。
- [x] 读取相关 Trellis spec：
  - `.trellis/spec/backend/index.md`
  - `.trellis/spec/backend/directory-structure.md`
  - `.trellis/spec/backend/persistence-and-config.md`
  - `.trellis/spec/backend/error-handling.md`
  - `.trellis/spec/backend/quality-guidelines.md`
  - `.trellis/spec/backend/logging-guidelines.md`
  - `.trellis/spec/guides/index.md`
- [x] 使用 `trellis-before-dev` 后再开始写代码。

## Task 1: 后端生成执行器边界

- [x] 新增 `app/services/` 包。
- [x] 新增 `app/services/generation_executor.py`。
- [x] 定义执行结果结构，至少包含 `status`、`progress`、`log`、`error`。
- [x] 实现从 legacy `config.json` 读取阶段 LLM 配置的 helper：
  - `architecture` 使用 `choose_configs.architecture_llm`。
  - `directory` 使用 `choose_configs.chapter_outline_llm`。
  - LLM 配置来自 `llm_configs`。
- [x] 校验输出目录、题材、类型、章节数、每章字数、API Key、模型名等关键字段。
- [x] 实现 `architecture` 执行：
  - 调用 `Novel_architecture_generate(...)`。
  - 检查 `Novel_architecture.txt` 非空。
  - 同步到 `Novel_setting.txt`。
- [x] 实现 `directory` 执行：
  - 确保 `Novel_architecture.txt` 可用；必要时从 `Novel_setting.txt` 同步。
  - 调用 `Chapter_blueprint_generate(...)`。
  - 检查 `Novel_directory.txt` 非空。

## Task 2: API 接入真实执行器

- [x] 修改 `app/api/server.py` 的 `create_generation_job`。
- [x] 对 `architecture` 和 `directory`：
  - 创建任务后置为 `running`。
  - 调用执行器。
  - 根据结果更新为 `done` 或 `failed`。
  - 保留 in-memory registry。
- [x] 对 `draft`、`finalization`、`consistency`、`batch` 保持现有壳任务边界，不扩大范围。
- [x] 确保日志包含输出路径、阶段、目标文件和完成/失败原因。
- [x] 避免日志输出 API Key、完整私有凭据或长篇正文。

## Task 3: 后端测试

- [x] 新增或更新 `tests/test_api_generation_jobs.py`。
- [x] 用 monkeypatch fake 掉 legacy 生成函数，避免真实 LLM 调用。
- [x] 覆盖 architecture 成功：
  - API 返回 `done`。
  - `Novel_architecture.txt` 和 `Novel_setting.txt` 非空。
- [x] 覆盖 directory 成功：
  - API 返回 `done`。
  - `Novel_directory.txt` 非空。
- [x] 覆盖缺少 API Key：
  - API 返回任务 `failed`。
  - `error` 或日志为中文可操作提示。
- [x] 覆盖 directory 缺少设定文件：
  - API 返回任务 `failed`。
  - 不静默创建空目录。
- [x] 保留或调整现有 queued 断言，使未接入阶段仍符合预期。

## Task 4: 前端提示与任务详情

- [x] 修改 `frontend/src/pages/GenerationPage.vue`：
  - 移除“所有任务只创建排队任务”的全局绝对提示。
  - 改为说明设定/目录已接入真实执行器，章节类和批量仍待后续接入。
- [x] 修改 `frontend/src/features/generation/components/GenerationJobDetail.vue`：
  - `queued` 提示只描述等待状态。
  - 不再断言任务不会调用 LLM 或写文件。
  - `done` / `failed` 主要依赖状态、错误和日志。
- [x] 如有必要，更新生成任务列表状态颜色或标签，但不做视觉重构。

## Task 5: 文档同步

- [x] 更新 `docs/feature-map-and-acceptance.md`：
  - 标记设定/目录阶段已经接入真实执行器。
  - 保留草稿、定稿、审校、批量仍未接入的边界。
  - 更新无 API Key 和真实 LLM 验收说明。
- [x] 如发现新的运行约定，更新 `AGENTS.md`。

## Validation

必须运行：

```bash
python -m pytest tests
cd frontend && npm run typecheck
cd frontend && npm run build
git diff --check
```

结果：

- [x] `.venv/bin/python -m pytest tests` 通过，50 passed，2 warnings。
- [x] `cd frontend && npm run typecheck` 通过。
- [x] `cd frontend && npm run build` 通过。
- [x] `git diff --check` 通过。

建议手工冒烟：

```bash
./scripts/dev.sh
```

手工验收重点：

- 设置有效 LLM 后，从前端创建“设定”任务能生成设定文件。
- 再创建“目录”任务能生成 `Novel_directory.txt`。
- 无 API Key 时返回失败任务和清晰提示。
- 章节类任务仍不被误描述为已真实接入。

## Risk And Rollback

- 风险：同步 LLM 调用耗时较长，前端按钮会等待请求结束。
  - 缓解：本轮只做设定/目录最小闭环；后续 milestone 再做任务持久化和后台执行。
- 风险：`Novel_architecture.txt` 与 `Novel_setting.txt` 双文件同步产生概念重复。
  - 缓解：本轮明确作为兼容层；后续服务化时统一命名。
- 风险：旧生成函数失败时可能只返回空文件而不抛异常。
  - 缓解：执行器必须检查目标文件非空。

回滚：

- 回退 `app/services/generation_executor.py` 和 `app/api/server.py` 的真实执行接入。
- 回退前端提示文案。
- 不删除用户输出目录中的生成文件。
