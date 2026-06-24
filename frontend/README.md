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

现有生产 GUI 入口不变：

```bash
python main.py
```

## 边界

- 当前前端只使用 `src/services/mockApi.ts` 中的 mock 数据。
- 当前前端不调用 Python 后端、不执行小说生成、不持久化配置、不操作向量库。
- 后续后端服务化完成后，再将 mock service 替换为本地 API 或 Tauri command。
