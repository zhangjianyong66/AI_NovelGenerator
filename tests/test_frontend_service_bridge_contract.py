from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SRC = PROJECT_ROOT / "frontend" / "src"


def test_pages_and_stores_do_not_import_mock_api_directly():
    checked_paths = [
        *sorted((FRONTEND_SRC / "pages").glob("*.vue")),
        *sorted((FRONTEND_SRC / "stores").glob("*.ts")),
    ]

    offenders = [
        path.relative_to(PROJECT_ROOT).as_posix()
        for path in checked_paths
        if "mockApi" in path.read_text(encoding="utf-8")
    ]

    assert offenders == []


def test_app_layout_displays_service_bridge_status():
    app_layout = (FRONTEND_SRC / "layouts" / "AppLayout.vue").read_text(encoding="utf-8")

    assert "serviceBridge.checkHealth" in app_layout
    assert "bridgeStatus.mode" in app_layout
    assert "Mock UI" not in app_layout


def test_generation_page_surfaces_real_backend_boundaries():
    generation_page = (FRONTEND_SRC / "pages" / "GenerationPage.vue").read_text(encoding="utf-8")
    job_detail = (
        FRONTEND_SRC / "features" / "generation" / "components" / "GenerationJobDetail.vue"
    ).read_text(encoding="utf-8")

    assert "chapterTargetMessage" in generation_page
    assert "batchValidationMessage" in generation_page
    assert "missingBatchChapters" in generation_page
    assert "normalizeGenerationError" in generation_page
    assert "任务历史保存在本地状态库" in generation_page
    assert "任务已记录在本地任务库" in job_detail
    assert "项目：" in job_detail
    assert "开始：" in job_detail


def test_chapter_page_supports_creating_planned_chapters_through_service_bridge():
    service_bridge = (FRONTEND_SRC / "services" / "serviceBridge.ts").read_text(encoding="utf-8")
    editor_store = (FRONTEND_SRC / "stores" / "editor.ts").read_text(encoding="utf-8")
    chapters_page = (FRONTEND_SRC / "pages" / "ChaptersPage.vue").read_text(encoding="utf-8")

    assert "async createChapter(" in service_bridge
    assert "method: 'POST'" in service_bridge
    assert "async createActiveChapter()" in editor_store
    assert "createActiveChapter" in chapters_page
    assert "isActiveChapterPlanned" in chapters_page
    assert "status === 'planned'" in chapters_page
    assert "创建章节文件" in chapters_page
