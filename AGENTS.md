# 项目说明

- 本项目是 Python `customtkinter` 桌面 GUI 应用，主入口为 `main.py`。
- 推荐 Python 版本为 3.10-3.12；README 标注最低 Python 3.9+。
- 依赖通过 `requirements.txt` 安装：`pip install -r requirements.txt`。
- 本地运行命令：`python main.py`。
- 启动时会读取项目根目录的 `config.json`；如果不存在，`config_manager.py` 会自动创建默认配置。
- `config.json` 包含 API Key、模型、代理、WebDAV 和小说参数等本地配置，已被 `.gitignore` 忽略，不应提交。
- 输出路径由 GUI 中的 `filepath` 参数决定；常见生成物包括 `Novel_setting.txt`、`Novel_directory.txt`、`chapter_X.txt`、`outline_X.txt`、`global_summary.txt`、`character_state.txt`、`plot_arcs.txt` 和 `vectorstore/`。
- 使用本地 Ollama Embedding 时，需要先启动 Ollama 并拉取模型，例如 `ollama serve` 和 `ollama pull nomic-embed-text`。
- 切换不同 Embedding 模型后，建议清空 `vectorstore/`，避免旧向量库影响检索。
- UI 字体与控件缩放集中定义在 `ui/styles.py`；新增或调整 CustomTkinter 界面时优先使用 `UI_FONT`、`EDITOR_FONT`、`SMALL_FONT`、`BOLD_FONT`、`TITLE_FONT` 和 `WIDGET_SCALING`，避免重新散落硬编码字体元组。该模块会按系统选择中文字体，Linux/Ubuntu 优先使用 `Noto Sans CJK SC` 等中文字体，Windows 优先使用 `Microsoft YaHei`。
- `frontend/` 是与现有 Python GUI 并行演进的 Tauri 2 + Vue 3 + TypeScript + Vite 前端工程；不会替代 `python main.py`。
- 前端依赖通过 `cd frontend && npm install` 安装；常用命令包括 `npm run dev`、`npm run typecheck`、`npm run build` 和 `npm run tauri:dev`。
- 前端源码目录约定：`src/router/` 管理路由，`src/layouts/` 管理应用壳层，`src/pages/` 放页面，`src/components/` 放通用组件，`src/stores/` 放 Pinia UI 状态，`src/services/` 放类型和 mock service，`src/styles/` 放全局样式 token。
- 当前前端仅使用 `src/services/mockApi.ts` 中的 mock 数据，不调用真实 Python 后端、不执行小说生成、不持久化配置、不操作向量库；后续后端服务化后再替换 mock service。
- 前端构建产物和安装产物已忽略：`frontend/node_modules/`、`frontend/dist/`、`frontend/src-tauri/target/` 不应提交。
- 当前测试可用 `python -m pytest tests` 运行；若环境缺少 pytest，先安装测试依赖或使用项目环境中的测试工具。
- 架构重构计划放在 `docs/superpowers/plans/`；主计划为 `2026-06-24-architecture-refactor.md`，执行时先读取主计划和对应 milestone 子计划。

# 协作约定

- 回答和计划默认使用中文。
- Git commit message 使用中文，推荐 Conventional Commits 格式，例如 `fix(ui): 修复配置保存异常`。
- 不要提交密钥、真实账号、私有 Base URL 或生成的大体积小说输出。
