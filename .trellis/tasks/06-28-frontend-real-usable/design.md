# 前端项目真实可用技术设计

## Summary

本轮只实现 Milestone 1：前端“生成小说设定”和“生成章节目录”能通过本地 FastAPI 触发真实后端执行，并在请求返回时得到 `done` 或 `failed` 状态。实现采用同步执行，不引入 SQLite、后台队列或任务恢复；但执行器边界要独立，方便后续替换为持久化工作流。

## Architecture

新增一个轻量后端执行边界，建议放在 `app/services/generation_executor.py`：

```text
app/api/server.py
  POST /api/generation-jobs
    ↓
app/services/generation_executor.py
  run_generation_job(config, stage, output_path)
    ↓
legacy novel_generator functions
  Novel_architecture_generate(...)
  Chapter_blueprint_generate(...)
```

`app/api/server.py` 继续拥有 HTTP request/response、Pydantic schema、in-memory job registry 和基础参数校验；执行器负责：

- 从 legacy `config.json` 解析阶段模型选择。
- 校验所需 LLM 配置、API Key、模型名、输出目录和项目参数。
- 调用旧生成函数。
- 检查输出文件是否存在且非空。
- 返回状态、进度、日志和错误消息。

## Data Flow

### Architecture Stage

1. 前端调用 `serviceBridge.createGenerationJob({ stage: 'architecture' })`。
2. API 创建 `GenerationJob`，状态先置为 `running`，日志写入开始信息。
3. 执行器读取：
   - `other_params.filepath`
   - `other_params.topic`
   - `other_params.genre`
   - `other_params.num_chapters`
   - `other_params.word_number`
   - `other_params.user_guidance`
   - `choose_configs.architecture_llm`
   - `llm_configs[architecture_llm]`
4. 调用 `Novel_architecture_generate(...)`。
5. 旧函数产出 `Novel_architecture.txt` 和 `character_state.txt`。
6. 为兼容新前端核心项目文件，执行器把非空 `Novel_architecture.txt` 同步到 `Novel_setting.txt`。
7. 任务更新为 `done`，`progress=100`。

### Directory Stage

1. 前端调用 `serviceBridge.createGenerationJob({ stage: 'directory' })`。
2. 执行器确认 `Novel_architecture.txt` 存在且非空；若只存在 `Novel_setting.txt`，可同步回 `Novel_architecture.txt` 以兼容旧目录生成函数。
3. 读取 `choose_configs.chapter_outline_llm` 和对应 LLM 配置。
4. 调用 `Chapter_blueprint_generate(...)`。
5. 检查 `Novel_directory.txt` 非空。
6. 任务更新为 `done`，`progress=100`。

## Compatibility

- 保留旧 GUI 的文件约定：`Novel_architecture.txt` 仍作为旧目录生成函数的输入。
- 新前端继续读取 `Novel_setting.txt`；本轮通过同步复制确保前端能看到架构生成结果。
- 不改变现有 `GenerationJob` API schema；继续使用已有 `queued | running | paused | done | failed` 状态枚举。
- 对未接入真实执行器的 `draft`、`finalization`、`consistency`、`batch` 阶段保持当前边界：可继续创建壳任务或保留明确提示。实现时不扩大这些阶段的真实执行范围。

## Error Handling

执行器失败分两类：

- 配置/前置条件错误：例如缺少输出目录、缺少阶段模型选择、LLM 配置不存在、API Key 为空、目录生成缺少设定文件。返回 `failed` 任务，日志和 `error` 使用中文说明。
- 运行时错误：旧生成函数或 LLM 调用抛异常。捕获异常，任务置为 `failed`，日志中给出摘要，不记录 API Key、完整私有 Base URL 或长篇正文。

本轮不要求把失败映射为 4xx HTTP。为了让前端任务列表能看到失败记录，推荐 `POST /api/generation-jobs` 返回 200 + `status='failed'` 的任务对象；只有不支持的 stage、明显非法 payload 继续用现有 422/400。

## Frontend Behavior

`GenerationPage.vue` 的全局提示要改为阶段化说明：

- 设定、目录：提示已接入本地真实执行器，需要有效 LLM 配置，执行完成会写入项目文件。
- 草稿、定稿、审校、批量：仍提示尚未接入真实执行器或仍处于后续 milestone。

`GenerationJobDetail.vue` 的 `queued` 提示不能再断言所有任务“不会自动调用 LLM 或写入小说文件”。应改为只在 `queued` 时描述等待状态；已完成/失败任务主要看状态、错误和日志。

前端无需新增轮询，因为同步执行返回时任务已经是 `done` 或 `failed`。`loadJobs` 保持现状即可。

## Testing Strategy

后端测试：

- 用 `TestClient(create_app(config_file=...))` 和临时输出目录隔离真实配置。
- 通过 monkeypatch 执行器或 legacy 函数，避免真实 LLM 调用。
- 覆盖：
  - architecture 成功：写入 `Novel_architecture.txt` 和 `Novel_setting.txt`，任务 `done`。
  - directory 成功：已有设定文件时写入 `Novel_directory.txt`，任务 `done`。
  - 缺少 API Key：任务 `failed`，错误为中文。
  - 缺少设定文件执行 directory：任务 `failed`，错误为中文。
  - 未接入阶段仍保持现有边界。

前端验证：

- `npm run typecheck`
- `npm run build`
- 必要时手工检查生成页提示文案和任务详情状态。

## Trade-offs

- 选择同步执行：实现简单、可测试、立即让前端真实生成文件；代价是 HTTP 请求会等待 LLM 完成，长任务体验不如后台队列。
- 保留 in-memory job registry：本轮避免引入 SQLite 和任务恢复；代价是服务重启任务历史仍丢失。
- 通过文件同步兼容 `Novel_architecture.txt` 与 `Novel_setting.txt`：能快速打通旧生成函数和新前端；代价是短期存在两个含义相近的设定文件，后续应在服务层统一命名。

## Rollback

回滚优先级：

1. 回退前端提示文案改动。
2. 回退 `POST /api/generation-jobs` 对 architecture/directory 的真实执行调用，恢复 queued 壳任务。
3. 保留新增测试或按需同步回退。

回滚不应删除用户输出目录已有文件。
