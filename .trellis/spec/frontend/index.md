# Frontend Guidelines

前端工程位于 `frontend/`，使用 Tauri 2 + Vue 3 + TypeScript + Vite。修改前端时优先遵循 `AGENTS.md` 中的项目级约定，并阅读本目录下与任务相关的契约文档。

## Pre-Development Checklist

- [ ] 读取 `AGENTS.md` 中的前端目录、运行命令、服务边界和 UI 组件约定。
- [ ] 涉及真实后端、Mock fallback、保存/导入/生成/WebDAV 等写操作时，读取 [service-bridge-real-backend.md](./service-bridge-real-backend.md)。
- [ ] 页面和 store 不直接调用 `mockApi`，统一通过 `frontend/src/services/serviceBridge.ts`。
- [ ] 修改页面后至少运行 `cd frontend && npm run typecheck` 和 `cd frontend && npm run build`。
- [ ] 涉及真实接口闭环时，用临时输出目录执行浏览器或 API 冒烟，并避免提交 `config.json`、输出目录和密钥。

## Quality Check

- [ ] 所有读/写路径的数据来源状态清晰：真实后端、离线预览或断线。
- [ ] 写操作在非真实后端模式下禁用或提前提示，不静默写入 mock。
- [ ] 页面复用 `components/ui/` 与 `features/` 中已有组件，不重复维护任务、角色、日志、编辑器等状态逻辑。
- [ ] 生成任务页面明确 queued 任务不等于真实 LLM 生成完成；设定、目录、草稿、定稿、批量草稿、批量定稿、批量审校和审校已接入真实执行器，审校结果写入任务日志。
- [ ] 工作台与章节编辑职责边界保持一致：工作台编辑核心项目文件，章节页编辑 `chapter_X.txt`。
