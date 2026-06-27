# Quality Guidelines

本项目质量目标是保持旧 GUI 可运行，同时让本地 API、前端和未来服务化重构有清晰边界。改动应小步、可测试、兼容既有输出目录格式。

## Python 代码风格

- 使用 Python 3.10-3.12 兼容语法；README 标注最低 3.9+，但当前类型写法已经使用 `str | Path` 等较新语法。
- 保持 UTF-8 文件读写，涉及中文内容时使用 `ensure_ascii=False`。
- 新增 API model 使用 Pydantic `BaseModel`，字段名面向前端使用 camelCase。
- 新增文件路径逻辑优先用 `pathlib.Path`；旧模块已有 `os.path` 时可以局部沿用，不做无关重构。
- 避免在 GUI、API、生成核心之间复制同一段配置映射或文件名映射；共享映射放在边界 owner 附近。
- CustomTkinter 新控件优先复用 `ui/styles.py` 的字体和缩放常量，避免散落硬编码字体元组。

## FastAPI 代码风格

- `create_app(config_file: str | Path | None = None)` 是测试隔离入口。新增 API 时保持可注入配置路径。
- handler 使用 `response_model`，返回 Pydantic model 或简单 dict。
- 与 legacy `config.json` 的转换放在 `_xxx_from_legacy()` / `_merge_xxx()` 这类 helper 中，测试覆盖双向映射。
- 对前端保存操作不要写 mock fallback；真实保存必须落到本地 API 和文件系统。

## 前端代码风格

- Vue 3 + TypeScript + Vite；状态使用 Pinia。
- 页面目录遵循写作流程：项目 → 工作台 → 章节编辑 → 生成任务 → 知识库 → 设置。
- 通用组件优先放在 `frontend/src/components/ui/`，复用现有 `PageHeader`、`ActionBar`、`StatusMessage`、`FormSection`、`Tabs`、`LongTextEditor`、`ConfirmPanel`。
- API 类型集中在 `frontend/src/services/types.ts`；服务调用集中在 `serviceBridge.ts`。
- 前端真实 API 地址默认 `http://127.0.0.1:8000`，本地覆盖用 `VITE_API_BASE_URL`。

## 测试命令

Python：

```bash
python -m pytest tests
```

前端：

```bash
cd frontend
npm run typecheck
npm run build
```

本地 API 手动检查：

```bash
uvicorn app.api.server:app --reload --host 127.0.0.1 --port 8000
```

前后端联调：

```bash
./scripts/dev.sh
```

该脚本会同时启动 `uvicorn app.api.server:app` 和前端 Vite dev server，并把 `VITE_API_BASE_URL` 指向本地 API。可用 `API_HOST`、`API_PORT`、`FRONTEND_HOST`、`FRONTEND_PORT` 覆盖默认地址。

## 测试约定

- API 测试使用 `fastapi.testclient.TestClient` 和 `create_app(config_file=str(tmp_path / "config.json"))`。
- 测试应创建临时 `config.json` 和输出目录，不读写仓库根目录真实配置。
- 缺失输出目录的 API 测试应断言默认 `output/` 会被创建并写回临时配置，而不是依赖 400 错误。
- 配置保存测试要断言 legacy 字段仍保留，例如保存项目配置后 `llm_configs` 不丢失。
- 新增接口至少覆盖成功路径、关键错误路径和持久化结果。
- 解析器和纯函数优先写直接单元测试，例如 `tests/test_chapter_directory_parser.py`。
- 归档任务中的 `test-cases.md` 可作为前端人工验收清单；如果本轮没有启动应用逐项人工验收 TC-01 到 TC-30，不要标记为全量手工通过。
- 可用 `cdp-browser-chrome` MCP 做前端浏览器冒烟测试：启动 `./scripts/dev.sh`，若默认端口被占用则用 `API_PORT` / `FRONTEND_PORT` 覆盖；通过 CDP 检查主路由渲染、后端连接状态和关键按钮交互。
- CDP 冒烟测试不能替代外部服务或破坏性手工项，例如 WebDAV 备份/恢复、清理向量库、真实文件导入；这些项目必须在验收结论中列为未覆盖或需人工确认。
- 当前 CDP 工具未暴露稳定的 viewport resize 能力；响应式 TC-29 若要求约 900px 宽度，应通过可控浏览器窗口或 Playwright 类工具补测，不要仅凭默认视口结论替代。

## 禁止模式

- 直接提交或测试依赖根目录 `config.json`。
- 在页面或 store 中直接调用 `mockApi`，绕过 `serviceBridge.ts`。
- 在多个文件重复定义同一套 API payload 字段、配置字段映射或输出文件名。
- 为未实现的 SQLite 架构创建空壳目录或伪迁移。
- 大范围重排旧 GUI 文件，只为“顺手整理”。
- 改模型配置时泄露 API Key、真实账号或私有 Base URL 到日志、测试快照或文档。

## 代码审查清单

- `python main.py` 入口是否仍可用。
- `python -m pytest tests` 是否通过。
- 前端改动是否通过 `npm run typecheck`，必要时通过 `npm run build`。
- 配置字段是否同时更新 Python API、前端类型、测试和项目说明。
- 保存类操作是否真实持久化，而不是 mock 成功。
- `.gitignore` 中禁止提交的产物是否没有进入变更。

## 代码例子

API 测试必须通过临时配置隔离真实用户配置，示例来自 `tests/test_api_project_config.py`：

```python
config_file = tmp_path / "config.json"
client = TestClient(create_app(config_file=str(config_file)))
response = client.get("/api/project-config")
```

配置兼容测试应断言 legacy 字段仍写回原结构，示例来自 `tests/test_api_project_config.py`：

```python
saved = json.loads(config_file.read_text(encoding="utf-8"))
assert saved["other_params"]["filepath"] == str(tmp_path / "saved-output")
assert saved["other_params"]["num_chapters"] == 36
assert "llm_configs" in saved
```

Pydantic 字段约束应有错误路径测试，示例来自 `tests/test_api_project_config.py`：

```python
response = client.put(
    "/api/project-config",
    json={"outputPath": "", "novelParams": {"numChapters": -1, "wordNumber": 3000}},
)
assert response.status_code == 422
```

文件系统接口测试要同时检查响应和磁盘结果，示例来自 `tests/test_api_role_library.py`：

```python
save_response = client.put("/api/roles/主角/林澈", json={"content": "新内容"})
assert save_response.status_code == 200
assert (role_dir / "林澈.txt").read_text(encoding="utf-8") == "新内容"
```
