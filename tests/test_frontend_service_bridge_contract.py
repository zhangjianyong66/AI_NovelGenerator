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
