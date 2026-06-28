# Persistence And Config

当前项目没有 ORM。持久化由根目录 `config.json`、用户输出目录中的文本文件、角色库目录、WebDAV 远程配置备份、Chroma `vectorstore/` 和前端生成任务 SQLite 状态库组成。SQLite 当前只保存生成任务历史，不承载小说正文、项目配置、角色库或向量数据。

## 本地配置

- 默认配置文件是项目根目录 `config.json`，已被 `.gitignore` 忽略，禁止提交。
- 旧 GUI 通过 `config_manager.py` 读写配置；如果文件不存在，`create_config()` 会写入默认结构。
- FastAPI 本地 API 默认读写同一个 `config.json`，测试中通过 `create_app(config_file=tmp_path / "config.json")` 隔离真实配置。
- FastAPI 本地 API 读取配置时，如果 `other_params.filepath` 缺失或为空，会自动使用配置文件同级的 `output/`，创建目录并写回配置；根目录 `output/` 不提交。
- 保存 JSON 时使用 UTF-8、`ensure_ascii=False`、缩进格式，并优先保持原子写入模式：先写临时文件，再 `os.replace()`。

## 生成任务状态库

- 生成任务状态库默认位于项目根目录 `.local/state.sqlite3`，`.local/` 已被 `.gitignore` 忽略。
- 该库由 `app/services/generation_job_store.py` 使用标准库 `sqlite3` 管理，当前只包含 `generation_jobs` 表。
- `generation_jobs` 保存任务 ID、项目 ID、阶段、标题、状态、进度、开始时间、日志、错误和创建请求参数，供前端刷新或后端重启后恢复任务历史。
- API 测试应通过 `create_app(state_db_file=tmp_path / "state.sqlite3")` 隔离任务状态库，不读写真正的 `.local/state.sqlite3`。
- 删除 `.local/state.sqlite3` 只会清空生成任务历史，不会删除 `config.json` 或小说输出文件。

参考文件：

- `config_manager.py`
- `app/api/server.py`
- `tests/test_api_project_config.py`
- `tests/test_api_model_settings.py`

## 配置兼容规则

`config.json` 的 legacy 字段仍是源数据格式：

- `other_params.filepath`
- `other_params.topic`
- `other_params.genre`
- `other_params.num_chapters`
- `other_params.word_number`
- `other_params.chapter_num`
- `llm_configs`
- `embedding_configs`
- `choose_configs`
- `proxy_setting`
- `webdav_config`

API 返回给前端时使用 camelCase，并隐藏密钥正文：

- `apiKey` 返回空字符串
- `hasApiKey` 表示是否已保存密钥
- 保存时空 `apiKey` 应保留同名旧密钥
- WebDAV 密码同理使用 `password` + `hasPassword`

修改配置字段时必须同步：

- Pydantic model
- legacy config merge/from 函数
- 前端 `frontend/src/services/types.ts`
- `serviceBridge.ts` 调用处
- pytest 断言
- `AGENTS.md` 中项目级说明，如该信息会被下次复用

## 输出目录文件

输出目录来自 `config.json` 的 `other_params.filepath`。常见文件包括：

- `Novel_setting.txt`
- `Novel_directory.txt`
- `chapter_<数字>.txt`
- `outline_<数字>.txt`
- `global_summary.txt`
- `character_state.txt`
- `plot_arcs.txt`
- `vectorstore/`
- `角色库/<分类>/<角色名>.txt`

API 当前固定支持的核心项目文件映射在 `app/api/server.py` 的 `CORE_PROJECT_FILES`。新增项目文件接口时先扩展该映射和测试，不要在页面里硬编码文件路径。

当前本地 API 暴露给前端的项目/知识库列表是文件系统视图：

- `GET /api/projects` 返回当前配置对应的单项目摘要，章节完成数来自输出目录下的 `chapter_<数字>.txt`。
- `GET /api/knowledge` 汇总 `vectorstore/imported/` 下的导入文件和 `角色库/<分类>/<角色名>.txt` 角色文件。

## Scenario: 文件系统章节生命周期

### 1. Scope / Trigger

- Trigger: 前端章节页需要从目录推进到可编辑章节，不再要求用户手动创建 `chapter_<数字>.txt`。
- Scope: 本地 FastAPI 章节接口、输出目录根部章节文件、前端章节编辑页。

### 2. Signatures

- `GET /api/projects/{project_id}/chapters`
- `POST /api/chapters/{chapter_number}`
- `PUT /api/chapters/{chapter_number}`

### 3. Contracts

- `GET /api/projects/{project_id}/chapters` 返回已有章节文件和计划章节的并集：
  - 已有文件来自输出目录根部 `chapter_<数字>.txt`。
  - 计划章节来自 `Novel_directory.txt` 可解析章节号，以及 `other_params.num_chapters` 推导的 `1..N`。
  - 缺失文件的计划章节返回 `status="planned"`、`content=""`、`words=0`。
  - 已有章节返回 `status="draft"`，正文来自根部 `chapter_<数字>.txt`。
- `POST /api/chapters/{chapter_number}` 只创建缺失的根部 `chapter_<数字>.txt`，不写 legacy `chapters/`，不覆盖已有文件。
- `PUT /api/chapters/{chapter_number}` 只保存已存在的根部章节文件；不得自动创建缺失章节。
- 标题和简介尽量从 `Novel_directory.txt` 补齐，解析不到时使用 `第<数字>章` 和空简介。

### 4. Validation & Error Matrix

| Condition | Expected |
| --- | --- |
| `POST` 章节号小于等于 0 | HTTP `400`，`detail="章节号必须大于 0"` |
| `POST` 目标 `chapter_<数字>.txt` 已存在 | HTTP `409`，`detail="章节文件已存在"`，不得覆盖正文 |
| `PUT` 目标章节文件不存在 | HTTP `404`，`detail="章节文件不存在"` |
| 输出路径缺失 | 沿用 `_active_output_path()`，返回中文 `400` |

### 5. Good/Base/Bad Cases

- Good: `Novel_directory.txt` 包含第 2 章且只有 `chapter_1.txt` 时，列表返回第 1 章 `draft` 和第 2 章 `planned`。
- Base: 用户对第 2 章调用 `POST /api/chapters/2` 后，根部出现空 `chapter_2.txt`，随后 `PUT` 可保存正文。
- Bad: `PUT /api/chapters/2` 在文件不存在时自动创建文件；这会模糊“创建”和“保存”两个用户动作。
- Bad: 把计划章节计入 `GET /api/projects` 的 `chaptersCompleted`；完成数仍只按真实 `chapter_<数字>.txt` 文件计算。

### 6. Tests Required

- API 测试用临时 `config.json` 和输出目录隔离真实数据。
- 断言列表混合已有章节和计划章节，顺序按章节号。
- 断言 `POST` 创建缺失章节并返回可编辑章节。
- 断言 `POST` 对已有章节返回 `409` 且磁盘正文未变。
- 断言新建章节可以继续通过 `PUT` 保存。

### 7. Wrong vs Correct

#### Wrong

```python
@app.put("/api/chapters/{chapter_number}")
def save_chapter(chapter_number: int, request: ChapterSaveRequest):
    _chapter_file_path(output_path, chapter_number).write_text(request.content)
```

问题：缺失章节会被保存动作隐式创建，前端无法区分“计划章节尚未落盘”和“真实章节已存在”。

#### Correct

```python
@app.post("/api/chapters/{chapter_number}")
def create_chapter(chapter_number: int):
    with file_path.open("x", encoding="utf-8"):
        pass

@app.put("/api/chapters/{chapter_number}")
def save_chapter(chapter_number: int, request: ChapterSaveRequest):
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="章节文件不存在")
```

正确做法：创建与保存分离，`open("x")` 防止覆盖已有正文。

## 向量库和知识库

- 向量库默认在当前输出目录的 `vectorstore/`，Chroma collection name 仍为 `novel_collection`。
- 切换 Embedding 模型后建议清空 `vectorstore/`，避免旧向量污染检索。
- 知识导入接口会把本地文件分块写入 `vectorstore/`，并在成功后复制源文件到 `vectorstore/imported/` 作为前端列表记录。
- 清理向量库会删除整个 `vectorstore/`，包括 `imported/` 副本，因此 UI 和 API 文案必须明确这是破坏性操作。

参考文件：

- `novel_generator/vectorstore_utils.py`
- `novel_generator/knowledge.py`
- `app/api/server.py`
- `tests/test_api_knowledge_tools.py`

## Scenario: 知识库真实向量化导入

### 1. Scope / Trigger

- Trigger: 前端知识库页调用本地 API 导入资料，资料必须进入旧生成链路读取的 Chroma 向量库，而不是只复制文件。
- Scope: `POST /api/knowledge/import`、`GET /api/knowledge`、`config.json.embedding_configs`、输出目录 `vectorstore/`、`novel_generator.knowledge.import_knowledge_file(...)`。

### 2. Signatures

- API: `POST /api/knowledge/import`
- Request model: `KnowledgeImportRequest`
  - `filePath: str`，本机知识文件路径。
- Response model: `OperationResult`
  - `success: bool`
  - `message: str`
- Legacy importer:

```python
def import_knowledge_file(
    embedding_api_key: str,
    embedding_url: str,
    embedding_interface_format: str,
    embedding_model_name: str,
    file_path: str,
    filepath: str,
) -> KnowledgeImportResult:
    ...
```

### 3. Contracts

- API 必须从当前 `config.json` 读取选中的 Embedding 配置：
  - 选中名称来自 `last_embedding_interface_format`；缺失时可回退到 `embedding_configs` 第一项。
  - 配置项来自 `embedding_configs[选中名称]`。
  - 必须有接口格式和模型名。
  - 远程接口必须有 API Key；本地 `Ollama`、`ML Studio` / `LM Studio` 可以没有 API Key。
- API 调用 `novel_generator.knowledge.import_knowledge_file(...)` 写入 Chroma。导入失败时不得复制源文件到 `vectorstore/imported/`，也不得返回成功。
- 导入成功后复制源文件到当前输出目录 `vectorstore/imported/<文件名>`，仅用于前端展示和追踪导入源文件。
- `GET /api/knowledge` 对 `vectorstore/imported/` 文件返回 `tags=["导入文件", "已向量化"]`，前提是 `vectorstore/` 中存在非 `imported/` 的 Chroma 数据文件。
- 章节草稿生成继续通过 `novel_generator.chapter.py` 加载同一 `vectorstore/`，不新增单独检索 API。

### 4. Validation & Error Matrix

| Condition | Expected |
| --- | --- |
| `filePath` 不存在或不是文件 | HTTP `400`，`detail="知识文件不存在"` |
| `embedding_configs` 缺失或选中项不存在 | HTTP `400`，`detail="请先配置 Embedding 模型"` |
| 选中 Embedding 配置缺接口格式 | HTTP `400`，`detail="Embedding 配置缺少接口格式"` |
| 选中 Embedding 配置缺模型名 | HTTP `400`，`detail="Embedding 配置缺少模型名称"` |
| 远程 Embedding 配置缺 API Key | HTTP `400`，`detail="Embedding 配置缺少 API Key"` |
| legacy importer 返回失败 | HTTP `400`，`detail` 使用 importer 的中文失败原因 |
| 导入成功 | HTTP `200`，复制导入副本，响应说明已写入向量库和片段数 |

### 5. Good/Base/Bad Cases

- Good: 有效 Ollama Embedding 配置、源文件存在，导入后 `vectorstore/` 出现 Chroma 数据，`vectorstore/imported/<文件名>` 存在，知识列表展示“已向量化”。
- Base: OpenAI Embedding 配置未填写 API Key，接口直接返回中文 400，不调用外部服务。
- Base: `ML Studio` / `LM Studio` 本地接口允许空 API Key，由 adapter 向本地服务发请求。
- Bad: API 先复制文件再尝试向量化；一旦向量化失败，前端会误以为知识已可用于生成。
- Bad: 页面或 API 把 `vectorstore/imported/` 当成向量库本体；它只是导入源文件副本。

### 6. Tests Required

- API 测试使用临时 `config.json` 和输出目录，不读写真实配置或真实向量库。
- 通过 monkeypatch fake legacy importer 覆盖：
  - 成功路径的调用参数、导入副本、响应文案和 `已向量化` 标签。
  - 缺 Embedding 配置、缺模型名、远程缺 API Key 的中文 400。
  - legacy importer 失败时不复制导入副本。
- 使用 fake embedding adapter 验证 legacy importer 写入的 Chroma `vectorstore/` 可被 `load_vector_store(...).similarity_search(...)` 检索到。
- 前端改动必须通过 `cd frontend && npm run typecheck` 和 `cd frontend && npm run build`。

### 7. Wrong vs Correct

#### Wrong

```python
@app.post("/api/knowledge/import")
def import_knowledge_file(request: KnowledgeImportRequest):
    shutil.copy2(source_path, output_path / "vectorstore" / "imported" / source_path.name)
    return OperationResult(success=True, message=f"已导入 {source_path.name}")
```

问题：这只创建了导入副本，没有写入 Chroma。后续章节草稿生成仍检索不到资料。

#### Correct

```python
result = import_knowledge_to_vectorstore(
    embedding_api_key=config.apiKey,
    embedding_url=config.baseUrl,
    embedding_interface_format=config.interfaceFormat,
    embedding_model_name=config.modelName,
    file_path=str(source_path),
    filepath=str(output_path),
)
if not result.success:
    raise HTTPException(status_code=400, detail=result.message)
shutil.copy2(source_path, import_dir / source_path.name)
```

正确做法：先用当前 Embedding 配置写入旧生成链路使用的 Chroma `vectorstore/`，成功后再复制源文件副本。

## WebDAV

- WebDAV 配置写在 `config.json.webdav_config`。
- API 备份/恢复使用远程 `AI_Novel_Generator/config.json`。
- 恢复前应在本地 `backup/` 下创建 `config_*_bak.json`。
- 网络请求使用有限超时，当前 API 约定为 `REQUEST_TIMEOUT = (5, 30)`。

## 禁止事项

- 不提交 `config.json`、`backup/`、`vectorstore/`、生成小说正文或真实密钥。
- 不把前端保存类操作静默落到 mock 数据；保存应走本地 API。
- 不把 SQLite 范围扩大到项目、章节、知识库等业务数据，除非先补设计、规范和测试。
- 不让测试读写真实根目录 `config.json`，必须使用临时路径。

## 代码例子

配置保存使用临时文件和 `os.replace()` 做原子替换，示例来自 `app/api/server.py`：

```python
fd, temp_path = tempfile.mkstemp(suffix=".json", dir=str(config_file.parent))
try:
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=4)
    os.replace(temp_path, config_file)
except Exception:
    os.unlink(temp_path)
    raise
```

旧 GUI 配置管理同样使用锁和原子写入，示例来自 `config_manager.py`：

```python
with _config_lock:
    fd, temp_path = tempfile.mkstemp(suffix='.json', dir=dir_name)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, ensure_ascii=False, indent=4)
    os.replace(temp_path, config_file)
```

密钥字段保存时保留旧值，API 响应不回显密钥正文，示例来自 `app/api/server.py`：

```python
"api_key": item.apiKey or (old_llm_configs.get(item.name) or {}).get("api_key", "")
```

角色库测试展示了当前文件系统持久化合同，示例来自 `tests/test_api_role_library.py`：

```python
role_dir = output_path / "角色库" / "主角"
(role_dir / "林澈.txt").write_text("林澈：调查员", encoding="utf-8")
client = TestClient(create_app(config_file=str(config_file)))
```
