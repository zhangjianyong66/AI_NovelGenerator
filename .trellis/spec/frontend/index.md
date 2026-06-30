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

## Scenario: 前端工作上下文持久化

### 1. Scope / Trigger

- Trigger: 页面需要在刷新、重开前端或切换页面后恢复“用户正在看哪里/准备生成什么”的轻量工作上下文。
- Scope: 章节/工作台选中项、生成页选中任务、生成页批量参数。
- 不适用：真实业务配置、正文草稿、模型密钥、后端任务状态和输出文件内容。

### 2. Signatures

- `frontend/src/services/workspaceStateStorage.ts`
- `getProjectWorkspaceState(projectId: string): ProjectWorkspaceState`
- `updateProjectWorkspaceState(projectId: string, patch: ProjectWorkspaceState): void`
- `normalizeGenerationBatchForm(input: unknown): GenerationBatchFormState`
- localStorage key: `ai-novel-generator.workspaceState.v1`

```ts
interface ProjectWorkspaceState {
  activeChapterId?: string
  activeProjectFileId?: ProjectFileId
  generationSelectedJobId?: string
  generationBatchForm?: {
    startChapter: number
    endChapter: number
    targetWords: number
    minimumWords: number
    autoEnrich: boolean
  }
}
```

### 3. Contracts

- 状态必须按 `projectId` 分桶，切换项目不得沿用上一个项目的章节、项目文件、任务选择或批量参数。
- 恢复选中项时必须先确认该 id 仍存在于当前后端返回列表；不存在时回落到当前列表第一项或默认值。
- 该机制只保存小型 UI 工作上下文字段。禁止保存章节正文、核心项目文件正文、API Key、密码、Base URL、代理地址和生成的大体积内容。
- 当前章节号、小说参数、模型配置和 WebDAV 配置继续通过后端配置接口保存，不通过 `workspaceStateStorage` 代替。

### 4. Validation & Error Matrix

| Condition | Expected |
| --- | --- |
| `localStorage` 不可用或写入失败 | 静默忽略，页面继续使用内存状态 |
| JSON 损坏或不是对象 | 读取为空状态，页面使用默认值 |
| 保存的章节/任务/文件 id 不存在 | 回落到当前列表第一项或默认文件 |
| 批量参数字段缺失、非数字或负数 | 使用默认值或归一化到非负数，最终仍由页面现有校验提示 |

### 5. Good/Base/Bad Cases

- Good: `editorStore.loadChapters(projectId)` 读取保存的 `activeChapterId`，只有章节仍存在时才恢复。
- Base: 生成页没有保存状态时使用默认批量参数 `1-1`、`3000/2000`、不开启自动扩写。
- Bad: 把 `projectConfig.novelParams.chapterNum` 只保存到 localStorage，导致后端生成任务继续使用旧配置。
- Bad: 把编辑器正文草稿写入 `workspaceStateStorage`，造成大体积本地状态和隐私泄漏风险。

### 6. Tests Required

- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`
- 静态合约或单元测试覆盖：按项目隔离、损坏 JSON 容错、批量参数归一化、字段白名单不包含正文和密钥。

### 7. Wrong vs Correct

#### Wrong

```ts
window.localStorage.setItem('chapterDraft', editorStore.activeChapterDraft)
```

#### Correct

```ts
updateProjectWorkspaceState(projectId, {
  activeChapterId: editorStore.activeChapterId,
})
```
