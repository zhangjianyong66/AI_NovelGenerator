# 前端知识库真实向量化实施计划

## 实施步骤

- [x] 读取并确认相关代码边界：
  - `app/api/server.py`
  - `novel_generator/knowledge.py`
  - `novel_generator/vectorstore_utils.py`
  - `embedding_adapters.py`
  - `frontend/src/pages/KnowledgePage.vue`
  - `frontend/src/features/knowledge/components/KnowledgeFileList.vue`
  - `frontend/src/services/serviceBridge.ts`
  - `tests/test_api_knowledge_tools.py`
- [x] 增强 `novel_generator/knowledge.py`：
  - 增加轻量结果结构或等价返回值，保持旧 GUI 调用兼容。
  - 文件不存在、空内容、分块为空、向量库初始化/追加失败时返回失败原因。
  - 成功时返回导入片段数。
- [x] 在 `app/api/server.py` 增加 Embedding 配置解析 helper：
  - 从 `_load_config(config_path)` 读取 `last_embedding_interface_format` 和 `embedding_configs`。
  - 校验选中配置、接口格式、模型名、必要 API Key。
  - `Ollama` 不强制 API Key，其他接口先按需要密钥处理。
- [x] 修改 `POST /api/knowledge/import`：
  - 验证源文件存在。
  - 调用 legacy 知识导入函数写入 Chroma。
  - 失败时返回 HTTP 400 中文错误。
  - 成功后复制源文件到 `vectorstore/imported/`。
  - 返回“已导入并写入向量库”类成功文案。
- [x] 修改 `_knowledge_items(...)`：
  - 对 `vectorstore/imported/` 文件加 `已向量化` 标签，当 `vectorstore/` 存在 Chroma 数据文件时展示。
  - 仍保留角色库汇总逻辑。
- [x] 调整前端知识库页面文案：
  - 导入成功使用后端返回文案。
  - 保持写操作守卫和 mock 禁写语义。
  - 如无类型变化，不改 `KnowledgeItem` 合同。
- [x] 更新测试：
  - 知识导入成功路径用 monkeypatch fake legacy importer，断言调用参数、复制副本、成功文案和列表标签。
  - 缺配置/缺模型名/缺 API Key 路径返回 400。
  - legacy importer 返回失败时 API 返回 400。
  - 清理向量库测试继续通过。
- [x] 更新文档：
  - `docs/feature-map-and-acceptance.md`：知识库能力从“复制文件”更新为“导入时写入向量库，真实 Embedding 配置可用时章节生成可检索”。
  - `AGENTS.md`：记录 API 知识导入的新边界，供下次复用。

## 验证命令

- [x] `.venv/bin/python -m pytest tests`
- [x] `cd frontend && npm run typecheck`
- [x] `cd frontend && npm run build`

## 风险点与回滚

- Chroma/Embedding 依赖可能在测试环境缺少外部服务；测试必须 monkeypatch legacy importer，不调用真实网络。
- `Ollama` 与 OpenAI 类接口的 API Key 规则不同；实现时明确只豁免本地接口格式。
- `vectorstore/` 同时包含 Chroma 数据和 `imported/` 副本，判断“已向量化”不能只看 `imported/`。
- 回滚点：
  - 恢复 `POST /api/knowledge/import` 为复制文件。
  - 保留或回退 `novel_generator/knowledge.py` 返回值增强；如果旧 GUI 不受影响，可保留。
  - 同步回滚文档能力描述。

## 启动实现前检查

- [x] 用户已审阅 `prd.md`、`design.md`、`implement.md` 并同意进入实现。
- [x] 运行 `python3 ./.trellis/scripts/task.py start .trellis/tasks/06-28-frontend-real-usable-continue` 后再改业务代码。
