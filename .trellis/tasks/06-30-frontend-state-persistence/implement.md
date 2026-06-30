# 前端状态持久化补齐实施计划

## Checklist

- [x] 新增 `frontend/src/services/workspaceStateStorage.ts`，定义工作上下文类型、默认批量表单、按项目读写函数和容错 JSON 解析。
- [x] 修改 `frontend/src/stores/editor.ts`：增加当前项目 id，`resetProjectState(projectId)` 接收项目 id；`loadChapters` / `loadProjectFiles` 从 storage 恢复选中项；所有选择动作写回 storage。
- [x] 修改 `frontend/src/layouts/AppLayout.vue`：调用 `editorStore.resetProjectState(projectId)`，保持项目切换时按项目恢复状态。
- [x] 修改 `frontend/src/pages/ChaptersPage.vue` 和 `WorkspacePage.vue`：必要时适配 `resetProjectState` 签名，不改变现有未保存变更确认行为。
- [x] 修改 `frontend/src/pages/GenerationPage.vue`：用 storage 默认值初始化 `batchForm`，mounted 后按项目恢复批量参数和选中任务；watch 表单和任务选择写回 storage。
- [x] 运行 `cd frontend && npm run typecheck`。
- [x] 运行 `cd frontend && npm run build`。

## Validation Notes

- 手工静态检查：搜索 `activeChapterId = this.activeChapterId ||` 这类只依赖内存的回落逻辑，确认已改为“storage 命中且存在于列表时恢复，否则回落默认值”。
- 手工静态检查：搜索新 storage helper 的保存字段，确认没有正文、API Key、密码、Base URL、代理地址或大体积内容。
- 失败回滚点：若生成页恢复逻辑影响任务列表选择，应先保留批量表单持久化，撤回任务选择恢复。
