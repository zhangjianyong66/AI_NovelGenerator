# 前端章节草稿与定稿真实可用技术设计

## Summary

本轮只实现单章 `draft` 和单章 `finalization` 的同步真实执行。继续沿用上一任务建立的本地 FastAPI `POST /api/generation-jobs` 和 in-memory job registry，不引入持久化任务、后台队列或轮询。核心设计目标是让新前端能真实推进当前章节，同时兼容旧 GUI 的 `chapters/chapter_X.txt` 文件约定。

## Architecture

扩展现有执行器边界：

```text
app/api/server.py
  POST /api/generation-jobs
    ↓
app/services/generation_executor.py
  run_generation_job(config, stage, output_path, request context)
    ↓
legacy functions
  generate_chapter_draft(...)
  finalize_chapter(...)
  enrich_chapter_text(...)
```

`app/api/server.py` 继续负责：

- Pydantic request/response。
- 任务对象创建、状态更新、日志追加。
- 对不支持 stage 的基础校验。
- 对 `batch` 和 `consistency` 保持现有未接入边界。

`generation_executor.py` 负责：

- 阶段 LLM 配置解析与校验。
- Embedding 配置解析与默认值处理。
- 章节号、目录文件、章节正文等前置条件校验。
- 调用旧章节生成/定稿函数。
- 同步 `chapters/chapter_X.txt` 与根部 `chapter_X.txt`。
- 返回 `done` / `failed`、日志和错误。

## File Compatibility

当前存在两套章节文件路径：

- 新前端/API：`<output>/chapter_X.txt`
- 旧 GUI/legacy 函数：`<output>/chapters/chapter_X.txt`

本轮采用兼容同步策略：

1. 草稿生成前不要求根部 `chapter_X.txt` 或 `chapters/chapter_X.txt` 已存在。
2. `generate_chapter_draft(...)` 生成后会写入 `chapters/chapter_X.txt`。
3. 执行器检查 `chapters/chapter_X.txt` 非空，并复制到根部 `chapter_X.txt`。
4. 定稿前以根部 `chapter_X.txt` 为前端权威输入；如果根部文件存在且非空，先同步到 `chapters/chapter_X.txt`，再调用 `finalize_chapter(...)`。
5. 定稿后再把 `chapters/chapter_X.txt` 同步回根部 `chapter_X.txt`，保证前端读取最新正文。

这样旧 GUI 继续使用 `chapters/`，新前端继续使用根部文件，短期不改变任一侧读取约定。

## Data Flow

### Draft

1. 前端调用 `createGenerationJob({ stage: 'draft', chapterNumber })`。
2. API 创建任务，状态置为 `running`。
3. 执行器读取：
   - `other_params.filepath`
   - `other_params.word_number`
   - `other_params.user_guidance`
   - `other_params.characters_involved`
   - `other_params.key_items`
   - `other_params.scene_location`
   - `other_params.time_constraint`
   - `choose_configs.prompt_draft_llm`
   - 选中的 Embedding 配置或可用默认 Embedding 配置
4. 执行器确认 `Novel_directory.txt` 非空，因为旧草稿提示词依赖章节目录。
5. 调用 `generate_chapter_draft(...)`。
6. 将 `chapters/chapter_X.txt` 同步到根部 `chapter_X.txt`。
7. 任务置为 `done`，日志记录目标章节和文件。

### Finalization

1. 前端调用 `createGenerationJob({ stage: 'finalization', chapterNumber })`。
2. 执行器确认根部 `chapter_X.txt` 存在且非空。
3. 将根部正文同步到 `chapters/chapter_X.txt`。
4. 读取 `choose_configs.final_chapter_llm` 和 Embedding 配置。
5. 如果请求传入 `autoEnrich=true` 且章节字数低于 `minimumWords`，可先调用 `enrich_chapter_text(...)` 并写回双路径；当前前端单章定稿不主动传该参数，默认不扩写。
6. 调用 `finalize_chapter(...)`，更新 `global_summary.txt`、`character_state.txt`，并沿用旧逻辑尝试更新 `vectorstore/`。
7. 将 `chapters/chapter_X.txt` 同步回根部 `chapter_X.txt`。
8. 任务置为 `done`。

## Request Contract

复用现有 `GenerationJobCreateRequest`：

- `stage='draft' | 'finalization'`
- `chapterNumber` 可选；缺省时使用 `config.json` 的 `other_params.chapter_num`。
- `autoEnrich`、`minimumWords`、`targetWords` 仅作为可选扩写参数，不要求前端本轮暴露新 UI。

本轮不新增自定义提示词字段。旧 GUI 的提示词预览/编辑能力留到后续增强。

## Error Handling

返回策略沿用设定/目录任务：尽量返回 200 + `status='failed'` 的任务对象，让前端任务列表可看到失败记录；明显非法 stage 继续 422，`batch` 参数错误继续 400。

关键失败消息：

- 未填写当前章节号：`章节号必须大于 0`
- 草稿缺少目录：`请先生成章节目录`
- 草稿 LLM 未选择或缺 API Key：`生成章节草稿未选择 LLM 配置` / `LLM 配置缺少 API Key：...`
- 定稿缺少章节正文：`请先生成或保存章节正文`
- 定稿 LLM 未选择或缺 API Key：对应中文提示。
- 草稿生成空内容：`章节草稿生成结果为空`

日志不得输出 API Key、完整私有凭据或长篇正文。

## Frontend Behavior

`GenerationPage.vue` 更新为：

- 顶部提示说明设定、目录、草稿、定稿已接入真实执行器。
- 审校和批量仍提示后续接入。
- 草稿任务只要求当前章节号有效，不再要求根部 `chapter_X.txt` 已存在。
- 定稿任务要求当前章节文件存在且非空。
- 成功创建草稿或定稿后重新加载章节列表，使新生成章节能立即用于后续校验。

不新增页面结构，不做视觉重构。

## Testing Strategy

后端测试：

- monkeypatch `generate_chapter_draft(...)`，写入 `chapters/chapter_1.txt`，证明 API 返回 `done` 且根部 `chapter_1.txt` 被同步。
- monkeypatch `finalize_chapter(...)`，写入或更新 `global_summary.txt`、`character_state.txt`，证明任务 `done`。
- 覆盖草稿缺少目录失败。
- 覆盖草稿缺少 API Key 失败。
- 覆盖定稿缺少章节正文失败。
- 保留 `consistency`、`batch` 未接入边界。

前端验证：

- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`

全量验证：

- `python -m pytest tests`
- `git diff --check`

## Trade-offs

- 同步执行简单可测，但长 LLM 请求会阻塞 HTTP 请求；任务持久化和后台执行留到后续 milestone。
- 双路径同步有重复文件风险，但它是当前最小兼容方案；一次性迁移旧 GUI 或前端文件约定会扩大范围。
- 不做提示词预览编辑，牺牲旧 GUI 的一部分交互能力，换取前端章节生成闭环先落地。
- 不更新 `plot_arcs.txt`，因为当前旧定稿函数没有稳定实现；文档需明确该能力仍待后续补齐。

## Rollback

回滚顺序：

1. 从 `EXECUTABLE_GENERATION_STAGES` 移除 `draft`、`finalization`，恢复壳任务。
2. 回退执行器对章节阶段的新增调用和同步逻辑。
3. 回退前端提示与校验文案。

回滚不得删除用户输出目录中已经生成的章节、摘要、角色状态或向量库文件。
