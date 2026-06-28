# 前端章节草稿与定稿真实可用实施计划

## Scope

本轮只执行单章草稿和单章定稿真实闭环。

不要继续实现：

- 一致性审校真实执行。
- 批量章节真实生成。
- 任务持久化或后台队列。
- 提示词预览/编辑弹窗。
- `plot_arcs.txt` 自动更新。
- 项目管理或章节状态数据库。

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
  - `.trellis/spec/frontend/index.md`
  - `.trellis/spec/frontend/service-bridge-real-backend.md`
  - `.trellis/spec/frontend/component-guidelines.md` 当前不存在
  - `.trellis/spec/frontend/state-and-data.md` 当前不存在
  - `.trellis/spec/guides/index.md`
- [x] 使用 `trellis-before-dev` 后再开始写代码。

## Task 1: 扩展后端执行器

- [x] 扩展 `app/services/generation_executor.py` 的 `GenerationStage`，加入 `draft` 和 `finalization`。
- [x] 调整 `run_generation_job(...)` 入参，使章节阶段能接收 `chapterNumber`、`autoEnrich`、`minimumWords`、`targetWords`。
- [x] 新增章节路径 helper：
  - 根部章节：`output_path / f"chapter_{chapter}.txt"`
  - legacy 章节：`output_path / "chapters" / f"chapter_{chapter}.txt"`
  - 双路径同步 helper。
- [x] 新增草稿阶段执行：
  - 解析 `choose_configs.prompt_draft_llm`。
  - 解析 Embedding 配置。
  - 校验章节号、`Novel_directory.txt`、字数和 LLM 配置。
  - 调用 `generate_chapter_draft(...)`。
  - 检查 `chapters/chapter_X.txt` 非空。
  - 同步到根部 `chapter_X.txt`。
- [x] 新增定稿阶段执行：
  - 解析 `choose_configs.final_chapter_llm`。
  - 解析 Embedding 配置。
  - 校验章节号和根部章节正文。
  - 定稿前同步根部章节到 `chapters/chapter_X.txt`。
  - 可选处理 `autoEnrich`。
  - 调用 `finalize_chapter(...)`。
  - 定稿后同步 legacy 章节到根部章节。
- [x] 确保日志包含目标章节、输出路径和目标文件，不泄露密钥或长正文。

## Task 2: API 接入章节执行器

- [x] 修改 `app/api/server.py` 的 `EXECUTABLE_GENERATION_STAGES`，加入 `draft` 和 `finalization`。
- [x] 修改章节阶段前置校验：
  - `draft` 不再要求根部章节文件已存在。
  - `finalization` 仍要求章节文件存在且非空，或交由执行器返回 failed 任务。
  - `consistency` 维持当前未接入边界。
- [x] 调用执行器时传入章节任务上下文。
- [x] 保留 `batch` 当前壳任务和范围校验，不扩大真实执行范围。
- [x] 创建任务成功或失败后都写入 in-memory registry，方便前端查看日志。

## Task 3: 后端测试

- [x] 更新 `tests/test_api_generation_jobs.py`。
- [x] 新增 fake `generate_chapter_draft(...)`，写入 `chapters/chapter_1.txt`。
- [x] 新增 fake `finalize_chapter(...)`，写入 `global_summary.txt` 和 `character_state.txt`。
- [x] 覆盖草稿成功：
  - API 返回 `done`。
  - 根部 `chapter_1.txt` 和 `chapters/chapter_1.txt` 均非空。
  - `GET /api/projects/current/chapters` 能读到章节。
- [x] 覆盖定稿成功：
  - API 返回 `done`。
  - `global_summary.txt` 和 `character_state.txt` 更新。
- [x] 覆盖草稿缺少 `Novel_directory.txt` 失败。
- [x] 覆盖草稿缺少 API Key 失败。
- [x] 覆盖定稿缺少章节正文失败。
- [x] 调整现有 “chapter stage queued” 断言，使 `draft/finalization` 已真实执行，`consistency` 仍是未接入边界。
- [x] 保持 `tests/test_api_batch_generation_jobs.py` 对批量壳任务的断言。

## Task 4: 前端生成页更新

- [x] 修改 `frontend/src/pages/GenerationPage.vue` 顶部能力提示：
  - 设定、目录、草稿、定稿已接入真实执行器。
  - 审校和批量仍待后续接入。
- [x] 修改章节目标校验：
  - 草稿只要求当前章节号有效。
  - 定稿和审校要求章节文件存在；审校仍提示未接入。
- [x] 创建草稿或定稿任务成功后重新加载章节列表。
- [x] 批量校验保持现状，不扩大实现。
- [x] 如需调整任务详情文案，只改状态语义，不做视觉重构。

## Task 5: 文档同步

- [x] 更新 `docs/feature-map-and-acceptance.md`：
  - 草稿和定稿标记为已接入真实执行器。
  - 审校和批量仍保持后续范围。
  - 明确章节文件双路径兼容策略。
  - 明确 `plot_arcs.txt` 暂不自动更新。
- [x] 如新增或确认项目运行约定，更新 `AGENTS.md`。

## Validation

必须运行：

```bash
python -m pytest tests
cd frontend && npm run typecheck
cd frontend && npm run build
git diff --check
```

如本地 Python 环境需要项目虚拟环境，优先使用 `.venv/bin/python -m pytest tests`。

结果：

- [x] `.venv/bin/python -m pytest tests` 通过，55 passed，2 warnings。
- [x] `cd frontend && npm run typecheck` 通过。
- [x] `cd frontend && npm run build` 通过。
- [x] `git diff --check` 通过。

建议手工冒烟：

```bash
./scripts/dev.sh
```

手工验收重点：

- 设置有效 LLM 后，从前端生成第 1 章草稿，章节编辑页能看到 `chapter_1.txt`。
- 编辑并保存章节后，创建定稿任务，`global_summary.txt` 和 `character_state.txt` 有更新。
- 无 API Key 时返回失败任务和清晰中文提示。
- 审校和批量仍不被误描述为已真实接入。

## Risk And Rollback

- 风险：旧函数写 `chapters/`，前端读根部，双路径同步可能造成用户误判哪个文件是最新。
  - 缓解：定稿前以根部文件为权威输入，定稿后同步回根部；文档记录兼容策略。
- 风险：同步 LLM 调用耗时较长。
  - 缓解：本轮只做单章，后续任务持久化时再迁移后台执行。
- 风险：Embedding 配置缺失导致草稿检索或定稿向量库更新失败。
  - 缓解：草稿阶段尽量传入可用默认值；定稿沿用旧函数内部向量库更新失败降级为 warning 的行为。

回滚：

- 从可执行阶段集合移除 `draft` 和 `finalization`。
- 回退执行器新增章节逻辑和前端校验文案。
- 不删除用户输出目录中已生成或更新的章节文件。
