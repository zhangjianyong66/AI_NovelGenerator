# 项目管理最小闭环执行计划

## Pre-Implementation

- [x] 用户确认 `prd.md`、`design.md`、`implement.md` 后运行 `task.py start`。
- [x] 执行前读取 `trellis-before-dev`，并按前端/后端规范加载必要上下文。
- [x] 确认工作区状态，避免覆盖用户未提交改动。

## 1. 后端项目状态存储

- [x] 新增 `app/services/project_store.py`。
- [x] 使用标准库 `sqlite3` 和当前 `state_db_file`。
- [x] 实现 `recent_projects` schema、稳定项目 ID、upsert、get、list。
- [x] 保持状态库只保存最近项目索引，不保存密钥和小说正文。

验证点：

- `ProjectStore` 单元或 API 测试通过临时 `state_db_file` 隔离。

## 2. 后端 API 合同

- [x] 在 `app/api/server.py` 新增 `ProjectCreateRequest`、`ProjectSwitchRequest`。
- [x] 扩展 `create_app(...)` 初始化 `ProjectStore`。
- [x] 新增 helper：
  - 路径校验和规范化。
  - 基于输出目录与当前配置生成 `ProjectSummary`。
  - 当前项目 upsert 最近项目。
- [x] 扩展 `GET /api/projects` 返回最近项目列表，当前项目置顶。
- [x] 新增 `POST /api/projects` 创建项目并更新 `config.json`。
- [x] 新增 `POST /api/projects/switch` 支持通过 `projectId` 或 `outputPath` 切换。
- [x] 保留 `GET/PUT /api/project-config` 现有行为。

测试：

- [x] 更新 `tests/test_api_projects_and_knowledge.py` 或新增 `tests/test_api_projects.py`。
- [x] 覆盖新建项目创建目录、写配置、记录最近项目。
- [x] 覆盖打开已有目录不覆盖文件、重启 app 后列表仍存在。
- [x] 覆盖当前项目置顶和章节完成数。
- [x] 覆盖空路径、无效路径、未知项目 ID 中文错误。

## 3. 前端服务与状态

- [x] 更新 `frontend/src/services/types.ts`，新增项目创建/切换请求类型。
- [x] 更新 `frontend/src/services/serviceBridge.ts`：
  - 新增 `createProject`。
  - 新增 `switchProject`。
  - 两者不使用 mock fallback。
- [x] 更新 `frontend/src/stores/projects.ts`：
  - `loadProjects(force = false)`。
  - `createProject` 和 `switchProject` action。
  - 切换成功后确保 active project 指向后端返回项目或当前 active 项目。
- [x] 如有必要，给 `editor.ts` / `generation.ts` 增加轻量 reset action，防止切换时旧项目 draft 留在界面。

## 4. 前端项目页

- [x] 更新 `frontend/src/pages/ProjectsPage.vue`。
- [x] 新增“新建项目”表单：输出路径、主题、类型、章节数、每章字数。
- [x] 新增“打开已有项目”表单：输出路径。
- [x] 最近项目卡片提供“切换”动作，当前项目不可重复切换或显示 active。
- [x] 非真实后端模式下禁用新建/切换，并展示统一不可写提示。
- [x] 切换成功后刷新项目配置；依赖当前项目的全局状态由 store 或 layout watcher 重新加载。

## 5. 文档与规范

- [x] 更新 `docs/feature-map-and-acceptance.md` 的项目管理能力状态和冒烟验收。
- [x] 更新 `AGENTS.md` 项目级说明，记录项目管理接口、最近项目状态库和切换语义。
- [x] 如实现扩大 SQLite 到最近项目索引，更新 `.trellis/spec/backend/persistence-and-config.md` 和 `.trellis/spec/backend/database-guidelines.md`。
- [x] 如前端服务桥合同新增项目写操作，更新 `.trellis/spec/frontend/service-bridge-real-backend.md`。

## 6. 验证

- [x] `python -m pytest tests`
- [x] `cd frontend && npm run typecheck`
- [x] `cd frontend && npm run build`
- [ ] 可选 API 冒烟：
  - 临时 `config.json` / 临时输出目录启动 `create_app` 或测试客户端。
  - 创建项目、切换项目、确认 `config.json.other_params.filepath` 更新。
- [x] 检查 `git status`，确认没有提交 `config.json`、`.local/`、输出目录、前端构建产物。

## Risk / Rollback Points

- 后端 `GET /api/projects` 响应语义变为多项目列表；前端现有页面应兼容列表，测试要覆盖当前项目仍可显示。
- 切换项目会改变 `config.json.other_params.filepath`，测试必须使用临时配置，人工冒烟必须使用临时目录。
- 前端编辑器草稿若未清理，可能在切换后显示旧项目内容；实现时必须重载或清空当前项目相关 store。
- 回滚时删除新增 API、`ProjectStore`、前端表单和相关文档即可；`.local/state.sqlite3` 删除不会影响小说输出文件。
