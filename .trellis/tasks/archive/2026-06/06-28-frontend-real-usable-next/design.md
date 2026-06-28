# 前端 UI 真实可用后续完善 - Design

## Architecture

本轮沿用现有“本地 FastAPI + 输出目录文本文件 + Vue serviceBridge”的边界，不新增数据库或章节元数据文件。章节生命周期状态由文件系统和目录蓝图即时推导：

- 输出目录根部存在 `chapter_X.txt`：该章节是可编辑草稿，状态返回 `draft`。
- `Novel_directory.txt` 或 `other_params.num_chapters` 中存在章节号，但根部没有 `chapter_X.txt`：该章节是计划章节，状态返回 `planned`，正文为空，字数为 0。
- 创建章节文件只写根部 `chapter_X.txt`，不主动写 legacy `chapters/chapter_X.txt`。后续草稿/定稿执行器已有双路径同步逻辑，避免本轮引入新的同步副作用。

## Backend Contract

扩展 `app/api/server.py` 的章节 helper：

- 新增 `_planned_chapter_numbers(output_path, config)` 或等价 helper，从 `Novel_directory.txt` 解析章节号，并与 `other_params.num_chapters` 生成的 `1..N` 合并。
- 调整 `GET /api/projects/{project_id}/chapters`：返回已有章节号和计划章节号的并集，按数字排序。
- 调整 `_chapter_response(...)`：允许文件不存在时返回 `Chapter(status="planned", words=0, content="")`，标题和简介仍来自目录蓝图。
- 新增 `POST /api/chapters/{chapter_number}` 或等价接口创建缺失章节文件，响应 `Chapter`。章节号必须是正整数；文件已存在返回 `409`，避免覆盖正文。
- 保持 `PUT /api/chapters/{chapter_number}` 只保存已有文件。创建和保存是两个显式动作，避免用户选中计划章节时误以为保存会自动创建。

## Frontend Contract

扩展 `frontend/src/services/types.ts`、`serviceBridge.ts`、`stores/editor.ts` 和 `ChaptersPage.vue`：

- `ChapterStatus` 已包含 `planned`，继续复用。
- `serviceBridge.createChapter(chapterOrder)` 新增真实写接口，不提供 mock fallback。
- `editorStore.createActiveChapter()` 调用 serviceBridge 创建当前计划章节，成功后替换章节列表中的同 ID 记录并重置对应 draft。
- 章节编辑页选中 `planned` 章节时：
  - 编辑器保持只读，避免对不存在文件产生未保存草稿幻觉。
  - 显示“创建章节文件”按钮，按钮受 `canWriteToBackend` 控制。
  - 创建成功后编辑器切换为可写，用户可输入正文并保存。
- 已有章节的编辑、保存、上一章/下一章、未保存切换确认逻辑保持不变。

## Data Flow

1. 用户进入章节编辑页。
2. 前端通过 `serviceBridge.listChapters(projectId)` 请求本地 API。
3. API 读取 `config.json` 的输出路径、`Novel_directory.txt` 和根部 `chapter_*.txt`，返回章节并集。
4. 用户选择 `planned` 章节并点击创建。
5. 前端调用 `POST /api/chapters/{order}`；API 原子地创建空文本文件或返回 409。
6. 前端用响应替换 store 中的章节记录，编辑器变为可写。
7. 用户输入正文后调用既有 `PUT /api/chapters/{order}` 保存。

## Compatibility

- 不改变旧 GUI 输出格式。
- 不改变生成任务请求/响应结构。
- 草稿任务仍可在章节文件不存在时直接生成章节；创建空章节只是手写编辑路径。
- `GET /api/projects` 的章节完成数仍按实际 `chapter_*.txt` 文件计数，不把计划章节当作已完成。
- 读类接口仍允许 mock fallback；创建章节文件是写操作，必须真实后端可用。

## Error Handling

- `POST /api/chapters/{chapter_number}`：
  - `chapter_number <= 0` 返回 `400`，中文 `detail`。
  - 文件已存在返回 `409`，中文 `detail`。
  - 输出路径未配置继续使用现有 `_active_output_path()` 错误。
- 前端优先显示后端 `detail`，不能泛化成“本地后端请求失败”。
- 离线预览或断线时，创建按钮禁用或提前显示 `serviceBridge.getWriteUnavailableMessage(...)`。

## Trade-offs

- 选择即时推导章节状态，而不是新增 SQLite 章节表：实现小、兼容旧输出目录，但无法记录“已定稿/需审校”等长期状态；这属于后续独立任务。
- 创建章节文件不写 legacy `chapters/`：避免用户手写空章节污染旧生成目录；需要旧 GUI 读取时仍可通过既有定稿/草稿同步路径处理。
- 不让 `PUT /api/chapters/{chapter}` 自动创建文件：交互更明确，避免用户在计划章节上误保存空内容覆盖预期。
