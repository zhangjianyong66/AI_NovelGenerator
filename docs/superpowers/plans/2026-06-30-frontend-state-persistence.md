# 前端状态持久化补齐 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让章节/工作台选择、生成页批量参数和生成任务选择在刷新或重开前端后按项目恢复。

**Architecture:** 新增一个小型 `workspaceStateStorage` helper 统一管理 `localStorage` 中的按项目工作上下文。编辑器 store 负责章节和项目文件选中项恢复；生成页负责页面级批量参数和选中任务恢复。真实项目配置、任务历史、密钥和正文内容不进入该本地持久化。

**Tech Stack:** Vue 3、Pinia、TypeScript、Vite、浏览器 `localStorage`。

---

### Task 1: 工作上下文存储 Helper

**Files:**
- Create: `frontend/src/services/workspaceStateStorage.ts`

- [ ] **Step 1: 新增类型和默认值**

```ts
export interface GenerationBatchFormState {
  startChapter: number
  endChapter: number
  targetWords: number
  minimumWords: number
  autoEnrich: boolean
}

export interface ProjectWorkspaceState {
  activeChapterId?: string
  activeProjectFileId?: string
  generationSelectedJobId?: string
  generationBatchForm?: GenerationBatchFormState
}

const storageKey = 'ai-novel-generator.workspaceState.v1'
```

- [ ] **Step 2: 实现容错读写**

读写函数必须捕获 `localStorage` 和 JSON 异常，异常时返回空对象或静默忽略写入。

- [ ] **Step 3: 实现按项目 merge 更新**

导出：

```ts
export function getProjectWorkspaceState(projectId: string): ProjectWorkspaceState
export function updateProjectWorkspaceState(projectId: string, patch: ProjectWorkspaceState): void
export function normalizeGenerationBatchForm(input: unknown): GenerationBatchFormState
```

### Task 2: 编辑器 Store 恢复章节和项目文件

**Files:**
- Modify: `frontend/src/stores/editor.ts`
- Modify: `frontend/src/layouts/AppLayout.vue`

- [ ] **Step 1: 在 store 中记录当前项目**

`state` 增加 `activeProjectId`。`resetProjectState(projectId = '')` 清空内存内容并设置 `activeProjectId = projectId`。

- [ ] **Step 2: 章节加载后恢复选中项**

`loadChapters(projectId)` 加载章节后读取 `getProjectWorkspaceState(projectId).activeChapterId`，只有该 id 仍存在于 `chapters` 时才恢复，否则使用第一章。

- [ ] **Step 3: 选择动作写回存储**

`selectChapter`、`selectPreviousChapter`、`selectNextChapter`、`createActiveChapter` 成功后调用 `updateProjectWorkspaceState(activeProjectId, { activeChapterId })`。

- [ ] **Step 4: 项目文件加载和选择写回存储**

`loadProjectFiles()` 用 `activeProjectId` 读取 `activeProjectFileId`；`selectProjectFile` 写回 storage。

- [ ] **Step 5: AppLayout 传入项目 id**

把 `editorStore.resetProjectState()` 改为 `editorStore.resetProjectState(projectId)`。

### Task 3: 生成页恢复批量参数和选中任务

**Files:**
- Modify: `frontend/src/pages/GenerationPage.vue`

- [ ] **Step 1: 复用 helper 默认值和归一化**

从 `workspaceStateStorage` 引入批量表单默认值或归一化函数，让 `batchForm` 初始值来自同一个默认来源。

- [ ] **Step 2: mounted 后按项目恢复**

在项目和任务列表加载完成后读取项目 workspace state：

- `batchForm` 使用 `normalizeGenerationBatchForm(saved.generationBatchForm)`。
- `selectedJobId` 只有仍存在于 `jobs` 时恢复，否则使用 `jobs[0]?.id ?? ''`。

- [ ] **Step 3: watch 写回**

监听 `batchForm` 深层变化和 `selectedJobId`，写入 `updateProjectWorkspaceState(projectId, ...)`。没有 `activeProjectId` 时不写。

- [ ] **Step 4: 任务列表变化时保持合法选择**

保留现有 `watch(jobs, ...)` 刷新上下文逻辑，并在选择回落到首个任务时写回 storage。

### Task 4: 验证

**Files:**
- No source file expected.

- [ ] **Step 1: 类型检查**

Run: `cd frontend && npm run typecheck`

Expected: exit code 0。

- [ ] **Step 2: 构建**

Run: `cd frontend && npm run build`

Expected: exit code 0。

- [ ] **Step 3: 静态审查**

确认 storage helper 只保存小型工作上下文字段，不保存正文、密钥、Base URL、代理或生成内容。
