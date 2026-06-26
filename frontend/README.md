# Tauri + Vue 前端

这是 AI Novel Generator 的下一代前端工程骨架，与现有 Python `customtkinter` GUI 并行存在。

## 环境

- Node.js 18+
- Rust stable
- Tauri 2 所需系统 WebView 依赖

## 命令

```bash
cd frontend
npm install
npm run dev
npm run typecheck
npm run build
npm run tauri:dev
```

本地真实 API 可在项目根目录启动：

```bash
uvicorn app.api.server:app --reload --host 127.0.0.1 --port 8000
```

现有生产 GUI 入口不变：

```bash
python main.py
```

## 边界

- 前端默认通过 `src/services/serviceBridge.ts` 访问 `http://127.0.0.1:8000` 的本地 FastAPI 服务。
- 如需修改 API 地址，可在 `frontend/.env.local` 设置 `VITE_API_BASE_URL`。
- 后端不可用时，读类数据允许降级到 `src/services/mockApi.ts` 展示；真实保存类操作应走本地 API。
- 当前本地 API 已覆盖项目配置、模型设置、核心项目文件、章节、生成任务、知识工具、角色库和 WebDAV 配置。
- 生成任务接口当前返回排队状态和日志，尚未接入真实 LLM 执行器。
