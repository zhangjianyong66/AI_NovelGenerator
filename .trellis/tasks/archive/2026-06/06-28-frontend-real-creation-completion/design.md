# 补齐前端真实创作能力技术设计

## Architecture

本任务包含两个可独立验收的交付：

1. 批量定稿真实执行。
2. 项目参数隔离。

批量定稿优先实现，作为当前前端生成任务的直接补强。项目参数隔离在批量定稿完成后实施，避免生成执行器变更和配置持久化变更相互干扰。

## 批量定稿真实执行

### 边界

- `batch` 第一版语义固定为“批量定稿”，不自动生成缺失草稿。
- 输入继续使用现有 `GenerationJobCreateRequest` 字段：`startChapter`、`endChapter`、`targetWords`、`minimumWords`、`autoEnrich`。
- 后端继续通过 `POST /api/generation-jobs` 同步执行，不引入后台队列、暂停、恢复或重试。
- 范围内章节文件必须存在且非空。空章节按该章失败处理；前端仍保留现有缺失文件预校验。

### 后端数据流

1. `app/api/server.py` 将 `batch` 纳入可执行阶段。
2. `app/services/generation_executor.py` 扩展 `GenerationStage` 支持 `batch`。
3. `run_generation_job(...)` 接收批量范围参数并调用 `_run_batch_finalization(...)`。
4. `_run_batch_finalization(...)` 逐章调用现有 `_run_finalization(...)`，为每章追加独立日志。
5. 单章失败时捕获异常，记录失败章节和原因，继续处理后续章节。
6. 所有章节处理结束后：
   - 全部成功：返回 `done`，`progress=100`。
   - 存在失败：返回 `failed`，`progress` 可按成功比例或 100 记录，`error` 包含成功/失败摘要。

### 文件影响

批量定稿成功的章节沿用单章定稿副作用：

- 同步根部 `chapter_X.txt` 和 legacy `chapters/chapter_X.txt`。
- 更新 `global_summary.txt`。
- 更新 `character_state.txt`。
- 沿用旧逻辑尝试更新向量库。

失败章节不应阻止后续章节尝试执行。

### 前端影响

`frontend/src/pages/GenerationPage.vue` 删除“批量阶段只创建任务记录”的提示，改为说明批量第一版执行“已有章节批量定稿”。现有批量参数表单、缺失章节校验和任务日志展示继续复用。

## 项目参数隔离

### 边界

第一版只隔离项目参数和输出目录：

- `filepath`
- `topic`
- `genre`
- `num_chapters`
- `word_number`
- `chapter_num`
- `user_guidance`
- `characters_involved`
- `key_items`
- `scene_location`
- `time_constraint`

以下配置保持全局共享：

- `llm_configs`
- `embedding_configs`
- `choose_configs`
- `proxy_setting`
- `webdav_config`
- API Key 和密码字段

### 持久化策略

扩展 `app/services/project_store.py` 的 `recent_projects` 记录，增加项目参数快照字段。可选实现为单个 JSON 字段 `params_json`，保存上述项目参数。原因：

- 避免 SQLite 表字段过多。
- 便于兼容后续参数扩展。
- 不存密钥，风险低。

### 切换项目数据流

1. 在切换离开当前项目前，将当前根 `config.json.other_params` 的项目参数保存到当前项目的 `params_json`。
2. 切换到目标项目时：
   - 如果目标项目已有 `params_json`，把该快照合并回根 `config.json.other_params`，并确保 `filepath` 指向目标输出目录。
   - 如果目标项目没有快照，保留目标路径，并从当前请求或现有输出目录推导最小标题/类型信息。
3. 根 `config.json` 始终代表“当前活动项目配置”，保证旧 GUI 继续读取同一文件。
4. `GET /api/project-config` 继续读取根 `config.json`，但根配置会在切换时被目标项目参数刷新。
5. `PUT /api/project-config` 保存当前活动项目参数时，同时更新根 `config.json` 和当前项目的参数快照。

### 项目列表影响

`GET /api/projects` 对非活动项目可从项目快照读取标题、类型、章节数，避免只显示路径或错误沿用当前项目参数。章节完成数仍从对应输出目录即时扫描。

## Compatibility

- 旧 GUI 不需要知道 SQLite 项目快照；它继续读写根目录 `config.json`。
- 如果用户通过旧 GUI 修改当前项目参数，新前端下一次调用项目列表或切换前会把根 `config.json` 当前参数同步回当前项目快照。
- 已有 `.local/state.sqlite3` 缺少新字段时，`ProjectStore` 初始化时通过迁移补齐。
- 删除 `.local/state.sqlite3` 只会丢失最近项目和参数快照，不会删除小说输出文件或根 `config.json`。

## Error Handling

- 批量范围无效继续返回 400。
- 批量缺少章节文件继续在 API 层提前返回 400。
- 单章定稿执行中的 LLM、文件、配置错误被记录到该章节日志；批量继续执行后续章节。
- 项目快照 JSON 解析失败时，应降级为空快照并继续使用根 `config.json`，不阻塞应用启动。

## Testing

- 后端 pytest 覆盖批量定稿全成功、部分失败继续执行、缺少章节/空章节错误日志。
- 后端 pytest 覆盖项目切换保存和恢复不同项目参数。
- 前端契约测试覆盖生成页不再声明批量未接入，并说明批量定稿边界。
- 运行 `python -m pytest tests`。
- 运行 `cd frontend && npm run typecheck`。
