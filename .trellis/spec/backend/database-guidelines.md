# Database Guidelines

当前项目没有数据库、ORM 或迁移系统。业务数据仍由本地 `config.json`、输出目录文本文件、角色库目录、WebDAV 配置备份和 Chroma `vectorstore/` 承载。

## 当前真实状态

- 不存在 SQLAlchemy、Alembic、Django ORM、Prisma 或 SQLite schema。
- `app/api/server.py` 的 `create_app(config_file=...)` 通过可注入配置文件支持测试隔离。
- API 和旧 GUI 都读写 legacy `config.json`，但 API 对前端暴露 camelCase Pydantic model。
- 章节、设定、目录、角色库、剧情要点都是输出目录下的 UTF-8 文本文件。
- 向量库是当前输出目录下的 `vectorstore/`，不是关系型数据库。

## 示例

测试隔离入口来自 `app/api/server.py`：

```python
def create_app(config_file: str | Path | None = None) -> FastAPI:
    app = FastAPI(title="AI Novel Generator Local API")
    config_path = Path(config_file) if config_file is not None else DEFAULT_CONFIG_FILE
```

API 测试应使用临时配置文件，例如 `tests/test_api_project_config.py`：

```python
config_file = tmp_path / "config.json"
client = TestClient(create_app(config_file=str(config_file)))
```

章节文件路径仍按 legacy 文件名拼接：

```python
def _chapter_file_path(output_path: Path, chapter_number: int) -> Path:
    return output_path / f"chapter_{chapter_number}.txt"
```

## 引入数据库前的要求

如果后续 milestone 真正引入 SQLite 或其他数据库，必须先更新设计文档和本规范，并明确：

- 数据库文件位置、备份和 `.gitignore` 规则。
- schema owner、迁移工具和迁移执行入口。
- legacy `config.json` 与输出目录文本文件的迁移或双写策略。
- `python main.py` 旧 GUI 的兼容边界。
- API 测试如何创建临时数据库并避免污染真实用户数据。

在上述设计落地前，不要新增空壳迁移目录、伪 ORM 层或只在文档里存在的 repository 抽象。
