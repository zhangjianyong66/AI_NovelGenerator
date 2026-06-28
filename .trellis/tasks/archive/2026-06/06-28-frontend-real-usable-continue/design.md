# 前端知识库真实向量化设计

## 目标边界

本轮把知识库导入从“复制文件到 `vectorstore/imported/`”升级为“复制文件并写入现有 Chroma 向量库”。后续章节草稿生成不新增接口，继续复用 `novel_generator/chapter.py` 里已经存在的 `load_vector_store(...)` 和关键词检索流程。

不做后台队列、导入进度、独立检索 API、项目多实例管理，也不改旧 GUI 的用户流程。

## 数据流

```
前端 KnowledgePage
  -> serviceBridge.importKnowledgeFile(filePath)
  -> POST /api/knowledge/import
  -> 读取 config.json 当前 outputPath + selected embedding config
  -> legacy knowledge importer 分块 + embedding + Chroma add_documents
  -> 复制源文件到 outputPath/vectorstore/imported/
  -> GET /api/knowledge 展示已向量化知识文件
  -> draft 生成阶段加载同一 outputPath/vectorstore/novel_collection
```

## 后端设计

### Embedding 配置解析

在 `app/api/server.py` 增加薄 helper，从当前 legacy `config.json` 中解析选中 Embedding 配置：

- 选中名称来自 `last_embedding_interface_format`，缺失时可回退到 `embedding_configs` 的第一项。
- 配置项来自 `embedding_configs[选中名称]`。
- 必须有 `interface_format` 和 `model_name`。
- 对需要密钥的接口要求 `api_key` 非空；`Ollama` 可不要求 API Key。
- `base_url` 允许沿用旧导入函数默认值。

错误使用 `HTTPException(status_code=400, detail="<中文原因>")`，由 `serviceBridge` 透传给页面。

### 向量化导入

优先复用 `novel_generator.knowledge.import_knowledge_file(...)`，避免复制分块、Embedding adapter 和 Chroma 写入逻辑。该函数当前没有返回成功/失败信号，因此需要做向后兼容增强：

- 保持旧签名参数不变。
- 返回一个包含导入片段数或成功状态的轻量结果，旧 GUI 可忽略返回值。
- 对文件不存在、空内容、分块为空、创建/追加向量库失败等情况返回失败信息，API 将其转换为 HTTP 400。
- 成功后 API 再复制源文件到 `vectorstore/imported/`，确保列表可追踪。

如果 legacy 函数内部异常，API 不伪装成功，返回中文错误。

### 知识文件状态

`GET /api/knowledge` 继续汇总 `vectorstore/imported/` 和角色库。为了不扩大前端类型合同，本轮不新增字段，只通过 `tags` 表达状态：

- `vectorstore/` 中存在 Chroma 数据库文件时，导入文件标签包含 `已向量化`。
- 如果只存在旧导入副本但向量库不存在，标签为 `导入文件`，描述仍显示相对路径。

清理向量库会删除整个 `vectorstore/`，包括 `imported/`，所以清理后列表为空或只剩角色库。

## 前端设计

前端保持现有页面结构：

- `KnowledgePage.vue` 继续用 `runOperation` 和 `serviceBridge.canWrite(...)` 守卫导入。
- 导入成功文案改为后端返回的“已导入并写入向量库”。
- `KnowledgeFileList.vue` 已渲染 `tags`，无需新增复杂 UI；只需确保标签能显示 `已向量化`。
- 不直接调用 `mockApi`，不增加 mock 写入 fallback。

## 测试策略

### Python API

新增或调整 `tests/test_api_knowledge_tools.py`：

- 有效 Embedding 配置下，导入会调用 legacy 导入函数并复制文件。
- 使用 monkeypatch fake 掉 legacy 向量化函数，避免测试依赖真实 Embedding 外部服务。
- fake 成功路径断言 API 返回成功文案、导入副本存在、列表标签包含 `已向量化`。
- fake 失败路径断言 API 返回 400 和中文错误。
- 缺少选中 Embedding 配置、缺模型名、需要密钥但缺 API Key 均返回 400。

如需证明检索链路，增加一个纯后端单元测试用可控 fake embedding 或 monkeypatch 验证 API 使用的 outputPath 与 legacy vectorstore owner 一致；不在 CI 中调用真实 OpenAI/Ollama。

### 前端

- `tests/test_frontend_service_bridge_contract.py` 保持页面/store 不直接 import `mockApi`。
- 如类型变化，更新 `frontend/src/services/types.ts`；本轮推荐不新增字段，降低前端改动。
- 运行 `cd frontend && npm run typecheck` 和 `cd frontend && npm run build`。

## 兼容与回滚

- 旧 GUI 调用 `novel_generator.knowledge.import_knowledge_file(...)` 时可忽略返回值，用户日志行为不变。
- 回滚时可把 API 导入恢复为复制文件，但需同步回滚文档中“已向量化”的能力描述。
- 不迁移或删除已有 `vectorstore/` 格式；仍使用 `novel_collection` collection name。
