# AI NovelGenerator 项目规范索引

本目录记录当前仓库的项目级开发约定。虽然目录名仍为 `backend`，规范覆盖现有 Python 桌面 GUI、本地 FastAPI API，以及并行演进的 `frontend/` Tauri + Vue 工程。

## 适用范围

- Python 入口与旧 GUI：`main.py`、`ui/`
- 小说生成核心：`novel_generator/`、`llm_adapters.py`、`embedding_adapters.py`、`prompt_definitions*.py`
- 本地 API：`app/api/server.py`
- 前端工程：`frontend/`
- 测试：`tests/`
- 项目计划与运行文档：`docs/superpowers/plans/`、`AGENTS.md`

## 开发前检查

修改代码前按任务读取对应规范：

- 改目录、模块边界、入口或部署方式：读 [Directory Structure](./directory-structure.md)
- 改数据库、ORM、迁移或持久化方案：读 [Database Guidelines](./database-guidelines.md) 和 [Persistence And Config](./persistence-and-config.md)
- 改配置、输出文件、向量库、角色库或 WebDAV：读 [Persistence And Config](./persistence-and-config.md)
- 改 API、异常展示、前后端错误合约：读 [Error Handling](./error-handling.md)
- 改 Python、Vue、测试或构建脚本：读 [Quality Guidelines](./quality-guidelines.md)
- 改日志、调试输出、密钥处理：读 [Logging Guidelines](./logging-guidelines.md)

始终同时阅读共享思考指南：

- `.trellis/spec/guides/index.md`

## 常用命令

Python 环境：

```bash
pip install -r requirements.txt
python main.py
python -m pytest tests
uvicorn app.api.server:app --reload --host 127.0.0.1 --port 8000
```

前端环境：

```bash
cd frontend
npm install
npm run dev
npm run typecheck
npm run build
npm run tauri:dev
```

## 交付边界

- 不提交 `config.json`、API Key、私有 Base URL、真实账号、小说生成输出、`vectorstore/`、`backup/`、`frontend/node_modules/`、`frontend/dist/`、`frontend/src-tauri/target/`。
- 迁移期间保持 `python main.py` 可运行；`frontend/` 是并行前端，不默认替代旧 GUI。
- Git commit message 使用中文，推荐 Conventional Commits，例如 `fix(api): 修复配置保存异常`。
