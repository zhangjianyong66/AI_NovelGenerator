# 前端 UI 重构技术架构设计

## 推荐结论

采用“保守增强现有 Tauri 2 + Vue 3 + TypeScript + Vite 架构”的路线，不引入大型第三方 UI 组件库，不引入 Vue Query，不引入 TipTap / ProseMirror / Monaco。第一阶段建设项目内轻量设计系统、轻量 feature 分层、`WritingEditor` 适配层和工作台优先的信息架构。

## 架构目标

- 把前端从页面堆叠演进为可维护的桌面写作工具架构。
- 让工作台成为章节编辑器中心：中间长文本编辑，侧边轨道承载章节/文件导航、上下文资料和生成动作。
- 保留真实 API 与 Mock fallback 的 `serviceBridge` 边界，页面和组件不直接耦合 mock 或 fetch。
- 将通用 UI、业务组件、状态管理和服务访问边界拆清楚，降低后续页面迁移成本。

## 非目标

- 不替换现有前端技术栈。
- 不引入 Element Plus、Naive UI、Ant Design Vue 等大型组件库。
- 不在第一阶段建设完整主题系统或深浅色主题切换。
- 不在第一阶段引入专业编辑器内核。
- 不做手机端完整创作体验。
- 不改变后端 API 契约和旧 Python GUI 入口。

## 前端分层

```text
frontend/src/
  components/ui/          # 无业务语义的基础 UI 组件
  features/
    writing/              # 工作台、章节编辑、项目文件编辑相关业务组件和 store/composable
    generation/           # 生成动作、任务列表、日志轨道
    knowledge/            # 知识库、角色库、剧情要点
    settings/             # 设置页表单业务组件，可后置迁移
  layouts/                # 应用壳层与页面框架
  pages/                  # 路由级页面，逐步变薄
  router/                 # 路由配置
  services/               # serviceBridge、API DTO、mock fallback
  stores/                 # 迁移期保留全局 store；新业务 store 可下沉到 feature
  styles/                 # token、base、全局工具样式
```

迁移期允许 `stores/` 与 `features/*/stores/` 共存。新增复杂业务状态优先放入 feature；跨全局的应用壳状态才保留在全局 store。

## 设计系统边界

第一阶段只做基础组件和样式 token：

- `styles/tokens.css`：颜色、字号、间距、圆角、阴影、层级、布局尺寸。
- `styles/base.css`：body、表单控件、focus、禁用态、滚动条、可访问性基础。
- `components/ui/`：`AppButton`、`IconButton`、`TextField`、`TextAreaField`、`SelectField`、`ToggleField`、`SplitPane`、`Toolbar`、`EmptyState`、`LoadingState`、`SaveState`。

现有 `PageHeader`、`ActionBar`、`StatusMessage`、`FormSection`、`Tabs`、`LongTextEditor`、`ConfirmPanel` 应逐步对齐新 token 和基础组件命名，不要求一次性删除。

## 工作台信息架构

工作台以章节编辑器为中心：

```text
WorkbenchLayout
  left rail: 项目文件、章节列表、当前项目摘要
  center: WritingEditor
  right rail: 上下文资料、生成动作、任务状态、日志摘要
```

核心业务组件：

- `WritingEditor`：封装增强版 textarea 的统一适配层。
- `ChapterNavigator`：章节列表、上一章/下一章、脏状态切换保护。
- `ProjectFileNavigator`：小说设定、目录蓝图、角色状态、全局摘要。
- `ContextRail`：目录蓝图、角色状态、全局摘要、剧情要点入口。
- `GenerationRail`：针对当前章节/文件的生成动作、运行任务、日志摘要。

## 编辑器策略

第一阶段继续使用增强版 `textarea`，但所有页面通过 `WritingEditor` 适配层访问，不直接依赖底层 textarea。`WritingEditor` 应暴露稳定契约：

- 输入：`modelValue`、`title`、`subtitle`、`readonly`、`disabled`、`dirty`、`saveState`、`minHeight`。
- 输出：`update:modelValue`、`save`、`focus` 等必要事件。
- 内部能力：字数统计、段落统计、选区统计、空状态、保存状态、只读状态、可替换编辑器根节点。

后续如需 TipTap / ProseMirror / Monaco，应只替换 `WritingEditor` 内部实现，页面和业务组件不改契约。

## 状态与数据流

第一阶段继续使用 Pinia + `serviceBridge`：

```text
页面/业务组件
  ↓ props/events
feature composables
  ↓
feature stores / Pinia stores
  ↓
serviceBridge
  ↓
本地 FastAPI 或 mock fallback
```

规范：

- 组件不直接调用 `fetch` 或 `mockApi`。
- 页面尽量不直接拼装复杂 async 流程，抽到 feature composable。
- store 统一维护 `isLoading`、`isSaving`、`error`、`lastSavedAt` 或等价 async state。
- 真实保存类操作必须走后端接口，mock fallback 仅用于读类展示或明确允许的测试路径。

## 响应式与桌面窗口

- 主目标：桌面窗口，1280px 以上体验最佳。
- 降级目标：约 900px 宽度仍可用。
- 降级方式：右侧上下文/生成轨道可折叠或切换为 tabs；左侧导航可压缩。
- 非目标：手机端完整创作体验。
- 现状差异：`frontend/src-tauri/tauri.conf.json` 当前 `minWidth` 为 1080，后续实现时应评估是否调整到 900 附近。

## 取舍

- 不引入大型 UI 组件库：减少模板感、样式覆盖和长期绑定，代价是基础组件需要自己补齐。
- 不引入 Vue Query：避免服务端缓存状态和编辑草稿状态混杂，代价是需要规范 Pinia async state。
- 不引入专业编辑器内核：降低第一阶段复杂度，代价是长文高级能力暂时有限。
- 工作台优先：先验证最复杂体验，代价是其他页面统一视觉需要后续 milestone 推广。

## 文档同步

`frontend/README.md` 目前仍写着“只使用 mock 数据”，已落后于 `serviceBridge` 和本地 API 现状。执行阶段应更新 README，说明真实 API、mock fallback 和常用启动命令。
