# 继续完善前端真实可用闭环

## Goal

继续把新 Tauri/Vue 前端从“围绕当前 `config.json` 输出目录工作”推进到“能从项目页真实进入和切换本地小说项目”的创作工具。本轮建议聚焦项目管理最小闭环：用户可以在前端新建一个项目输出目录、打开/切换一个已有输出目录，并让工作台、章节、生成任务、知识库和设置页随当前项目读取同一真实输出路径。

用户价值：用户不再需要到设置页手动改 `other_params.filepath` 才能切换小说工程；项目页成为真实入口，降低误写到旧输出目录的风险。

## Confirmed Facts

- 当前没有活动 Trellis 任务，本任务为 `.trellis/tasks/06-28-frontend-real-usable-ui-flow`。
- 最近已归档的相关任务已经完成：
  - `06-28-frontend-real-usable`：设定和目录真实生成执行器。
  - `06-28-frontend-chapter-generation-real-usable`：单章草稿和定稿真实执行器。
  - `06-28-frontend-real-usable-followup`：生成任务历史持久化到 `.local/state.sqlite3`。
  - `06-28-frontend-real-usable-next`：章节列表计划章节和创建缺失章节文件。
  - `06-28-frontend-real-usable-continue`：知识库真实向量化导入。
- `docs/feature-map-and-acceptance.md` 的后续优先级中，项目管理能力排在剩余未完成重点之前：前端不再只围绕 `config.json` 当前输出目录工作，而是支持新建、打开、切换和最近项目。
- `app/api/server.py` 当前 `GET /api/projects` 只返回 `_project_summary(config_path)`，即当前 `config.json` 的单个项目摘要。
- `app/api/server.py` 当前 `GET/PUT /api/project-config` 会读写 `config.json` 的 `other_params.filepath` 和小说参数。
- `frontend/src/pages/ProjectsPage.vue` 当前只展示当前输出路径与项目卡片，没有真实新建、打开或切换项目入口。
- `frontend/src/stores/projects.ts` 当前 `selectProject(projectId)` 只修改前端内存中的 `activeProjectId`，不会触发后端切换输出路径；多数页面仍以 `current` 项目和 `config.json` 当前路径作为真实数据边界。
- `frontend/src/services/serviceBridge.ts` 是前端真实/Mock 数据访问和写操作守卫统一入口；新增项目写操作必须继续走这里，且不能 mock 写入。
- 本项目要兼容旧 Python GUI；旧 GUI 仍读取根目录 `config.json`，因此最小项目切换应更新 `config.json` 的当前输出路径，而不是迁移旧配置格式。

## Approach Options

1. **推荐：基于 `config.json` 的最小项目管理闭环**
   - 后端新增“创建项目目录”“打开/切换项目路径”“最近项目列表”的最小接口。
   - 当前项目仍通过 `config.json.other_params.filepath` 表示，切换项目即更新 `config.json` 当前路径和可推导的小说参数。
   - 最近项目元数据保存在 `.local/` 本地状态中，不迁移小说正文，不引入项目数据库。
   - 取舍：实现快、兼容旧 GUI；项目级模型配置仍是全局 `config.json`，不是每个项目一份。
2. **项目清单数据库方案**
   - 后端新增项目表，保存 title、outputPath、genre、最近打开时间等；切换时同步 `config.json`。
   - 取舍：后续扩展更强，但本轮会引入更多状态迁移和同步规则。
3. **每个项目独立配置文件方案**
   - 每个输出目录都拥有自己的项目配置和模型选择，根配置只保存最近项目。
   - 取舍：长期更像完整项目系统，但会明显影响旧 GUI 兼容和当前本地 API 边界，不适合作为本轮最小闭环。

## Scope Decision

- 用户已确认本轮采用“基于 `config.json` 的最小项目管理闭环”。
- 当前项目仍由根目录 `config.json.other_params.filepath` 决定；项目创建/切换只更新当前输出路径和相关小说参数。
- 最近项目列表作为本地 UI 状态保存在 `.local/` 状态库，供前端项目页展示和切换；它不是小说正文或项目配置的权威来源。

## Requirements

- R1. 本轮只实现项目管理最小闭环，不展开每项目独立模型配置、项目数据库迁移、WebDAV 项目同步或大规模视觉重构。
- R2. 后端必须继续兼容旧 Python GUI：根目录 `config.json` 仍是当前项目与模型配置来源。
- R3. 新建项目应能创建指定输出目录，并将基础小说参数写入当前 `config.json`；输出目录不存在时自动创建。
- R4. 打开/切换已有项目应更新当前 `config.json.other_params.filepath`，并从目标输出目录和当前配置推导项目摘要。
- R5. 后端应记录最近项目列表，至少保存输出路径、标题/主题、类型、最近打开时间、章节总数和已落盘章节数；该状态不得提交到 git。
- R6. `GET /api/projects` 应返回最近项目列表，并明确当前 active 项目；没有最近项目时仍返回当前 `config.json` 项目摘要。
- R7. 前端项目页应提供真实的新建项目和打开/切换项目入口；写入口必须受 `serviceBridge.canWrite(...)` 控制。
- R8. 切换项目成功后，前端应刷新项目列表、项目配置和依赖当前输出目录的页面数据，避免继续展示旧项目文件。
- R9. 离线预览或本地后端未连接时，项目新建/切换必须禁用或提前提示不可写，不允许 mock 写入。
- R10. 不提交 `config.json`、API Key、私有 Base URL、真实小说正文、`vectorstore/`、`.local/` 或前端构建产物。

## Acceptance Criteria

- [ ] 规划阶段产出收敛后的 `prd.md`、`design.md` 和 `implement.md`。
- [ ] 后端提供项目创建和项目切换 API，能真实创建目录或切换到已有输出目录，并更新 `config.json.other_params.filepath`。
- [ ] 后端最近项目状态保存在 `.local/` 或测试可隔离的等价位置，重启后 `GET /api/projects` 仍能返回最近项目列表。
- [ ] 项目切换不会删除或覆盖目标目录中的 `Novel_setting.txt`、`Novel_directory.txt`、`chapter_X.txt` 等小说文件。
- [ ] 前端项目页可以新建项目、切换最近项目；成功后工作台/章节/生成/知识库读取新输出路径。
- [ ] 后端不可用或 mock 模式下，项目新建/切换入口不可写，并展示统一不可写提示。
- [ ] `python -m pytest tests` 通过，或记录明确环境阻塞。
- [ ] `cd frontend && npm run typecheck` 通过，或记录明确环境阻塞。
- [ ] `cd frontend && npm run build` 通过，或记录明确环境阻塞。
- [ ] `docs/feature-map-and-acceptance.md`、`AGENTS.md` 和必要的 `.trellis/spec/` 更新项目管理真实边界。

## Out Of Scope

- 不实现每个项目独立 LLM/Embedding/WebDAV 配置。
- 不实现项目删除、归档、重命名、复制、导入压缩包或远程同步。
- 不迁移旧输出目录结构，不新增小说正文数据库。
- 不改变旧 Python GUI 的启动方式和配置读取方式。
- 不实现一致性审校或批量生成真实执行器。
- 不重做前端整体视觉结构。

## Notes

- 本任务属于复杂跨层任务，进入实现前必须补充 `design.md` 和 `implement.md`，并经用户确认后再 `task.py start`。
