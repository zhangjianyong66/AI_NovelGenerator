# Logging Guidelines

项目当前主要使用 Python 标准库 `logging`，部分旧工具和调试流程仍有 `print()`。新增代码应优先使用 `logging` 或既有 GUI 日志回调，避免把敏感配置和大段正文打印到控制台。

## Python 日志

- provider、生成流程、向量库和配置错误使用 `logging.warning()` / `logging.error()`。
- 长流程状态可使用 `logging.info()`，但不要记录完整 API Key、WebDAV 密码、私有 Base URL 或整章小说正文。
- 旧模块中存在多处 `logging.basicConfig(...)`；新增模块不要随意重复全局配置日志格式，除非任务明确整理日志系统。
- 需要把错误反馈给 GUI 时，优先使用现有 `log_func`、`handle_exception_func` 或 `ui/helpers.py` 的 helper。

参考文件：

- `llm_adapters.py`
- `embedding_adapters.py`
- `novel_generator/common.py`
- `novel_generator/vectorstore_utils.py`
- `config_manager.py`
- `ui/helpers.py`

## 调试输出

现有代码中存在打印 prompt 和 LLM 返回内容的调试输出，例如 `novel_generator/common.py`、`consistency_checker.py`。新增调试输出前先判断：

- 是否会暴露用户小说正文、API 密钥、私有地址或账号。
- 是否会在批量生成时刷出大量日志，影响 GUI 或终端可读性。
- 是否应该改成可控的 debug 日志或 UI 日志。

不要新增无条件打印完整 prompt、完整模型响应或完整配置 JSON。

## API 与前端日志

- FastAPI handler 当前不做结构化访问日志；开发期依赖 uvicorn 默认日志即可。
- 前端 `serviceBridge.ts` 用状态对象承载错误，不应在每个页面重复 `console.error`。
- 如需新增前端调试日志，限制在开发诊断场景，避免记录用户正文和密钥。

## 敏感信息

禁止记录：

- `api_key` / `apiKey`
- `webdav_password` / `password`
- 私有 `base_url` 或内部服务地址
- 小说输出全文、角色库全文、知识库全文
- 本机绝对路径中包含的私人账号信息，除非它是用户明确需要排查的路径问题

## 日志级别

- `info`：可恢复长流程状态，例如开始导入知识库、向量库已更新。
- `warning`：外部服务返回空、向量库加载失败但可继续、章节内容为空导致跳过。
- `error`：配置读写失败、网络调用失败、向量库删除失败、无法恢复的生成异常。

测试中不要断言完整日志文本，除非日志本身就是用户可见合约。
