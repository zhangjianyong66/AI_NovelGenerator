# 前端状态持久化补齐设计

## Architecture

本次只保存“前端工作上下文”，不改变后端配置和任务历史语义。持久化使用浏览器 `localStorage`，通过一个小型 TypeScript helper 统一封装读写、JSON 容错和按项目分桶，避免页面各自直接解析存储数据。

持久化 key 使用 `ai-novel-generator.workspaceState.v1`。value 是按 `projectId` 索引的对象，每个项目保存：

- `activeChapterId`
- `activeProjectFileId`
- `generationSelectedJobId`
- `generationBatchForm`

布局折叠偏好继续沿用 `AppLayout.vue` 现有的独立 key，不纳入本次迁移。

## Boundaries

- `frontend/src/services/workspaceStateStorage.ts` 负责 localStorage 读写、容错、类型收窄和字段校验。
- `frontend/src/stores/editor.ts` 负责章节和核心项目文件的选中状态恢复/写入。它仍不保存正文草稿和核心文件草稿。
- `frontend/src/pages/GenerationPage.vue` 负责生成页页面级状态的恢复/写入，因为 `selectedJobId` 和 `batchForm` 当前属于该页面。
- 后端 `serviceBridge`、SQLite 状态库和 `config.json` 不改变。

## Data Flow

1. 项目切换触发 `editorStore.resetProjectState(projectId)`。
2. `loadChapters(projectId)` 加载章节后，从 storage 读取该项目的 `activeChapterId`；若章节存在则恢复，否则选择第一章。
3. `loadProjectFiles(projectId)` 加载核心项目文件后，从 storage 读取该项目的 `activeProjectFileId`；若文件存在则恢复，否则使用默认文件。
4. 用户调用 `selectChapter`、`selectPreviousChapter`、`selectNextChapter`、`createActiveChapter` 或 `selectProjectFile` 后，store 写回当前项目状态。
5. 生成页 mounted 后加载项目、配置、章节和任务，再从 storage 恢复 `batchForm` 与 `selectedJobId`。
6. 用户修改 `batchForm` 或选择任务时，页面写回 storage；任务列表刷新后如果保存的任务不存在，页面回落到首个任务并更新 storage。

## Compatibility

- localStorage 不可用、JSON 损坏、字段类型错误或旧版本缺字段时，helper 返回空对象或默认值，页面继续加载。
- 非法批量参数不阻断恢复，但会先经过数值规范化：章节和字数必须是有限数字，缺失字段用当前默认值；最终仍由页面已有校验给出用户提示。
- 只保存小型字符串、数字和布尔值，不保存正文、密钥、Base URL、代理配置或大体积生成内容。

## Trade-offs

选择 localStorage 而不是后端状态库：这些数据是前端工作上下文，和真实小说配置不同；保存在后端会扩大 API 和迁移范围。后续如果要跨设备恢复 UI 状态，可以再把 helper 后面的存储实现替换为后端接口。

选择自写 helper 而不是引入 Pinia 持久化插件：当前项目没有该依赖，本次字段少且需要按项目隔离和字段白名单，自写 helper 更可控。
