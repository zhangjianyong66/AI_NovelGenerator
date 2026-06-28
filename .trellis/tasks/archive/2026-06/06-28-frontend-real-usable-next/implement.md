# 前端 UI 真实可用后续完善 - Implementation Plan

## Checklist

1. 后端测试先行
   - 扩展 `tests/test_api_chapters.py`：计划章节列表、已有+计划混合排序、创建缺失章节、拒绝覆盖已有章节、创建后保存。
   - 断言响应字段兼容现有 `Chapter` 结构。

2. 后端实现
   - 在 `app/api/server.py` 增加目录章节号解析 helper。
   - 调整章节列表返回已有章节和计划章节的并集。
   - 调整 `_chapter_response(...)` 支持不存在文件返回 `planned`。
   - 新增 `POST /api/chapters/{chapter_number}` 创建缺失章节文件。

3. 前端类型和服务桥
   - 确认 `ChapterStatus` 包含 `planned`。
   - 在 `frontend/src/services/serviceBridge.ts` 新增 `createChapter(chapterOrder)`，不允许 mock fallback。
   - 如 mock 数据需要展示 planned 章节，只改读类预览数据，不添加 mock 写入。

4. 前端 store 和页面
   - 在 `frontend/src/stores/editor.ts` 新增创建当前章节 action。
   - 更新 `frontend/src/pages/ChaptersPage.vue`：planned 章节只读、创建按钮、创建状态/错误提示、保存按钮禁用条件。
   - 保持现有章节保存、切换确认和离线写守卫。

5. 文档更新
   - 更新 `docs/feature-map-and-acceptance.md` 的章节生命周期状态和验收剧本。
   - 若新增的 API/运行约定对后续复用重要，同步更新 `AGENTS.md`。

6. 验证
   - `python -m pytest tests`
   - `cd frontend && npm run typecheck`
   - `cd frontend && npm run build`
   - 视时间进行本地 API 冒烟：临时输出目录只含 `Novel_directory.txt`，确认章节列表返回 planned，创建后文件落盘。

## Risk Points

- 目录解析格式多样：优先复用现有 `get_chapter_info_from_blueprint(...)` 补标题，章节号集合可用保守正则匹配中文/阿拉伯数字章节行；测试覆盖当前文档中的常见格式。
- Store 中 `chapterDrafts` 对 planned 章节为空内容，创建后必须重置为响应正文，避免保留只读状态时产生的临时草稿。
- `serviceBridge` 写接口不能 fallback 到 mock，否则会违反真实后端边界。

## Rollback Points

- 后端章节列表扩展集中在 `app/api/server.py` helper 和章节路由。
- 前端创建入口集中在 `ChaptersPage.vue` 与 `editorStore`。
- 如果 planned 列表导致生成页批量缺章判断变化，需要明确保留“批量缺实际文件”的校验，不能把 planned 当作已有文件。
