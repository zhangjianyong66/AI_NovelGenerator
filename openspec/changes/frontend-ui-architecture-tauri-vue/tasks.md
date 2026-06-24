## 1. 前端工程骨架

- [x] 1.1 创建 `frontend/` 目录并初始化 Tauri + Vue + TypeScript + Vite 工程
- [x] 1.2 配置基础脚本、TypeScript、Vite 和 Tauri 开发配置
- [x] 1.3 建立 `src/` 下的 `router/`、`layouts/`、`pages/`、`components/`、`stores/`、`services/`、`styles/` 目录
- [x] 1.4 添加前端启动说明，明确新前端与 `python main.py` 并行存在

## 2. 应用壳层与路由

- [x] 2.1 实现 Vue 应用入口和全局样式 token
- [x] 2.2 实现应用壳层布局，包括顶部状态栏、左侧导航、中央内容区和右侧上下文区
- [x] 2.3 配置路由页面：项目、工作台、章节编辑、生成任务、设置、知识库
- [x] 2.4 确认各路由可在开发模式下正常切换

## 3. Mock 数据边界与状态管理

- [x] 3.1 定义前端类型：Project、Chapter、GenerationJob、ModelConfig、KnowledgeItem
- [x] 3.2 实现 `mockApi`，提供项目、章节、任务、配置和知识库 mock 数据
- [x] 3.3 建立 Pinia stores，封装项目、编辑器和生成任务 UI 状态
- [x] 3.4 确认页面只依赖 mock service 和 stores，不调用真实 Python 后端

## 4. 工作台页面骨架

- [x] 4.1 实现项目页，展示 mock 项目入口
- [x] 4.2 实现工作台页，展示小说设定、目录蓝图、章节正文和上下文面板的主要区域
- [x] 4.3 实现章节编辑页，展示章节列表、章节内容编辑区和章节元信息
- [x] 4.4 实现生成任务页，展示 mock 任务状态、日志和生成操作入口

## 5. 配置与知识库页面骨架

- [x] 5.1 实现设置页，展示模型、Embedding 和代理配置区域的 UI 骨架
- [x] 5.2 实现知识库页，展示知识文件和角色库区域的 UI 骨架
- [x] 5.3 确认所有页面在无真实后端服务时可渲染并展示 mock 数据

## 6. 验证与文档

- [x] 6.1 运行前端类型检查和构建命令
- [x] 6.2 运行现有 Python 测试，确认本变更未影响现有后端与 GUI
- [x] 6.3 验证 `python main.py` 仍作为现有 GUI 入口
- [x] 6.4 更新项目说明，记录 Tauri + Vue 前端的目录结构、启动方式和并行迁移边界
