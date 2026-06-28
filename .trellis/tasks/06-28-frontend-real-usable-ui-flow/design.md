# 项目管理最小闭环设计

## Architecture

本轮采用“`config.json` 当前项目 + `.local/state.sqlite3` 最近项目列表”的最小方案。

- 当前项目权威来源仍是根目录 `config.json.other_params.filepath`，旧 Python GUI 和本地 API 继续共享同一配置。
- 输出目录中的 `Novel_setting.txt`、`Novel_directory.txt`、`chapter_X.txt`、`vectorstore/`、角色库等仍是小说项目文件权威来源。
- `.local/state.sqlite3` 只新增最近项目索引，不保存小说正文、不保存密钥、不保存完整项目配置。
- 前端项目页通过 `serviceBridge` 调用真实 API 创建/切换项目；切换后清空或重载依赖当前输出目录的 Pinia 状态。

## Backend Contracts

新增或扩展 API model：

- `ProjectSummary`
  - 保持现有字段：`id`、`title`、`genre`、`status`、`summary`、`updatedAt`、`chaptersTotal`、`chaptersCompleted`。
  - `id` 使用稳定路径派生 ID，例如标准化绝对路径的短 hash；当前项目仍允许兼容 `current`，但列表中项目必须可被切换接口识别。
  - `summary` 继续展示输出路径，避免新增前端字段破坏范围。
- `ProjectCreateRequest`
  - `outputPath: str`
  - `topic: str = ""`
  - `genre: str = ""`
  - `numChapters: int >= 0`
  - `wordNumber: int >= 0`
- `ProjectSwitchRequest`
  - `projectId: str | None = None`
  - `outputPath: str | None = None`

新增 API：

- `POST /api/projects`
  - 创建输出目录。
  - 合并当前 `config.json`，写入 `other_params.filepath`、`topic`、`genre`、`num_chapters`、`word_number`，保留模型、代理、WebDAV 等全局配置。
  - upsert 最近项目记录。
  - 返回新当前项目摘要。
- `POST /api/projects/switch`
  - 通过 `projectId` 查最近项目，或通过 `outputPath` 打开已有目录。
  - 目录不存在或不是目录时返回中文 `400`。
  - 更新 `config.json.other_params.filepath`；如果目标目录已有可推导信息，可只更新路径并保留当前 topic/genre，避免错误覆盖用户配置。
  - upsert 最近项目记录并返回当前项目摘要。

扩展 `GET /api/projects`：

- 返回最近项目列表，当前项目排在第一位并标记 `status="active"`。
- 最近项目不存在时，仍返回当前 `config.json` 项目摘要。
- `chaptersCompleted` 始终按真实 `chapter_<数字>.txt` 文件数计算，不能把计划章节计入完成数。

## Persistence

新增 `app/services/project_store.py`，使用与生成任务相同的 SQLite 文件。

表：`recent_projects`

- `id TEXT PRIMARY KEY`
- `output_path TEXT NOT NULL UNIQUE`
- `title TEXT NOT NULL`
- `genre TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

`ProjectStore` 职责：

- 根据输出路径生成稳定 ID。
- upsert 最近项目记录。
- 通过 ID 查找最近项目。
- 列出最近项目，按 `updated_at DESC`。

不保存 `config.json` 中的 API Key、模型配置、WebDAV 密码、完整 `other_params`。测试通过 `create_app(state_db_file=tmp_path / "state.sqlite3")` 隔离。

## Frontend Contracts

`frontend/src/services/types.ts` 新增：

- `ProjectCreateRequest`
- `ProjectSwitchRequest`

`serviceBridge.ts` 新增写操作：

- `createProject(request)`
- `switchProject(request)`

这两个方法不得允许 mock fallback。后端不可用时页面使用 `canWrite` 和 `getWriteUnavailableMessage` 禁用或提示。

`projects.ts` store 调整：

- `loadProjects(force = false)` 支持强制重载。
- `createProject(...)` 调用服务桥，成功后强制重载项目列表并选中新当前项目。
- `switchProject(...)` 调用服务桥，成功后强制重载项目列表并选中新当前项目。
- 项目切换后发起依赖方重置/重载：编辑器章节、项目文件、生成任务列表需要从新输出目录重新读取。

`ProjectsPage.vue` 调整：

- 在项目页增加两个紧凑表单：
  - 新建项目：输出路径、主题、类型、章节数、每章字数。
  - 打开已有项目：输出路径。
- 最近项目卡片提供“切换”动作；当前项目显示 active 状态。
- 使用现有 `PageHeader`、`StatusMessage`、`FormSection`、`TextField`、`AppButton`，避免引入新的 UI 框架。

## Data Flow

新建项目：

`ProjectsPage` 表单 -> `projectsStore.createProject` -> `serviceBridge.createProject` -> `POST /api/projects` -> 创建目录 -> 写 `config.json` -> upsert `recent_projects` -> 返回 `ProjectSummary` -> 前端重载项目列表和当前项目依赖数据。

切换最近项目：

项目卡片 -> `projectsStore.switchProject({ projectId })` -> `POST /api/projects/switch` -> 查 `recent_projects` -> 校验目录 -> 写 `config.json.other_params.filepath` -> upsert 最近项目 -> 前端重载。

打开已有目录：

路径输入 -> `projectsStore.switchProject({ outputPath })` -> 后端校验目录 -> 写当前输出路径 -> upsert 最近项目 -> 前端重载。

## Error Handling

- 新建项目 `outputPath` 为空：HTTP `400`，`detail="项目输出路径不能为空"`。
- 打开已有项目路径不存在或不是目录：HTTP `400`，`detail="项目输出路径不存在"`。
- `projectId` 不存在：HTTP `404`，`detail="项目不存在"`。
- 前端直接展示后端中文 `detail`，不泛化成“请求失败”。
- 离线预览或断线：不发起写请求，展示 serviceBridge 统一不可写文案。

## Compatibility

- 不改变 `python main.py`、旧 GUI 配置读取或输出文件格式。
- 不迁移已有输出目录；打开已有目录只记录最近项目并切换当前路径。
- `GET /api/project-config` 和设置页仍可编辑当前项目参数；它们与项目页共享同一个当前 `config.json`。
- 生成任务仍按 `projectId` 过滤。最小方案下，切换项目后新任务使用新 active project ID；历史任务按保存时 project ID 展示。

## Testing

后端：

- 新建项目创建目录、写回 `config.json`、返回摘要、记录最近项目。
- 打开已有目录更新 `filepath`、不覆盖目录文件、重启 app 后仍列出最近项目。
- 最近项目列表当前项目置顶，章节完成数来自真实章节文件。
- 无效路径、未知项目 ID 返回中文错误。

前端：

- `serviceBridge` 暴露 create/switch 方法且不允许 mock fallback。
- 项目页和 store 不直接 import `mockApi`。
- `npm run typecheck` 和 `npm run build`。

全量：

- `python -m pytest tests`
- 必要时用临时输出目录做项目创建/切换冒烟，不使用真实小说目录。

## Rollback

- 后端新增接口和 `ProjectStore` 是独立边界；回滚时删除接口、store、测试即可。
- 若 `.local/state.sqlite3` 中出现 `recent_projects` 表，删除状态库只会清空最近项目列表和生成任务历史，不会删除小说输出文件或 `config.json`。
