# 前端真实可用后续开发

## Goal

继续把新 Tauri/Vue 前端推进为真实创作工具。本轮推荐聚焦知识库真实向量化与检索最小闭环：从前端导入知识文件时，不再只复制到 `vectorstore/imported/`，而是调用现有 Embedding 配置写入旧生成链路已经使用的 Chroma `vectorstore/novel_collection`，让后续章节草稿生成可以检索这些资料。

用户价值：用户在前端导入世界观、设定或写作资料后，后续章节生成能通过现有知识检索链路读到资料；导入失败时能看到明确原因，而不是误以为文件已可用于生成。

## Confirmed Facts

- 最近相关任务已归档：
  - `06-28-frontend-real-usable`：完成小说设定和章节目录真实生成执行器。
  - `06-28-frontend-chapter-generation-real-usable`：完成单章草稿和定稿真实执行器。
  - `06-28-frontend-real-usable-followup`：生成任务历史持久化到 `.local/state.sqlite3`。
  - `06-28-frontend-real-usable-next`：章节列表支持计划章节，并可从前端创建缺失章节文件。
- `docs/feature-map-and-acceptance.md` 的“新前端真实可用开发顺序”中，下一优先级是知识库真实向量化与检索，然后才是项目管理能力。
- `app/api/server.py` 当前 `POST /api/knowledge/import` 只把文件复制到输出目录 `vectorstore/imported/`，不会创建 Embedding 或写入 Chroma。
- `novel_generator/knowledge.py` 已有旧 GUI 使用的 `import_knowledge_file(...)`，会读取文本、分块、创建 Embedding adapter，并写入或追加到输出目录 `vectorstore/` 下的 Chroma 集合。
- `novel_generator/chapter.py` 的草稿生成流程已经会加载同一输出目录下的 `vectorstore/novel_collection`，按关键词检索知识并注入草稿提示词。
- `embedding_adapters.py` 已有 OpenAI、Azure OpenAI、Ollama、LM Studio、Gemini、SiliconFlow 等 Embedding adapter 工厂。
- 模型设置接口已能读写 `embedding_configs` 和 `last_embedding_interface_format`；响应给前端时隐藏 API Key，但后端读取本地 `config.json` 可拿到真实密钥。
- 前端知识库页已经通过 `serviceBridge.importKnowledgeFile(...)` 调用真实 API，并在非真实后端模式下禁用导入等写操作。
- `KnowledgeItem` 当前只区分 `file` / `role`，知识文件列表展示 `name`、`description`、`tags`。

## Requirements

- R1. 本轮只实现知识库导入后的真实向量化最小闭环，不展开项目新建/切换、批量生成真实执行、一致性审校真实执行或后台异步队列。
- R2. 前端仍通过本地 FastAPI 边界导入知识文件，不直接调用 legacy Python 函数。
- R3. API 导入知识文件时必须复用旧 GUI 的向量库格式和输出目录，保持后续 `draft` 生成的现有检索逻辑可读取。
- R4. API 必须从当前 `config.json` 的选中 Embedding 配置中取接口格式、Base URL、模型名、API Key 和 retrieval K；缺失选中配置、模型名或必要密钥时返回清晰中文错误。
- R5. 导入成功后仍保留源文件副本到 `vectorstore/imported/`，用于前端列表和用户追踪，但成功含义必须是“已写入向量库”。
- R6. 导入失败时不得返回成功文案；前端必须展示后端错误，避免用户误以为知识已可用于生成。
- R7. 知识文件列表应能体现导入文件是否已向量化，至少通过标签或描述区分“已向量化”和旧的“导入文件”状态。
- R8. 清理向量库仍删除 `vectorstore/`，清理后知识文件列表应反映没有可用导入文件或向量化状态。
- R9. 保持旧 Python GUI 可运行，不改变旧函数签名，除非只做向后兼容增强。
- R10. 不提交 `config.json`、API Key、私有 Base URL、真实小说正文、`vectorstore/`、`.local/` 或前端构建产物。

## Acceptance Criteria

- [x] 规划阶段产出收敛后的 `prd.md`、`design.md` 和 `implement.md`。
- [x] `POST /api/knowledge/import` 在有效 Embedding 配置下会调用向量化导入，写入输出目录 `vectorstore/` 的 Chroma 集合，并保留 `vectorstore/imported/<文件名>` 副本。
- [x] 导入后使用同一 Embedding adapter 调用 `load_vector_store(...).similarity_search(...)` 能检索到测试知识片段，证明后续章节草稿生成可读取。
- [x] 缺少选中 Embedding 配置、模型名或必要 API Key 时，API 返回清晰中文错误且不展示成功导入。
- [x] 前端知识文件列表能展示已向量化状态；导入成功文案说明资料已写入向量库。
- [x] `python -m pytest tests` 通过，或记录明确环境阻塞。
- [x] `cd frontend && npm run typecheck` 通过，或记录明确环境阻塞。
- [x] `cd frontend && npm run build` 通过，或记录明确环境阻塞。
- [x] `docs/feature-map-and-acceptance.md` 和 `AGENTS.md` 更新知识库真实向量化边界。

## Out Of Scope

- 不实现项目新建、打开、切换或最近项目。
- 不实现一致性审校真实执行。
- 不实现批量章节真实执行。
- 不实现后台异步向量化队列、进度轮询、取消、暂停或断点恢复。
- 不新增独立检索 API，除非测试需要内部验证；章节草稿生成继续复用现有 `vectorstore` 检索。
- 不重做知识库页视觉结构。

## Scope Decision

- 用户已确认本轮按推荐范围执行：只做“前端导入知识文件 -> 后端真实向量化 -> 章节草稿可检索”的最小闭环。

## Notes

- 本任务属于复杂任务，进入实现前必须补充 `design.md` 和 `implement.md`，并经用户确认后再 `task.py start`。
- 系统环境没有 `python` 命令；验证使用项目虚拟环境命令 `.venv/bin/python -m pytest tests`，结果通过。
