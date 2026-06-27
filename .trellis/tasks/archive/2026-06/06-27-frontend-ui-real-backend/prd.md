# 重构前端 UI 并对接真实后端接口

## Goal

重构现有 Tauri/Vue 前端 UI，并明确、补齐与本地 FastAPI 真实接口的对接边界，让新前端成为可实际验收的本地桌面写作工作台，而不是只展示 mock 数据的界面原型。

本任务处于规划阶段；在设计和执行计划经过确认前不进入实现。

## Confirmed Facts

- 项目是 Python `customtkinter` 旧 GUI 与 `frontend/` Tauri 2 + Vue 3 + TypeScript + Vite 新前端并行演进的本地优先小说生成工具。
- 旧 GUI 仍负责完整真实 LLM/Embedding 生成流程；新前端当前负责下一代 UI、配置管理、项目文件/章节编辑、知识库/角色库管理、WebDAV 配置和生成任务壳层。
- 本地 FastAPI 边界在 `app/api/server.py`，已提供配置、模型设置、核心项目文件、章节、生成任务、知识库、角色库和 WebDAV 接口。
- `frontend/src/services/serviceBridge.ts` 已作为统一服务入口；页面和 store 不应新增对 `mockApi` 的直接依赖。
- 读类操作允许后端不可用时降级到 mock 展示数据；真实保存类操作应走后端接口，失败时提示错误。
- 生成任务接口当前只创建 in-memory `queued` 任务并返回日志，不调用真实 LLM，也不会修改小说文件。
- 现有验收文档位于 `docs/feature-map-and-acceptance.md`，包含无 API Key 的本地联调冒烟剧本。
- 前端主导航现有顺序为：项目 -> 工作台 -> 章节编辑 -> 生成任务 -> 知识库 -> 设置；该流程已记录为项目约定。
- 当前工作台已采用三轨布局，核心编辑器为 `features/writing/WritingEditor`，底层仍是增强版 `textarea`。
- `frontend/src/stores/editor.ts` 已支持章节和核心项目文件加载、草稿、保存、脏状态判断；章节页已有离开/切换前的未保存确认，工作台核心文件切换仍需要重点确认保护策略。
- `frontend/src/pages/GenerationPage.vue` 已能创建真实后端任务并查看日志，但页面需要更明确提示“任务排队不等于真实生成完成”。
- `frontend/src/pages/KnowledgePage.vue` 已接入知识导入、清理向量库、剧情要点、角色读取/保存、写入涉及角色等后端接口，清理向量库和写入配置需要更明确的操作反馈和风险边界。
- `frontend/src/stores/projects.ts` 当前默认 `activeProjectId` 是 mock 项目 id `p-ember-city`，但真实后端项目 id 是 `current`；需要作为真实接口闭环的兼容风险检查。
- 第一个 milestone 纳入项目页、右侧项目状态栏和顶部连接状态，但只做真实数据可信度修复，不做大视觉重构。
- `frontend/src/pages/ProjectsPage.vue` 当前有“新建项目”按钮，但本地 API 没有创建项目接口；第一个 milestone 需要隐藏、禁用或改写该入口，避免暗示存在多项目创建能力。
- 没有真实后端接口支撑的主操作入口应隐藏或移除；必要时只用普通说明呈现当前边界，不保留可点击但不可执行的主按钮。
- 后端已支持核心项目文件 `PUT /api/project-files/{file_id}` 自动创建固定文件；章节 `PUT /api/chapters/{chapter_number}` 对不存在文件返回 404。
- 前端当前没有专用单元测试配置；主要验证命令是 `cd frontend && npm run typecheck` 和 `cd frontend && npm run build`，真实接口路径需要配合本地 API 冒烟。
- 工作区当前 git 状态在任务创建前为 clean。

## Requirements

- 本轮首要成功标准是“可用性和真实接口闭环优先”：先把现有页面的信息架构、保存/加载状态、错误提示、真实后端状态、生成任务边界和无 API Key 冒烟验收打磨到可稳定使用；视觉升级只跟随这些流程做克制调整。
- 第一个 milestone 优先闭环“项目配置 -> 核心文件 -> 章节编辑”：先设置真实输出目录，再读写 `Novel_setting.txt` / `Novel_directory.txt` / `chapter_X.txt`，证明前端确实在操作本地后端和真实文件。
- 第一个 milestone 中，工作台只负责核心项目文件编辑闭环；章节导航和章节上下文可以保留，但章节正文编辑与保存由独立“章节编辑”页负责。
- 保持新前端与旧 GUI 的职责边界清晰：本轮不承诺把真实 LLM 生成执行器接入新前端，除非后续明确扩展范围。
- 重构后的 UI 必须围绕真实写作流程组织，而不是营销页或纯展示页。
- 前端数据访问继续通过 `frontend/src/services/serviceBridge.ts` 统一进入。
- 保存类操作不得静默写入 mock；后端不可用、接口失败、文件不存在等状态必须给出可理解反馈。
- 后端不可用时，项目配置、核心文件、章节等读类数据允许进入只读 mock 预览；页面必须显式标记“离线预览/非真实本地数据”，并禁用保存、导入、生成等所有写类操作。
- 核心项目文件不存在时，工作台允许用户通过保存动作创建固定文件；章节文件不存在时，章节编辑页暂不自动创建，只提示需要先准备 `chapter_X.txt` 或通过旧 GUI/后续生成流程创建。
- UI 必须准确呈现当前能力边界，尤其是生成任务只是排队/等待执行器接入，不应让用户误以为已经完成真实生成。
- 重构应优先复用现有通用 UI 组件和 feature 组件，避免页面内重复维护状态标签、日志查看、角色列表等逻辑。
- 计划阶段需要产出 `design.md` 与 `implement.md`，并按 milestone 拆分，避免一次性执行过大的前端改造。

## Acceptance Criteria

- [ ] 已形成并确认 PRD、技术设计和分阶段执行计划。
- [ ] 计划明确列出本轮要重构的页面/组件、真实后端接口覆盖范围、保留 mock 的只读降级范围和不做事项。
- [ ] 每个 milestone 都可以独立测试、独立提交、独立恢复执行。
- [ ] 最终实现后，`docs/feature-map-and-acceptance.md` 中无 API Key 冒烟验收路径仍成立，或被同步更新为新的真实验收路径。
- [ ] 最终实现后，前端至少通过 `npm run typecheck` 和 `npm run build`；涉及真实接口的路径需要配合本地 API 做冒烟验证。
- [ ] 第一个 milestone 必须完成类型检查/构建、本地 FastAPI 启动、前端浏览器冒烟，并验证真实文件读写、离线 mock 标记和写操作禁用。

## Out of Scope

- 将新前端生成任务接入真实 LLM 执行器。
- 替换或删除旧 Python GUI。
- 提交 `config.json`、真实 API Key、WebDAV 密码或大体积小说输出。
