## Why

现有 `frontend/` 已完成 Tauri + Vue 工作台骨架，但仍只依赖 mock 数据，无法替代当前 `customtkinter` GUI 的真实配置、文件编辑、生成、知识库、角色库和 WebDAV 能力。现在需要把前端从“可评审的界面骨架”推进到“可逐步承接真实业务操作的桌面工作台”，并通过稳定的本地后端边界避免把 Python 生成逻辑散落到 Vue 页面中。

## What Changes

- 新增前端真实服务接入层，用本地 FastAPI 或 Tauri command 边界替换页面对 `mockApi` 的直接依赖，并保留开发期 mock fallback。
- 补齐项目与配置管理能力，包括输出目录、小说参数、LLM 多配置、Embedding、代理和生成阶段模型选择。
- 补齐章节与项目文件编辑能力，包括加载、保存、字数统计和章节切换，覆盖现有输出目录中的核心文本文件。
- 补齐生成任务能力，包括生成设定、目录、草稿、定稿、批量生成、一致性审校、任务状态、日志和错误展示。
- 补齐知识库、向量库、角色库和 WebDAV 的前端操作入口与后端契约，优先覆盖旧 GUI 的常用流程。
- 保持 `python main.py` 与当前 `customtkinter` GUI 在迁移期间继续可用，不要求本变更一次性删除或替换旧界面。

## Capabilities

### New Capabilities

- `frontend-backend-service-bridge`: 定义 Vue/Tauri 前端调用本地后端服务的边界、错误处理、mock fallback 和运行状态展示。
- `frontend-project-config-management`: 定义前端项目、输出路径、小说参数、模型配置、Embedding、代理和生成阶段模型选择的真实读写行为。
- `frontend-file-editor-workspace`: 定义前端加载、编辑、保存小说设定、目录、角色状态、全局摘要和章节文件的工作区能力。
- `frontend-generation-operations`: 定义前端发起生成设定、目录、草稿、定稿、批量生成和一致性审校，并展示任务状态与日志的能力。
- `frontend-knowledge-role-webdav-tools`: 定义前端知识库导入、向量库清理、剧情要点查看、角色库基础管理和 WebDAV 备份恢复的能力。

### Modified Capabilities

无。

## Impact

- 影响 `frontend/src/services/`、`frontend/src/stores/`、`frontend/src/pages/`、`frontend/src/layouts/` 和相关类型定义。
- 可能新增或扩展 `app/api/`、`app/services/`、`app/client/`、`app/workflows/`、`app/repositories/` 等本地后端模块，以承载前端真实调用。
- 可能新增前端 API 客户端、Tauri 启动/健康检查逻辑、任务轮询或事件订阅逻辑。
- 需要扩展 Python 测试、前端类型检查和构建验证；保持 `python main.py`、现有 Python GUI 和旧输出目录格式兼容。
- 不应提交 `config.json`、API Key、私有 Base URL、生成小说正文、向量库目录或 WebDAV 凭据。
