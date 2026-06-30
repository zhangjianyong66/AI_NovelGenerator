# Error Handling

本项目错误处理分为三类：旧 GUI 中面向用户的弹窗/日志、本地 API 的 HTTP 错误、以及前端 serviceBridge 的连接状态与 mock 降级。

## FastAPI 错误合约

- 请求/响应校验交给 Pydantic model 和 FastAPI，字段约束应写在 model 上，例如 `Field(default=0, ge=0)`。
- 业务前置条件失败使用 `HTTPException`，`detail` 使用中文，方便前端直接展示。
- 常用状态码：
  - `400`：缺少输出路径、无效章节范围、文件不存在但属于用户操作问题。
  - `404`：请求的项目文件、章节、任务或角色文件不存在。
  - `422`：Pydantic 校验失败，或生成阶段不支持。
- API handler 保持薄层，错误尽量在 helper 中靠近数据边界抛出，例如 `_active_output_path()`、`_project_file_response()`、`_validate_library_name()`。

参考文件：

- `app/api/server.py`
- `tests/test_api_project_config.py`
- `tests/test_api_generation_jobs.py`
- `tests/test_api_role_library.py`

## 配置与文件错误

- 旧 `config_manager.load_config()` 对 JSON 格式错误、编码错误、IO 错误记录 `logging.error` 并返回 `{}`；不要让 GUI 因坏配置直接崩溃。
- API 的 `_load_config()` 当前不吞掉 JSON 解析错误；这能让测试和本地 API 暴露配置损坏问题。不要无意中把 API 错误全部吞掉。
- 写配置保持原子写入；临时文件写失败时删除临时文件并重新抛出。
- 读取输出目录文件时使用 UTF-8；不存在的核心项目文件可以返回 `exists=False`，但章节详情请求不存在章节时返回 `404`。

## 前端错误处理

- 所有真实 API 调用应经过 `frontend/src/services/serviceBridge.ts`。
- `requestJson()` 负责把非 2xx 响应标准化为 `ServiceBridgeError`，并更新 `status.mode`。
- 允许 mock 降级的读取类操作使用 `withMockFallback()`；保存类操作不应降级到 mock。
- 页面只消费 serviceBridge 的状态和错误，不应重复拼接 fetch URL 或复制错误解析逻辑。

参考文件：

- `frontend/src/services/serviceBridge.ts`
- `frontend/src/services/types.ts`
- `tests/test_frontend_service_bridge_contract.py`

## GUI 错误处理

- GUI 回调中需要捕获用户操作相关异常，并通过现有 helper 或弹窗展示。
- 长耗时 LLM/Embedding 测试在后台线程执行，错误通过 `log_func` 和 `handle_exception_func` 返回给界面。
- 不要在 GUI 回调里重复实现 API/生成核心的错误判断；优先复用 `config_manager.py`、`novel_generator/` 或后续 service 层。

## 常见错误边界

- 输出路径为空：API 应返回 `400` 和“请先设置项目输出路径”。
- 角色库分类或角色名包含 `/`、`\`、`.`、`..`：API 应拒绝，防止路径穿越。
- 批量章节范围无效：返回 `400`；批量定稿和批量审校缺失章节文件时指出第一个缺失章节。批量草稿允许缺失章节文件并负责生成，遇到已有章节默认跳过不覆盖。
- WebDAV URL 为空：返回 `400`；真实网络错误不伪装成成功。

## Scenario: Generation Job Background Executor

### 1. Scope / Trigger

- Trigger: `POST /api/generation-jobs` 的 `architecture`、`directory`、`draft`、`finalization`、`batch`、`batchDraft`、`batchFinalization`、`batchConsistency` 和 `consistency` 阶段已接入本地后台真实执行器，并通过 WebSocket 推送任务状态。
- Scope: FastAPI handler 创建并持久化任务记录，后台线程调用 `app/services/generation_executor.py` 执行 legacy 配置解析、旧生成函数调用、文件非空校验和用户可见错误；WebSocket 仅推送已保存的完整任务快照。

### 2. Signatures

- API: `POST /api/generation-jobs`
- Request model: `GenerationJobCreateRequest`
  - `projectId: str = "current"`
  - `stage: str`
  - `chapterNumber` 供 `draft`、`finalization`、`consistency` 使用；`draft` 可在章节文件不存在时创建正文，`finalization` 和 `consistency` 要求章节正文已存在。
  - `startChapter`、`endChapter`、`targetWords`、`minimumWords`、`autoEnrich` 供 `batchDraft`、`batchFinalization`、`batchConsistency` 和兼容旧 `batch` 使用；`finalization` 可消费 `targetWords`、`minimumWords`、`autoEnrich` 做可选扩写。
- Response model: `GenerationJob`
  - `status` 可为 `queued`、`running`、`done`、`failed`。
- WebSocket: `WS /api/projects/{project_id}/generation-jobs/ws`
  - 消息：`{"type": "generationJobUpdated", "job": GenerationJob}`。
  - 连接建立后可先发送当前项目已有任务快照；后续只广播同一 `project_id` 的任务更新。

### 3. Contracts

- `architecture`：
  - 使用 `choose_configs.architecture_llm` 找到 `llm_configs` 条目。
  - 调用 `Novel_architecture_generate(...)`。
  - 成功后要求 `Novel_architecture.txt` 非空，并同步写入前端读取的 `Novel_setting.txt`。
- `directory`：
  - 使用 `choose_configs.chapter_outline_llm` 找到 `llm_configs` 条目。
  - 要求 `Novel_architecture.txt` 非空；如果只存在 `Novel_setting.txt`，服务层可同步回 `Novel_architecture.txt` 兼容旧函数。
  - 调用 `Chapter_blueprint_generate(...)`，成功后要求 `Novel_directory.txt` 非空。
- `draft`：
  - 使用 `choose_configs.prompt_draft_llm` 找到 `llm_configs` 条目。
  - 要求 `Novel_directory.txt` 非空，但不要求根部 `chapter_X.txt` 预先存在。
  - 调用 `generate_chapter_draft(...)`；旧函数写入 `chapters/chapter_X.txt` 后，服务层必须同步到前端读取的根部 `chapter_X.txt`。
- `finalization`：
  - 使用 `choose_configs.final_chapter_llm` 找到 `llm_configs` 条目。
  - 以根部 `chapter_X.txt` 为前端权威输入，执行前同步到旧函数读取的 `chapters/chapter_X.txt`。
  - 调用 `finalize_chapter(...)`，先基于前章结尾、当前章节目录和下一章节目录润色当前章节正文并写回 `chapters/chapter_X.txt`，再更新 `global_summary.txt`、`character_state.txt`，并沿用旧逻辑尝试更新 `vectorstore/`。
  - 当前章节目录和下一章节目录必须通过 `chapter_directory_parser.get_chapter_outline_context(...)` 截取，不能使用只识别行首 `第N章` 的临时正则；章节目录常见格式是 Markdown 标题 `# 第N章 - 标题`，错误截取会把后续章节一并塞进定稿 prompt，导致模型把第 N 章写成第 N+1 章。
  - 定稿模型返回正文如果第一条非空行显式标注了与当前 `novel_number` 不一致的章节号，必须拒绝覆盖章节文件，让任务失败并保留原文。
  - 执行后再次同步 `chapters/chapter_X.txt` 到根部 `chapter_X.txt`。
- `consistency`：
  - 使用 `choose_configs.consistency_review_llm` 找到 `llm_configs` 条目。
  - 读取小说设定，优先 `Novel_setting.txt`，缺失时兼容 `Novel_architecture.txt`。
  - 读取根部 `chapter_X.txt` 作为章节正文，必须非空。
  - 读取 `character_state.txt`、`global_summary.txt`、`plot_arcs.txt` 作为可选上下文；缺失按空文本传入。
  - 调用 `check_consistency(...)`，审校结果写入任务日志，不修改章节正文、摘要、角色状态、剧情要点或向量库。
- `batchDraft`：
  - 语义是“批量生成草稿”，允许范围内缺失根部 `chapter_X.txt`。
  - 遇到已有根部 `chapter_X.txt` 时默认跳过，不覆盖正文，跳过不算失败。
  - 服务层逐章复用 `draft`，单章失败后继续后续章节。
  - 全部未失败返回 `done`；存在任一失败返回 `failed`，`error` 是成功/失败章节汇总，逐章失败原因写入日志。
- `batchFinalization` 和兼容旧 `batch`：
  - 语义是“批量定稿”，只处理范围内已存在的根部 `chapter_X.txt`。
  - API 层继续校验范围和缺失章节文件。
  - 服务层逐章复用 `finalization`，单章失败后继续后续章节。
  - 全部成功返回 `done`；存在任一失败返回 `failed`，`error` 是成功/失败章节汇总，逐章失败原因写入日志。
- `batchConsistency`：
  - 语义是“批量审校”，只处理范围内已存在的根部 `chapter_X.txt`。
  - API 层继续校验范围和缺失章节文件。
  - 服务层逐章复用 `consistency`，审校结果写入任务日志，不修改章节正文、摘要、角色状态、剧情要点或向量库。
  - 全部成功返回 `done`；存在任一失败返回 `failed`，`error` 是成功/失败章节汇总，逐章失败原因写入日志。
- 创建响应：
  - `POST /api/generation-jobs` 对可执行阶段应尽快返回已持久化的 `queued` 或 `running` 初始快照，不等待真实生成完成。
  - 后台执行开始时保存并广播 `running/progress=5`；完成后保存并广播最终 `done` 或 `failed`。
  - 前端和测试不得假设创建响应已经包含最终日志、错误或输出文件结果；需要通过 WebSocket、列表接口或详情接口读取最终状态。
  - 后台执行线程只存在于当前 FastAPI 进程；`create_app(...)` 启动时必须把 SQLite 中遗留的 `queued` / `running` 任务持久化为 `failed/progress=100/error="后端服务重启，任务已中断"`，避免后端重启后 UI 继续显示已失去执行线程的任务。

### 4. Validation & Error Matrix

- Unsupported `stage` -> HTTP `422`，`detail="不支持的生成阶段"`。
- `consistency` 缺章节文件 -> HTTP `400`，`detail="章节文件不存在"`。
- `batchDraft` 已有章节文件 -> 任务日志记录跳过，不覆盖章节正文。
- `batchFinalization` / `batchConsistency` / 兼容旧 `batch` 缺章节文件 -> HTTP `400`，`detail="章节文件不存在：<chapter>"`。
- 批量阶段单章失败 -> 任务响应 `status="failed"`，不是 HTTP 失败；日志包含逐章失败原因。
- 后端重启时 SQLite 中仍是 `queued` / `running` 的任务 -> 启动清理持久化为 `failed`，日志追加“后端服务重启，任务已中断”。
- `architecture` / `directory` / `draft` / `finalization` / `consistency` 缺阶段模型选择 -> 后台最终保存 `GenerationJob(status="failed")`，`error` 为中文原因。
- LLM 配置不存在、缺 API Key、缺模型名、缺接口格式 -> 后台最终保存 `failed` 任务，不伪装成功。
- 旧生成函数返回空文件或未写目标文件 -> 后台最终保存 `failed` 任务，说明目标生成结果为空。
- `draft` 缺 `Novel_directory.txt` -> 后台最终保存 `failed` 任务，`error="请先生成章节目录"`。
- `finalization` 缺根部章节正文 -> 后台最终保存 `failed` 任务，`error="请先生成或保存章节正文"`。
- `finalization` 模型返回显式错误章节标题，例如定稿第 2 章却返回 `# 第3章 ...` -> 后台最终保存 `failed` 任务，不覆盖 `chapter_2.txt`。
- `consistency` 缺 `Novel_setting.txt` 和 `Novel_architecture.txt` -> 后台最终保存 `failed` 任务，`error="请先准备小说设定"`。
- `consistency` 根部章节正文为空 -> 后台最终保存 `failed` 任务，`error="请先生成或保存章节正文"`。
- `consistency` 审校模型返回空白 -> 后台最终保存 `failed` 任务，`error="一致性审校结果为空"`。

### 5. Good/Base/Bad Cases

- Good: 有效 LLM 配置 + 项目参数完整，`architecture` 创建响应返回初始快照，随后详情接口或 WebSocket 更新为 `done`，`Novel_architecture.txt` 和 `Novel_setting.txt` 均非空。
- Base: 无 API Key，`architecture` 创建响应返回初始快照，随后详情接口或 WebSocket 更新为 `failed` 任务，前端能在详情里展示错误。
- Bad: `directory` 在缺少设定文件时静默返回 `done` 或写入空目录文件；这是错误实现。
- Good: `draft` 成功后，`chapters/chapter_1.txt` 和根部 `chapter_1.txt` 均非空，`GET /api/projects/current/chapters` 能读到章节正文。
- Base: `finalization` 成功后，章节正文会被润色后写回，`global_summary.txt` 和 `character_state.txt` 更新；`plot_arcs.txt` 当前不属于该执行器合同。
- Good: `consistency` 成功后，任务日志包含审校结果，项目文件内容保持不变。
- Base: `consistency` 缺小说设定或缺 API Key 时后台最终保存 `failed` 任务，前端能在详情里展示错误。
- Bad: `draft` 继续要求根部 `chapter_X.txt` 已存在，导致前端无法从目录推进到章节草稿。
- Bad: `consistency` 把审校结果写回章节或状态文件；审校当前是只读检查，不做自动修订。

### 6. Tests Required

- API 测试用 `create_app(config_file=tmp_path / "config.json")` 隔离真实配置。
- 真实 LLM 调用必须通过 monkeypatch fake 掉 legacy 生成函数。
- 断言点：
  - 成功任务的 `status == "done"`、`progress == 100`。
  - `POST /api/generation-jobs` 创建可执行任务时先返回 `queued` 或 `running`，不阻塞等待最终状态。
  - WebSocket 订阅能收到 `generationJobUpdated`，且最终快照包含 `done` 或 `failed`、日志和错误。
  - `state.sqlite3` 中启动前遗留的 `queued` / `running` 任务，在重建 app 后详情接口返回 `failed`、`progress == 100` 和中文中断错误。
  - 输出文件真实落盘且非空。
  - 缺 API Key / 缺设定文件最终保存 `failed` 任务和中文错误。
  - `draft` 成功时断言双路径章节文件同步，且章节列表可读。
  - `finalization` 成功时断言润色后章节正文、摘要和角色状态文件更新。
  - `finalization` 使用 Markdown 章节目录时，断言当前章节目录不包含下一章；模型返回错误章节标题时，断言原章节正文未被覆盖。
  - `consistency` 成功时断言审校结果持久化到任务日志，且章节、摘要、角色状态和剧情要点文件不变。
  - `batchDraft` 有效配置下生成缺失章节并跳过已有章节。
  - `batchFinalization` / 兼容旧 `batch` 有效配置下最终保存 `done`；部分章节失败时最终保存 `failed`，并断言后续章节仍被尝试执行。
  - `batchConsistency` 成功时断言审校结果写入任务日志，且项目文件保持不变。

### 7. Wrong vs Correct

#### Wrong

```python
@app.post("/api/generation-jobs")
def create_generation_job(request):
    Novel_architecture_generate(...)
    return {"status": "done"}
```

问题：API handler 直接拥有 LLM 参数映射和旧函数调用，难以测试，也会和后续工作流服务边界冲突。

#### Correct

```python
result = run_generation_job(config, stage, output_path)
job.status = result.status
job.progress = result.progress
job.log.extend(result.log)
job.error = result.error
```

正确做法：API 只更新任务响应，服务层拥有执行器合同、文件兼容和错误归一化。

## 代码例子

API 数据边界 helper 直接抛出 `HTTPException`，示例来自 `app/api/server.py`：

```python
def _active_output_path(config_path: Path) -> Path:
    filepath = (_load_config(config_path).get("other_params") or {}).get("filepath") or ""
    if not str(filepath).strip():
        raise HTTPException(status_code=400, detail="请先设置项目输出路径")
    return Path(filepath)
```

不存在的核心项目文件返回 `404`，调用方不用猜测文件名，示例来自 `app/api/server.py`：

```python
if file_id not in CORE_PROJECT_FILES:
    raise HTTPException(status_code=404, detail="未知项目文件")
```

前端连接错误集中在 `serviceBridge.ts` 标准化，页面只读共享状态：

```ts
status.error = normalized
status.mode = options.allowMockFallback ? 'mock' : 'disconnected'
throw normalized
```

旧 GUI 对破坏性操作使用显式确认，示例来自 `ui/generation_handlers.py`：

```python
first_confirm = messagebox.askyesno("警告", "确定要清空本地向量库吗？此操作不可恢复！")
if first_confirm:
    second_confirm = messagebox.askyesno("二次确认", "你确定真的要删除所有向量数据吗？此操作不可恢复！")
```
