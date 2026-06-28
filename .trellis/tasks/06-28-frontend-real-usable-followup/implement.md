# 前端任务持久化与可恢复工作流执行计划

## 执行范围

本轮只执行任务持久化最小闭环，不继续知识库真实向量化、项目管理、章节生命周期、真实审校或真实批量生成。

## Checklist

- [x] 1. 更新持久化规范与忽略规则
  - 在 `.trellis/spec/backend/database-guidelines.md` 记录本轮 SQLite 任务状态库的真实边界。
  - 确认 `.gitignore` 忽略 `.local/` 或等价状态目录。

- [x] 2. 增加后端任务仓储
  - 新增 `app/services/generation_job_store.py`。
  - 使用标准库 `sqlite3` 初始化 `generation_jobs` 表和项目/更新时间索引。
  - 提供保存、列表、详情读取函数，输入输出使用普通 dict，避免与 API model 循环依赖。

- [x] 3. 接入 FastAPI 生成任务接口
  - `create_app` 增加可选 `state_db_file` 参数。
  - 用任务仓储替换内存 `generation_jobs` 字典。
  - 创建任务时先保存 queued 记录，真实执行阶段保存 running 和最终结果。
  - 列表和详情接口改为从仓储读取。

- [x] 4. 补充后端测试
  - queued 任务在重建 app/client 后仍可列表和详情读取。
  - 已接入真实执行器的成功任务会持久化 `done`、进度、日志和错误空值。
  - 已接入真实执行器的失败任务会持久化 `failed`、中文错误和日志。
  - 确认测试使用临时数据库路径。

- [x] 5. 更新前端生成页提示与必要契约测试
  - 生成页说明任务历史保存在本地状态库。
  - 不改写 `serviceBridge` 写操作边界，不直接调用 `mockApi`。
  - 如源码契约测试需要，补充任务持久化文案或加载路径断言。

- [x] 6. 更新项目说明与验收文档
  - 更新 `docs/feature-map-and-acceptance.md` 中任务持久化状态。
  - 更新 `AGENTS.md` 中本地 API 生成任务存储边界和 `.local/` 注意事项。

- [x] 7. 验证
  - `python -m pytest tests`
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run build`
  - 检查 `git status --short`，确认未提交 `config.json`、`.local/`、输出目录、前端构建产物。

## 风险文件

- `app/api/server.py`：生成任务接口从内存字典切换到持久化仓储，需避免破坏已有同步执行语义。
- `tests/test_api_generation_jobs.py`：现有测试默认同一 app 内读写任务，需要扩展跨 app 重建场景。
- `frontend/src/pages/GenerationPage.vue`：只做小文案/状态增强，避免扩大 UI 重构。
- `.trellis/spec/backend/database-guidelines.md`：本轮会把“当前无数据库”的规范更新为“仅生成任务状态库使用 SQLite”。

## 验收重点

- 后端重启等价测试：创建任务后销毁 TestClient，重新 `create_app(config_file=..., state_db_file=...)`，任务仍存在。
- 已接入执行器最终状态必须保存，而不是只保存初始 queued。
- 失败任务必须可恢复查看中文错误。
- 未接入执行器的 `consistency` 和 `batch` 仍是 queued，不误标真实执行。

## 回滚点

- 若 SQLite 仓储接入导致生成任务测试大面积失败，先回退 `app/api/server.py` 中的仓储替换，保留仓储模块和测试作为后续修复依据。
- 删除 `.local/state.sqlite3` 只会清空任务历史，不影响小说输出文件。
