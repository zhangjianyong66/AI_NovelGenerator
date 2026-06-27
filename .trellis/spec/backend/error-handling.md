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
- 批量生成章节范围无效：返回 `400`；缺失章节文件时指出第一个缺失章节。
- WebDAV URL 为空：返回 `400`；真实网络错误不伪装成成功。

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
