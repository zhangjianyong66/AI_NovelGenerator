# 项目说明

- 本项目是 Python `customtkinter` 桌面 GUI 应用，主入口为 `main.py`。
- 推荐 Python 版本为 3.10-3.12；README 标注最低 Python 3.9+。
- 依赖通过 `requirements.txt` 安装：`pip install -r requirements.txt`。
- 本地运行命令：`python main.py`。
- 启动时会读取项目根目录的 `config.json`；如果不存在，`config_manager.py` 会自动创建默认配置。
- `config.json` 包含 API Key、模型、代理、WebDAV 和小说参数等本地配置，已被 `.gitignore` 忽略，不应提交。
- 本地 API 读取 `config.json` 时，如果 `other_params.filepath` 缺失或为空，会自动创建并写回配置文件同级的 `output/` 作为默认输出目录；根目录 `output/` 已被 `.gitignore` 忽略。
- 输出路径由 GUI 中的 `filepath` 参数决定；常见生成物包括 `Novel_setting.txt`、`Novel_directory.txt`、`chapter_X.txt`、`outline_X.txt`、`global_summary.txt`、`character_state.txt`、`plot_arcs.txt` 和 `vectorstore/`。
- 使用本地 Ollama Embedding 时，需要先启动 Ollama 并拉取模型，例如 `ollama serve` 和 `ollama pull nomic-embed-text`。
- 切换不同 Embedding 模型后，建议清空 `vectorstore/`，避免旧向量库影响检索。
- 项目功能地图与前端验收剧本放在 `docs/feature-map-and-acceptance.md`；不熟悉原项目或验收新前端时先阅读该文档，确认旧 GUI、新前端和本地 API 的职责边界。
- 新前端要从“可编辑工作台”变成“可真实创作工具”时，优先级记录在 `docs/feature-map-and-acceptance.md` 的“新前端真实可用开发顺序”：先做真实生成执行器最小闭环，再做章节草稿/定稿闭环、任务持久化与可恢复工作流、知识库真实向量化、项目管理和章节生命周期补齐；不要优先扩大纯视觉 UI 重构。
- UI 字体与控件缩放集中定义在 `ui/styles.py`；新增或调整 CustomTkinter 界面时优先使用 `UI_FONT`、`EDITOR_FONT`、`SMALL_FONT`、`BOLD_FONT`、`TITLE_FONT` 和 `WIDGET_SCALING`，避免重新散落硬编码字体元组。该模块会按系统选择中文字体，Linux/Ubuntu 优先使用 `Noto Sans CJK SC` 等中文字体，Windows 优先使用 `Microsoft YaHei`。
- `frontend/` 是与现有 Python GUI 并行演进的 Tauri 2 + Vue 3 + TypeScript + Vite 前端工程；不会替代 `python main.py`。
- 前端依赖通过 `cd frontend && npm install` 安装；常用命令包括 `npm run dev`、`npm run typecheck`、`npm run build` 和 `npm run tauri:dev`。
- 前后端联调可从项目根目录运行 `./scripts/dev.sh`，脚本会同时启动 `uvicorn app.api.server:app` 和 `frontend` Vite dev server，并设置 `VITE_API_BASE_URL` 指向本地 API；可用 `API_HOST`、`API_PORT`、`FRONTEND_HOST`、`FRONTEND_PORT` 覆盖默认 `127.0.0.1:8000` 和 `127.0.0.1:1420`。
- `./scripts/dev.sh` 启动后端和健康检查时会按 `PYTHON` 环境变量、`.venv/bin/python`、`venv/bin/python`、`python3`、`python` 的顺序选择解释器；如需指定虚拟环境解释器，可用 `PYTHON=/path/to/python ./scripts/dev.sh` 覆盖。
- 前端源码目录约定：`src/router/` 管理路由，`src/layouts/` 管理应用壳层，`src/pages/` 放页面，`src/components/` 放通用组件，`src/features/` 放业务 feature 模块，`src/stores/` 放 Pinia UI 状态，`src/services/` 放类型和 mock service，`src/styles/` 放全局样式 token。
- 前端通用 UI 组件集中放在 `frontend/src/components/ui/`，当前包括 `PageHeader`、`ActionBar`、`StatusMessage`、`FormSection`、`Tabs`、`LongTextEditor`、`ConfirmPanel`、`AppButton`、`IconButton`、字段组件、`Toolbar`、`SplitPane`、空/加载/保存状态组件；新增页面应优先复用这些组件来呈现页面标题、操作栏、状态提示、表单分组、tabs、长文本编辑/查看和破坏性操作确认。
- 前端写作编辑相关业务组件放在 `frontend/src/features/writing/`；`WritingEditor` 是章节正文和核心项目文件编辑的适配层，第一阶段底层仍是增强版 `textarea`，页面不应直接依赖底层编辑器实现。
- 前端主导航顺序按写作流程组织为：项目 → 工作台 → 章节编辑 → 生成任务 → 知识库 → 设置；页面标题和信息架构应继续遵循该流程。
- 工作台页使用 `features/writing` 中的 `WorkbenchLayout` 三轨结构：左轨放项目文件和章节导航，中间放 `WritingEditor` 编辑核心项目文件，右轨放上下文资料、任务状态和日志摘要；章节正文编辑与保存由独立“章节编辑”页负责。Tauri 窗口 `minWidth` 当前为 900，以支持窄桌面降级。
- 全局应用壳层 `frontend/src/layouts/AppLayout.vue` 支持左侧主导航和右侧项目状态栏折叠；左侧折叠后保留 64px 图标栏，右侧折叠后隐藏项目状态栏。折叠偏好保存在浏览器 `localStorage`，key 为 `ai-novel-generator.layout.navCollapsed` 和 `ai-novel-generator.layout.contextCollapsed`。
- 前端生成任务业务组件放在 `frontend/src/features/generation/`，当前包括生成动作组、任务列表和任务详情/日志查看；知识库业务组件放在 `frontend/src/features/knowledge/`，当前包括知识文件列表和角色库编辑器。生成页、知识库页应优先复用这些 feature 组件，避免在页面内重复维护任务状态标签、日志查看、角色列表和角色编辑模板。
- 设置页按 tabs 分组为项目参数、LLM、Embedding、阶段模型/代理、WebDAV；知识库页按 tabs 分组为知识文件、剧情要点、角色库；生成页分为任务创建、批量参数、任务列表、任务详情/日志区域。
- `app/api/server.py` 是前端真实接入使用的本地 FastAPI 最小服务边界；开发时可用 `uvicorn app.api.server:app --reload --host 127.0.0.1 --port 8000` 启动本地 API。
- 本地 API 已提供 `GET /health`、`GET /api/projects`、`GET/PUT /api/project-config`、`GET/PUT /api/model-settings` 和 `POST /api/model-settings/test-llm`；项目配置接口读写根目录 `config.json` 的 `other_params.filepath`、`topic`、`genre`、`num_chapters`、`word_number`、`chapter_num`、`user_guidance`、`characters_involved`、`key_items`、`scene_location`、`time_constraint`，响应给前端时使用 camelCase 字段。
- 模型设置接口读写 `config.json` 的 `llm_configs`、`embedding_configs`、`choose_configs`、`proxy_setting`、`last_interface_format` 和 `last_embedding_interface_format`；响应时 `apiKey` 置空并用 `hasApiKey` 表示是否已有密钥，保存时空 `apiKey` 会保留同名旧密钥。
- 核心项目文件接口为 `GET /api/project-files` 和 `PUT /api/project-files/{file_id}`，固定支持 `novelSetting` → `Novel_setting.txt`、`novelDirectory` → `Novel_directory.txt`、`characterState` → `character_state.txt`、`globalSummary` → `global_summary.txt`；文件目录来自 `config.json` 的 `other_params.filepath`。
- 章节接口为 `GET /api/projects/{project_id}/chapters` 和 `PUT /api/chapters/{chapter_number}`；当前按 `other_params.filepath` 下的 `chapter_<数字>.txt` 读取和保存，并尝试从 `Novel_directory.txt` 补章节标题和简述。
- 生成任务接口为 `POST /api/generation-jobs`、`GET /api/projects/{project_id}/jobs`、`GET /api/generation-jobs/{job_id}`；当前支持 `architecture`、`directory`、`draft`、`finalization`、`consistency` 和 `batch`，以 in-memory job registry 保存任务状态和日志。`batch` 请求支持 `startChapter`、`endChapter`、`targetWords`、`minimumWords`、`autoEnrich`。
- 生成任务的 `architecture` 和 `directory` 阶段已通过 `app/services/generation_executor.py` 接入同步真实执行器：`architecture` 调用旧 `Novel_architecture_generate(...)` 后同步 `Novel_architecture.txt` 到前端读取的 `Novel_setting.txt`，`directory` 调用旧 `Chapter_blueprint_generate(...)` 并写入 `Novel_directory.txt`；草稿、定稿、审校和批量仍是待后续接入的任务记录边界。
- 知识工具接口为 `GET /api/knowledge`、`POST /api/knowledge/import`、`POST /api/knowledge/clear-vectorstore`、`GET /api/knowledge/plot-arcs`；当前导入会把指定本地文件复制到当前输出目录的 `vectorstore/imported/`，清理会删除 `vectorstore/`，剧情要点读取 `plot_arcs.txt`；知识列表会汇总 `vectorstore/imported/` 下的导入文件和 `角色库/<分类>/<角色名>.txt` 角色文件。
- 角色库接口为 `GET /api/roles`、`GET/PUT /api/roles/{category}/{role_name}`、`POST /api/roles/import`；当前兼容输出目录下 `角色库/<分类>/<角色名>.txt`，前端可将选中角色名写入项目配置的 `characters_involved`。
- WebDAV 接口为 `GET/PUT /api/webdav-config`、`POST /api/webdav/test`、`POST /api/webdav/backup`、`POST /api/webdav/restore`；配置读写 `config.json` 的 `webdav_config`，响应时密码置空并用 `hasPassword` 表示是否已有密码，备份/恢复使用远程 `AI_Novel_Generator/config.json`，恢复前会在本地 `backup/` 下创建 `config_*_bak.json`。
- 前端真实 API 地址默认使用 `http://127.0.0.1:8000`；如需修改，在 `frontend/.env.local` 中设置 `VITE_API_BASE_URL`。
- 前端真实/Mock 数据访问应通过 `frontend/src/services/serviceBridge.ts` 统一进入，页面和 store 不应新增对 `mockApi` 的直接依赖。
- 当前前端已开始通过 `src/services/serviceBridge.ts` 调用真实本地后端；后端不可用时允许降级到 `src/services/mockApi.ts` 展示数据，但真实保存类操作应走后端接口，不应让页面直接调用 mock。
- `frontend/src/services/serviceBridge.ts` 也是前端后端模式与写操作守卫的统一来源；页面需要使用 `getModeLabel`、`canWrite`、`getWriteUnavailableMessage` 这类共享判断来展示“本地后端已连接/离线预览/本地后端未连接”，并在非真实后端模式下禁用保存、导入、生成、WebDAV 等写操作。
- 前端构建产物和安装产物已忽略：`frontend/node_modules/`、`frontend/dist/`、`frontend/src-tauri/target/` 不应提交。
- 当前测试可用 `python -m pytest tests` 运行；若环境缺少 pytest，先安装测试依赖或使用项目环境中的测试工具。
- 架构重构计划放在 `docs/superpowers/plans/`；主计划为 `2026-06-24-architecture-refactor.md`，执行时先读取主计划和对应 milestone 子计划。

# 协作约定

- 回答和计划默认使用中文。
- Git commit message 使用中文，推荐 Conventional Commits 格式，例如 `fix(ui): 修复配置保存异常`。
- 不要提交密钥、真实账号、私有 Base URL 或生成的大体积小说输出。
<!-- TRELLIS:START -->
# Trellis Instructions

These instructions are for AI assistants working in this project.

This project is managed by Trellis. The working knowledge you need lives under `.trellis/`:

- `.trellis/workflow.md` — development phases, when to create tasks, skill routing
- `.trellis/spec/` — package- and layer-scoped coding guidelines (read before writing code in a given layer)
- `.trellis/workspace/` — per-developer journals and session traces
- `.trellis/tasks/` — active and archived tasks (PRDs, research, jsonl context)

If a Trellis command is available on your platform (e.g. `/trellis:finish-work`, `/trellis:continue`), prefer it over manual steps. Not every platform exposes every command.

If you're using Codex or another agent-capable tool, additional project-scoped helpers may live in:
- `.agents/skills/` — reusable Trellis skills
- `.codex/agents/` — optional custom subagents

Managed by Trellis. Edits outside this block are preserved; edits inside may be overwritten by a future `trellis update`.

<!-- TRELLIS:END -->
