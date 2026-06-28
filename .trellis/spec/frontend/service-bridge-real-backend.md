# Service Bridge 与真实后端边界

## Scenario: 前端真实后端与离线预览模式

### 1. Scope / Trigger

- Trigger: 前端页面通过 `frontend/src/services/serviceBridge.ts` 同时支持本地 FastAPI 和只读 mock fallback。
- 适用范围：项目页、工作台、章节编辑、生成任务、知识库、设置页，以及任何新增的前端读写接口。

### 2. Signatures

- `serviceBridge.getStatus(): ServiceBridgeStatus`
- `serviceBridge.getModeLabel(mode?: BackendMode): string`
- `serviceBridge.canWrite(statusSnapshot?: ServiceBridgeStatus): boolean`
- `serviceBridge.getWriteUnavailableMessage(statusSnapshot?: ServiceBridgeStatus): string`

```ts
export type BackendMode = 'backend' | 'disconnected' | 'mock'

export interface ServiceBridgeStatus {
  mode: BackendMode
  isLoading: boolean
  health: BackendHealth | null
  error: ServiceBridgeError | null
}
```

### 3. Contracts

- `backend`: 真实本地 FastAPI 可用，页面允许保存、导入、生成、WebDAV 等写操作。
- `mock`: 读类接口允许降级到 `mockApi`，页面必须标记为“离线预览”，并禁用写操作。
- `disconnected`: 未获得可用读 fallback 或写请求失败，页面显示本地后端未连接或请求错误。
- 页面和 store 不直接调用 `mockApi`；所有真实/Mock 数据访问统一通过 `serviceBridge`。
- 写类方法不得提供 mock 写入 fallback，包括但不限于项目配置保存、模型设置保存、核心项目文件保存、章节保存、知识导入、清理向量库、角色保存/导入、生成任务创建、WebDAV 操作。
- 读类 fallback 只能用于展示预览数据，不能让用户误以为正在查看当前真实输出目录。
- 后端返回非 2xx JSON 错误时，`serviceBridge` 应优先把响应体中的 `detail` 或 `message` 作为 `ServiceBridgeError.message` 暴露给页面；页面不应把“章节文件不存在：2”这类可操作错误泛化成“本地后端请求失败”。

### 4. Validation & Error Matrix

| Condition | Expected UI / Error |
| --- | --- |
| `/health` 成功 | 顶部显示“本地后端已连接”，`canWrite` 为 `true` |
| 读类接口请求失败且有 mock fallback | `mode = 'mock'`，页面显示“离线预览”，写按钮禁用 |
| 写类操作在 `mock` 或 `disconnected` 模式触发 | 提前显示 `getWriteUnavailableMessage()`，不发起 mock 写入 |
| 创建计划章节文件 | 必须调用 `serviceBridge.createChapter()`，真实后端不可用时禁用或提前提示 |
| 创建已存在章节文件返回 409 | 显示后端中文错误，不覆盖当前编辑器正文 |
| 章节保存返回 404 | 显示“章节文件不存在”，不自动创建 `chapter_X.txt` |
| 已接入阶段生成任务创建成功 | `architecture`、`directory`、`draft`、`finalization` 同步返回 `done` 或 `failed`，页面展示任务状态、错误和日志 |
| 未接入阶段生成任务创建成功 | `consistency`、`batch` 返回 `queued`，日志说明等待执行器接入，不提示真实生成完成 |
| 生成任务创建返回 400 `{"detail": "章节文件不存在：2"}` | 页面展示“章节文件不存在：2”或带行动建议的等价文案 |

### 5. Good/Base/Bad Cases

- Good: 工作台通过 `serviceBridge.canWrite(bridgeStatus)` 禁用核心文件保存，并把 `WritingEditor` 设为只读。
- Base: 项目页读到 mock 项目卡片时仍可展示，但页面显示离线预览提示。
- Bad: 页面直接调用 `mockApi.saveXxx()` 或在后端不可用时把保存结果写进本地组件状态后显示“已保存”。

### 6. Tests Required

- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`
- 前端源码/合约测试应覆盖生成任务页的真实后端边界：目标章节提示、草稿不要求预先存在章节文件、批量缺章提示、后端错误 `detail` 透传、`queued` 详情解释。
- 真实后端冒烟：
  - 保存项目输出目录。
  - 工作台保存核心项目文件并检查真实文件落盘。
  - 章节页保存已存在 `chapter_1.txt` 并检查真实文件落盘。
  - 创建已接入阶段生成任务并确认 `done` / `failed`、错误和日志展示。
  - 创建未接入阶段生成任务并确认 `queued` 与等待执行器日志。
- 离线预览冒烟：
  - 使用不可用 API 地址启动前端或停止后端。
  - 确认页面显示离线预览或断线状态。
  - 确认保存、导入、生成、WebDAV 等写入口不可用或提前提示。

### 7. Wrong vs Correct

#### Wrong

```ts
// 页面直接判断英文 mode，且保存失败后仍可能落到 mock 展示逻辑。
const disabled = serviceBridge.getStatus().mode !== 'backend'
await mockApi.listProjects()
```

#### Correct

```ts
const bridgeStatus = ref<ServiceBridgeStatus>({ ...serviceBridge.getStatus() })
const canWriteToBackend = computed(() => serviceBridge.canWrite(bridgeStatus.value))
const writeUnavailableMessage = computed(() =>
  serviceBridge.getWriteUnavailableMessage(bridgeStatus.value),
)
```

使用共享 helper 的原因是状态文案、禁写条件和 fallback 语义必须由一个边界拥有，避免页面间出现“有的页面能写 mock、有的页面提示断线”的不一致行为。

## Page Responsibility Contract

- 项目页：展示当前项目、输出路径和小说参数；通过 `serviceBridge.createProject(...)` 和 `serviceBridge.switchProject(...)` 调用真实后端创建、打开和切换本地项目；离线预览或断线时这些写操作必须禁用或提前提示。
- 工作台：只负责核心项目文件编辑闭环；章节导航只作为上下文和跳转线索，不承担章节正文保存。
- 章节编辑页：展示已有章节和计划章节；计划章节来自后端 `status="planned"`，编辑器保持只读，用户必须先通过 `serviceBridge.createChapter(chapterOrder)` 创建缺失的 `chapter_X.txt`，之后才能编辑并通过 `saveChapter` 保存。
- 生成任务页：通过后端创建任务。已接入阶段包括设定、目录、草稿和定稿，会同步真实执行并返回 `done` / `failed`；未接入阶段包括审校和批量，只创建 queued 任务，不承诺生成或修改小说文件。
- 知识库页：读类信息可离线预览；导入、清理、保存角色、写入章节参数必须要求真实后端。

## Scenario: 计划章节创建入口

### 1. Scope / Trigger

- Trigger: 章节列表现在会包含 `status="planned"` 的计划章节，前端需要提供真实创建入口。
- Scope: `frontend/src/services/serviceBridge.ts`、`frontend/src/stores/editor.ts`、`frontend/src/pages/ChaptersPage.vue`。

### 2. Signatures

```ts
serviceBridge.createChapter(chapterOrder: number): Promise<Chapter>
```

后端 API：

```http
POST /api/chapters/{chapter_number}
```

### 3. Contracts

- `createChapter` 是写操作，不允许 mock fallback。
- 章节页判断 `activeChapter.status === 'planned'` 时：
  - `WritingEditor` 必须只读。
  - 保存按钮必须禁用或提前提示“请先创建章节文件”。
  - 创建按钮必须受 `serviceBridge.canWrite(...)` 控制。
- 创建成功后，store 用响应替换同 ID 章节记录，重置该章节 draft，并保持该章节选中。
- 生成页判断定稿、审校和批量是否缺章节文件时，不能把 `planned` 章节当成已有 `chapter_X.txt`。

### 4. Validation & Error Matrix

| Condition | Expected UI / Error |
| --- | --- |
| `planned` 章节被选中 | 编辑器只读，显示创建章节文件入口 |
| 后端不可写 | 创建按钮禁用或显示 `getWriteUnavailableMessage()` |
| `POST /api/chapters/{n}` 返回 409 | 页面展示后端错误，不覆盖 store 中正文 |
| 创建成功 | 章节状态变为可编辑，用户可输入正文并保存 |

### 5. Good/Base/Bad Cases

- Good: 目录中有第 2 章但文件缺失，章节页显示计划章节，点击创建后可编辑保存。
- Base: 后端断开且列表来自 mock，页面可展示预览数据但创建按钮不可写。
- Bad: 页面直接在 `mockApi` 或本地 store 里伪造创建成功；这会让用户误以为真实文件已落盘。
- Bad: 生成页批量校验把 `planned` 章节算作已有文件，导致后端再返回缺文件错误。

### 6. Tests Required

- 静态合约测试断言页面和 store 不直接 import `mockApi`。
- 静态合约测试断言 `serviceBridge.createChapter` 存在且使用 `POST`。
- API 测试断言创建章节真实落盘和 409 不覆盖。
- 前端改动必须通过 `npm run typecheck` 和 `npm run build`。

### 7. Wrong vs Correct

#### Wrong

```ts
if (activeChapter.status === 'planned') {
  await mockApi.saveChapter(activeChapter.order, '')
}
```

#### Correct

```ts
if (!serviceBridge.canWrite(bridgeStatus.value)) {
  errorMessage.value = serviceBridge.getWriteUnavailableMessage(bridgeStatus.value)
  return
}
await editorStore.createActiveChapter()
```
