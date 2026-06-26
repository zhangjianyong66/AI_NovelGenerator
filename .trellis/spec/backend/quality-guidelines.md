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

## 测试约定

- API 测试使用 `fastapi.testclient.TestClient` 和 `create_app(config_file=str(tmp_path / "config.json"))`。
- 测试应创建临时 `config.json` 和输出目录，不读写仓库根目录真实配置。
- 配置保存测试要断言 legacy 字段仍保留，例如保存项目配置后 `llm_configs` 不丢失。
- 新增接口至少覆盖成功路径、关键错误路径和持久化结果。
- 解析器和纯函数优先写直接单元测试，例如 `tests/test_chapter_directory_parser.py`。

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
