# 支持批量草稿定稿审校技术设计

## 方案选择

采用兼容扩展方案：保留现有 `batch` 阶段作为“批量定稿”的兼容别名，同时新增明确阶段：

- `batchDraft`：批量草稿
- `batchFinalization`：批量定稿
- `batchConsistency`：批量审校

前端新建任务时使用明确阶段，后端继续接受旧 `batch` 请求并按 `batchFinalization` 处理。这样可以不破坏已有任务历史、测试语义和旧前端调用。

## 架构边界

- 前端页面：`frontend/src/pages/GenerationPage.vue`
  - 负责展示批量参数、按批量动作选择不同校验规则、调用 store 创建任务。
  - 不直接调用 mock API，仍走 `generationStore` 和 `serviceBridge`。
- 前端动作组件：`frontend/src/features/generation/components/GenerationActions.vue`
  - 负责呈现单章动作和三个批量动作。
- 前端类型：`frontend/src/services/types.ts`
  - 扩展 `GenerationStage`。
- API 层：`app/api/server.py`
  - 负责 stage 白名单、批量范围校验、定稿/审校缺章节的 HTTP 400 前置校验、任务日志基础信息。
  - `batchDraft` 不做缺章校验。
  - `batchFinalization`、`batchConsistency` 做缺章校验。
- 执行器：`app/services/generation_executor.py`
  - 负责逐章运行 `_run_draft`、`_run_finalization`、`_run_consistency`。
  - 单章失败后继续下一章。
  - 汇总为统一的 `GenerationExecutionResult`。

## 数据流

1. 用户在生成任务页填写起始章节、结束章节、目标字数、最低字数、自动扩写。
2. 用户点击 `批量草稿` / `批量定稿` / `批量审校`。
3. 前端按动作做本地校验：
   - 批量草稿：只校验范围和字数非负。
   - 批量定稿、批量审校：校验范围、字数非负、目标章节文件存在。
4. 前端发送 `POST /api/generation-jobs`：
   - `stage=batchDraft|batchFinalization|batchConsistency`
   - `startChapter/endChapter/targetWords/minimumWords/autoEnrich`
5. API 保存任务请求和初始日志。
6. 执行器逐章运行对应单章函数。
7. API 保存最终状态、日志和错误。
8. 前端刷新任务列表，批量草稿/批量定稿完成后刷新章节上下文。

## 错误处理

- 无效范围：HTTP 400，`detail="批量生成章节范围无效"`。
- 批量定稿/审校缺章节文件：HTTP 400，`detail="章节文件不存在：<chapter>"`。
- 批量草稿缺目录、缺模型、缺 API Key、单章旧函数失败：任务返回 `failed`，日志保留每章失败原因。
- 批量草稿遇到已有根部 `chapter_X.txt`：默认跳过，不覆盖正文；跳过不计入失败，日志记录“第 X 章已存在，跳过草稿生成”。
- 批量执行任一章节失败：任务状态为 `failed`，`error` 使用“部分失败：成功章节 ...；失败章节 ...”。
- 批量审校不写回项目文件，只追加审校结果到任务日志。

## 兼容性

- `batch` 继续作为后端可接受 stage，标题和行为保持“批量定稿章节”。
- 新前端不再发送 `batch`，而是发送 `batchFinalization`。
- 历史任务列表只展示已有 `stage` 字符串；详情组件需要为新 stage 增加标签。
- 不改变旧 GUI 和旧生成函数签名。
- 批量草稿不提供强制覆盖选项；用户要重生成已有章节时，先手动删除该章文件，后续可单独设计覆盖开关。

## 文档更新

- 更新 `docs/feature-map-and-acceptance.md` 中“批量第一版只定稿”的说明。
- 更新 `AGENTS.md` 中本地 API 生成任务接口和执行器说明。
- 如果新增 stage 名称后形成稳定项目约定，补充 `.trellis/spec/backend/error-handling.md` 或相关规范。
