# 前端 UI 真实可用后续完善

## Goal

继续把新 Tauri/Vue 前端从“能触发核心生成流程”推进到“能独立完成日常写作操作”的真实创作工具。本轮建议聚焦章节生命周期最小闭环：生成或编辑目录后，即使输出目录里还没有 `chapter_X.txt`，前端也能根据 `Novel_directory.txt` 和项目章节数展示计划章节，并允许用户创建缺失章节文件后进入章节编辑。

用户价值：用户不需要离开前端或手动到文件系统创建 `chapter_2.txt`、`chapter_3.txt` 等空文件；目录生成后可以直接按章节列表推进“选择章节 -> 创建/生成草稿 -> 编辑保存”的流程。

## Confirmed Facts

- 当前没有活动 Trellis 任务，工作区创建了本任务 `.trellis/tasks/06-28-frontend-real-usable-next`。
- 最近已完成并归档：
  - `06-28-frontend-real-usable`：设定和目录真实生成执行器。
  - `06-28-frontend-chapter-generation-real-usable`：单章草稿和定稿真实执行器。
  - `06-28-frontend-real-usable-followup`：生成任务历史持久化到 `.local/state.sqlite3`。
- `docs/feature-map-and-acceptance.md` 的后续优先级仍包括知识库真实向量化、项目管理和章节生命周期；其中章节生命周期明确要求：生成目录后前端能看到章节列表，用户能创建或生成不存在的章节文件并继续编辑。
- `GET /api/projects/{project_id}/chapters` 当前只枚举输出目录根部已有的 `chapter_*.txt`；缺失章节不会出现在列表中。
- `PUT /api/chapters/{chapter_number}` 当前只保存已有章节文件；文件不存在时返回 404。
- `frontend/src/pages/ChaptersPage.vue` 当前空状态提示“请先准备章节文件”，没有从前端创建章节文件的入口。
- `frontend/src/pages/GenerationPage.vue` 已允许草稿任务在章节文件不存在时创建；草稿成功后会刷新章节上下文。
- 前端章节接口仍以输出目录根部 `chapter_X.txt` 为读取和保存入口，草稿/定稿执行器会与 legacy `chapters/chapter_X.txt` 同步。
- `Novel_directory.txt` 已通过 `chapter_directory_parser.get_chapter_info_from_blueprint(...)` 为已有章节补标题和简介；可继续复用该解析边界。

## Requirements

- R1. 本轮只实现章节生命周期最小闭环，不展开知识库真实向量化、项目多实例管理、后台任务恢复或大规模视觉重构。
- R2. 后端章节列表应能返回两类章节：已有 `chapter_X.txt` 的可编辑章节，以及从 `Novel_directory.txt` / `num_chapters` 推导出的计划章节。
- R3. 计划章节必须有稳定的 `id`、`order`、`title`、`synopsis`、`status`、`words`、`content` 字段，保持现有前端类型兼容；缺失文件的 `content` 为空，`words` 为 0。
- R4. API 必须提供创建缺失章节文件的真实写入能力，写入当前输出目录根部 `chapter_X.txt`；如果文件已存在，不得静默覆盖正文。
- R5. 前端章节编辑页应能展示计划章节，并为缺失章节提供明确的“创建章节文件”入口；创建成功后可直接编辑和保存。
- R6. 前端生成页的现有草稿流程不能被破坏：缺失章节仍可通过草稿生成；创建空章节只是用户手写/编辑路径的补充。
- R7. 离线预览或本地后端未连接时，创建章节文件等写操作必须禁用或给出明确不可写提示，继续通过 `serviceBridge` 统一守卫。
- R8. 测试必须覆盖章节列表混合已有/计划章节、创建缺失章节、拒绝覆盖已有章节、保存新建章节等路径。
- R9. 不提交 `config.json`、API Key、私有 Base URL、真实小说正文、`vectorstore/`、`.local/` 或前端构建产物。

## Acceptance Criteria

- [x] `GET /api/projects/current/chapters` 在只有 `Novel_directory.txt` 和项目章节数、但没有 `chapter_2.txt` 时，也会返回第 2 章计划章节，状态能区分未开始/计划。
- [x] 已有章节仍按真实文件内容返回，标题和简介继续从目录中补充。
- [x] 新增创建章节接口或等价写入边界可以创建缺失的 `chapter_X.txt`，返回可编辑章节；对已存在章节返回 409 或等价清晰错误，不覆盖正文。
- [x] 章节编辑页能显示计划章节；选中缺失章节时编辑器只读或空态合理，并提供创建章节文件入口。
- [x] 创建章节文件后，用户可以在章节编辑页输入正文并保存到真实 `chapter_X.txt`。
- [x] 生成任务页草稿、定稿、审校、批量的现有校验语义不退化。
- [x] `python -m pytest tests` 通过，或记录明确环境阻塞。
- [x] `cd frontend && npm run typecheck` 通过，或记录明确环境阻塞。
- [x] `cd frontend && npm run build` 通过，或记录明确环境阻塞。
- [x] `docs/feature-map-and-acceptance.md` 和必要的 `AGENTS.md` 更新章节生命周期边界。

## Out Of Scope

- 不实现知识库真实向量化和章节生成时检索命中。
- 不实现项目新建、打开、切换或最近项目。
- 不实现一致性审校真实执行。
- 不实现批量章节真实执行。
- 不新增章节数据库、复杂状态机或跨项目章节元数据迁移。
- 不改变旧 Python GUI 的文件格式和运行方式。
- 不重做前端整体视觉结构。

## Scope Decision

- 用户已确认本轮按“章节生命周期最小闭环”执行。知识库真实向量化和项目新建/切换保留为后续独立任务。
