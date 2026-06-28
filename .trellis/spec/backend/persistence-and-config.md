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

## 向量库和知识库

- 向量库默认在当前输出目录的 `vectorstore/`。
- 切换 Embedding 模型后建议清空 `vectorstore/`，避免旧向量污染检索。
- 知识导入接口当前把本地文件复制到 `vectorstore/imported/`。
- 清理向量库会删除整个 `vectorstore/`，因此 UI 和 API 文案必须明确这是破坏性操作。

参考文件：

- `novel_generator/vectorstore_utils.py`
- `novel_generator/knowledge.py`
- `app/api/server.py`
- `tests/test_api_knowledge_tools.py`

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
