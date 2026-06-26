# 前端 UI 重构实施计划

## 执行原则

- 本任务目前处于规划阶段，未获得实现确认前不改业务代码。
- 按架构层先后重构，以工作台作为首个落地页面。
- 每个 milestone 独立验证、独立提交、可恢复执行。
- 默认每轮只执行用户指定的 milestone 或任务范围。
- 不提交 `frontend/node_modules/`、`frontend/dist/`、`frontend/src-tauri/target/`、`config.json` 或生成小说输出。

## Milestone 1: 设计 token 与基础 UI

- [x] 拆分 `frontend/src/styles/global.css` 为 token/base/global 或等价结构。
- [x] 新增或整理基础 UI：`AppButton`、`IconButton`、字段组件、`Toolbar`、`SplitPane`、空/加载/保存状态。
- [x] 让现有 `PageHeader`、`ActionBar`、`StatusMessage`、`FormSection`、`Tabs` 复用 token 和基础样式。
- [x] 保持现有页面视觉不出现明显回退。

验证：

```bash
cd frontend
npm run typecheck
npm run build
```

结果：

- 2026-06-26：`npm run typecheck` 通过。
- 2026-06-26：`npm run build` 通过。

## Milestone 2: writing feature 与编辑器适配层

- [x] 创建 `frontend/src/features/writing/` 目录结构。
- [x] 新增 `WritingEditor`，以增强版 textarea 为第一阶段内核。
- [x] 封装字数/段落/选区/保存状态/只读状态等编辑器基础能力。
- [x] 梳理 `editor` store 的 async state、脏状态和保存状态，必要时下沉到 `features/writing/stores/`。

验证：

```bash
cd frontend
npm run typecheck
npm run build
```

结果：

- 2026-06-26：`npm run typecheck` 通过。
- 2026-06-26：`npm run build` 通过。
- 2026-06-26：`git diff --check` 通过。

手动验收：

- 章节正文可编辑、保存、显示未保存状态。
- 核心项目文件可编辑、保存、显示字数。
- 切换章节时仍有未保存保护。

## Milestone 3: 工作台重构

- [x] 新增 `WorkbenchLayout` 或等价工作台布局组件。
- [x] 工作台改为章节编辑器中心布局。
- [x] 左侧轨道整合项目文件和章节导航。
- [x] 中间区域使用 `WritingEditor`。
- [x] 右侧轨道整合上下文资料、生成动作、运行任务和日志摘要。
- [x] 支持约 900px 宽度可用降级，评估 Tauri `minWidth` 配置。

验证：

```bash
cd frontend
npm run typecheck
npm run build
```

结果：

- 2026-06-26：`npm run typecheck` 通过。
- 2026-06-26：`npm run build` 通过。
- 2026-06-26：`git diff --check` 通过。

手动验收：

- 工作台能完成加载项目、选择章节/项目文件、编辑、保存、查看生成状态。
- 约 900px 宽度下无关键内容不可访问或严重重叠。
- 本地后端不可用时读类数据可按现有策略 mock fallback。

## Milestone 4: 推广到章节、生成、知识库

- [x] 章节页复用 `WritingEditor`、章节导航和保存状态组件。
- [x] 生成页拆出 `features/generation` 组件，如生成动作组、任务列表、日志查看。
- [x] 知识库页拆出 `features/knowledge` 组件，如角色列表、角色编辑、剧情要点查看。
- [x] 消除页面内重复表单/按钮/状态样式。

验证：

```bash
cd frontend
npm run typecheck
npm run build
```

结果：

- 2026-06-26：`npm run typecheck` 通过。
- 2026-06-26：`npm run build` 通过。
- 2026-06-26：`git diff --check` 通过。

手动验收：

- [ ] 章节页编辑保存正常。
- [ ] 生成任务创建、列表和日志查看正常。
- [ ] 知识库导入、向量库清理、角色查看/保存路径正常。

## Milestone 5: 设置页与文档收尾

- [x] 设置页表单迁移到基础字段组件。
- [x] 统一配置测试、保存、WebDAV 备份/恢复的状态呈现。
- [x] 更新 `frontend/README.md`，修正 mock-only 旧说明，补充真实 API 与 fallback 说明。
- [x] 如实施中发现新的项目运行约定，更新根目录 `AGENTS.md`。

验证：

```bash
cd frontend
npm run typecheck
npm run build
python -m pytest tests
```

结果：

- 2026-06-26：`npm run typecheck` 通过。
- 2026-06-26：`npm run build` 通过。
- 2026-06-26：`python -m pytest tests` 通过，41 passed。
- 2026-06-26：`git diff --check` 通过。

## 风险与回滚点

- 样式 token 拆分可能影响全页面视觉；Milestone 1 应尽量小步提交。
- `WritingEditor` 替换会影响章节页和工作台保存链路；Milestone 2 需要重点手动验收脏状态。
- 工作台布局重构影响主体验；Milestone 3 应保留旧 store/API 契约，避免同时改后端。
- Tauri `minWidth` 调整可能暴露窄屏布局问题；先验证 UI 再改配置。

## 后续进入实现前检查

- [ ] 用户确认 `prd.md`、`design.md`、`implement.md`。
- [ ] 读取相关 Trellis spec 和前端现有约定。
- [ ] 运行 `git status --short`，确认工作区状态。
- [ ] 明确本轮只执行哪个 milestone，不连续执行整个大型计划。
