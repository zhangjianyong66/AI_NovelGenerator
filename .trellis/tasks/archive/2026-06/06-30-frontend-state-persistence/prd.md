# 前端状态持久化补齐

## Goal

补齐新前端的可恢复工作上下文，让用户刷新页面、重新打开前端或在页面之间切换后，仍能回到最近使用的项目、章节、项目文件、生成任务选择和生成参数。

核心用户价值：

- 章节编辑页不应在刷新后回到第 1 章，而应保留当前项目下最后选中的章节。
- 生成任务页的批量参数和任务选择不应只存在于当前页面实例，刷新后应恢复最近输入。
- 页面级偏好应按项目隔离，避免打开另一个小说项目时继承不相关的章节号、任务选择或批量范围。

## Confirmed Facts

- `frontend/src/stores/editor.ts` 当前把 `activeChapterId`、`activeProjectFileId`、章节草稿和核心项目文件草稿保存在 Pinia 内存状态中；`resetProjectState()` 会清空 `activeChapterId`，`loadChapters()` 在空值时回落到第一章。
- `frontend/src/pages/ChaptersPage.vue` 和 `frontend/src/pages/WorkspacePage.vue` 都通过 `editorStore.selectChapter(...)` 切换章节，因此同一个 store 适合承载“当前项目最后选中章节”的持久化入口。
- `frontend/src/pages/GenerationPage.vue` 当前使用页面级 `ref` 保存 `selectedJobId` 和 `batchForm`，默认值为第 1 章到第 1 章、3000/2000 字、不开启自动扩写；页面刷新后这些值会重置。
- `frontend/src/layouts/AppLayout.vue` 已直接用 `localStorage` 保存左侧导航和右侧状态栏折叠偏好，key 为 `ai-novel-generator.layout.navCollapsed` 和 `ai-novel-generator.layout.contextCollapsed`。
- `frontend/src/main.ts` 只安装了普通 Pinia，没有全局持久化插件；`frontend/package.json` 未包含 Pinia 持久化插件依赖。
- `frontend/src/pages/SettingsPage.vue` 的项目参数、模型设置和 WebDAV 设置已有后端保存接口；当前章节号 `projectConfig.novelParams.chapterNum` 属于真实项目配置，不应只作为前端本地偏好保存。
- 前端规范要求页面和 store 通过 `serviceBridge` 访问真实后端或 mock fallback；写操作不能静默写入 mock。纯前端 UI 工作上下文不属于后端写操作。

## Requirements

- R1: 章节选中状态必须按项目持久化。刷新章节页、工作台页或重新打开前端后，如果当前项目仍存在该章节，应恢复最后选中的章节；如果章节已不存在，应回落到当前章节列表第一项。
- R2: 核心项目文件选中状态必须按项目持久化。刷新工作台页或重新打开前端后，如果核心文件仍存在，应恢复最后选中的文件；如果文件已不存在，应回落到默认文件。
- R3: 生成任务页的批量参数必须持久化并按项目隔离，包括起始章节、结束章节、目标字数、最低字数和自动扩写。
- R4: 生成任务页的选中任务必须按项目持久化。刷新后若任务仍存在，应恢复该任务详情；若任务已不存在，应回落到最新任务。
- R5: 持久化数据必须能容忍 `localStorage` 不可用、JSON 解析失败、旧数据字段缺失或非法数字；发生异常时使用现有默认值，不阻断页面加载。
- R6: 持久化不得保存章节正文草稿、核心项目文件草稿、API Key、密码、Base URL、代理地址或生成的大体积内容。
- R7: 当前章节号、小说参数、模型配置、WebDAV 配置仍通过现有后端配置接口保存，不通过本次前端本地持久化机制替代。
- R8: 本次改动应优先复用现有 Pinia store 和页面组件结构，不引入新运行时依赖。

## Acceptance Criteria

- [ ] 在章节编辑页选择非第 1 章后刷新页面，当前项目仍选中同一章节。
- [ ] 在工作台页选择章节或核心项目文件后刷新页面，当前项目仍恢复对应选择。
- [ ] 切换到另一个项目后，章节选择、项目文件选择、生成参数和选中任务不沿用上一个项目的数据。
- [ ] 修改生成任务页批量参数后刷新页面，表单恢复上次输入值。
- [ ] 选择生成任务列表中的非首个任务后刷新页面，若该任务仍存在，详情区恢复该任务；若不存在，回落到列表首项。
- [ ] 人为写入损坏的前端持久化 JSON 后，页面仍可加载并使用默认值。
- [ ] `cd frontend && npm run typecheck` 通过。
- [ ] `cd frontend && npm run build` 通过。

## Out of Scope

- 不在本次实现章节正文或核心项目文件未保存草稿的本地自动恢复。
- 不在本次实现后端数据库保存前端 UI 偏好。
- 不在本次调整真实生成执行器、任务历史数据库或模型配置保存语义。
- 不在本次保存知识库页和设置页的当前 tab、导入路径、角色选择等次级页面工作上下文。
