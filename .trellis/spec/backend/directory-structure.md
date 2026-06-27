# Directory Structure

本项目是一个渐进重构中的本地优先小说生成器：生产入口仍是 Python `customtkinter` 桌面 GUI，同时存在用于新前端接入的 FastAPI 本地 API，以及并行演进的 Tauri 2 + Vue 3 前端。

## 顶层结构

```text
.
├── main.py                         # 现有桌面 GUI 入口
├── config_manager.py               # 根目录 config.json 读写与默认配置
├── llm_adapters.py                 # LLM provider 适配
├── embedding_adapters.py           # Embedding provider 适配
├── chapter_directory_parser.py     # 章节目录解析
├── consistency_checker.py          # 一致性检查
├── prompt_definitions*.py          # 中英文 prompt 定义
├── utils.py                        # 旧 GUI/生成流程通用文件工具
├── novel_generator/                # 设定、目录、章节、定稿、知识库、向量库核心流程
├── ui/                             # CustomTkinter GUI 页面、样式和回调
├── app/api/server.py               # 本地 FastAPI API 边界
├── frontend/                       # Tauri 2 + Vue 3 + TypeScript + Vite 前端
├── tests/                          # pytest 测试，当前重点覆盖 API 与解析器
├── docs/superpowers/plans/         # 架构重构计划和 milestone 子计划
└── .trellis/spec/                  # 面向后续 agent 的项目规范
```

## Python 模块边界

- `main.py` 只负责初始化 CustomTkinter、设置控件缩放并创建 `NovelGeneratorGUI`。不要把业务逻辑塞回入口。
- `ui/` 负责界面布局、用户输入、按钮回调和 UI 状态。新增或调整控件时复用 `ui/styles.py` 中的 `UI_FONT`、`EDITOR_FONT`、`SMALL_FONT`、`BOLD_FONT`、`TITLE_FONT`、`WIDGET_SCALING`。
- `novel_generator/` 放生成流程和核心文件/向量库操作。GUI 不应复制这些流程逻辑；需要复用时通过函数或后续 service 层调用。
- `app/api/server.py` 是当前前端真实接入的最小本地 API 边界。API 层应继续用 Pydantic model 定义请求/响应，用 helper 函数封装 legacy `config.json` 与输出目录格式转换。
- 根目录 `config_manager.py` 仍服务旧 GUI；`app/api/server.py` 内部有独立 `_load_config` / `_save_config` 以支持测试隔离。改配置格式时必须同时确认旧 GUI 和 API 的兼容性。

参考文件：

- `main.py`
- `ui/main_window.py`
- `ui/styles.py`
- `novel_generator/chapter.py`
- `app/api/server.py`
- `config_manager.py`

## 前端结构

```text
frontend/
├── src/router/              # Vue Router
├── src/layouts/             # 应用壳层
├── src/pages/               # 页面：项目、工作台、章节、生成、知识库、设置
├── src/components/ui/       # 通用 UI 组件
├── src/stores/              # Pinia 状态
├── src/services/            # 类型、mock、serviceBridge
├── src/styles/              # 全局样式 token
└── src-tauri/               # Tauri 2 Rust 壳
```

前端真实/Mock 数据访问统一从 `frontend/src/services/serviceBridge.ts` 进入。页面和 store 不应新增对 `mockApi` 的直接依赖。真实后端地址默认是 `http://127.0.0.1:8000`，本地覆盖使用 `frontend/.env.local` 的 `VITE_API_BASE_URL`。

## 运行入口

- 生产 GUI：`python main.py`
- 本地 API：`uvicorn app.api.server:app --reload --host 127.0.0.1 --port 8000`
- 前端开发：`cd frontend && npm run dev`
- 前后端联调：`./scripts/dev.sh`
- Tauri 开发：`cd frontend && npm run tauri:dev`

## 部署与打包

- Python 桌面应用可用 `pyinstaller main.spec` 打包，README 提到需要按本机路径调整 `main.spec` 中的 `customtkinter_dir`。
- Tauri 前端构建使用 `cd frontend && npm run tauri:build`，构建产物在 `frontend/src-tauri/target/`，不提交。
- 迁移期间不要删除或破坏 `python main.py` 入口，除非任务明确要求切换生产入口。

## 命名约定

- Python 文件和函数使用 `snake_case`；保留既有 `chapter_X.txt`、`outline_X.txt`、`Novel_setting.txt`、`Novel_directory.txt` 等输出文件名。
- API 对前端暴露 camelCase 字段，例如 `numChapters`、`wordNumber`、`hasApiKey`；写入 `config.json` 时转换为 legacy snake_case 字段，例如 `num_chapters`、`word_number`。
- Vue 组件使用 `PascalCase.vue`，服务和 store 使用现有小驼峰或复数命名，例如 `serviceBridge.ts`、`projects.ts`。

## 代码例子

API model 字段面向前端使用 camelCase，约束直接放在 Pydantic model 上，示例来自 `app/api/server.py`：

```python
class NovelParams(BaseModel):
    topic: str = ""
    genre: str = ""
    numChapters: int = Field(default=0, ge=0)
    wordNumber: int = Field(default=0, ge=0)
    chapterNum: str = ""
```

输出目录核心文件名由 API 边界统一维护，页面和测试不应重复定义，示例来自 `app/api/server.py`：

```python
CORE_PROJECT_FILES = {
    "novelSetting": ("小说设定", "Novel_setting.txt"),
    "novelDirectory": ("目录蓝图", "Novel_directory.txt"),
    "characterState": ("角色状态", "character_state.txt"),
    "globalSummary": ("全局摘要", "global_summary.txt"),
}
```

旧 GUI 的长耗时操作通过回调把日志和异常送回界面，示例来自 `ui/main_window.py`：

```python
test_llm_config(
    interface_format=interface_format,
    api_key=api_key,
    base_url=base_url,
    model_name=model_name,
    log_func=self.safe_log,
    handle_exception_func=self.handle_exception,
)
```
