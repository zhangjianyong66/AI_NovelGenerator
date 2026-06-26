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


def test_local_frontend_origin_is_allowed_for_api_requests():
    client = TestClient(create_app())

    response = client.options(
        "/api/projects/p-ember-city/chapters",
        headers={
            "Origin": "http://127.0.0.1:1420",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:1420"
