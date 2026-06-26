from fastapi.testclient import TestClient

from app.api.server import create_app


def test_health_endpoint_reports_ready_status():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "mode": "backend",
        "service": "AI_NovelGenerator",
    }
