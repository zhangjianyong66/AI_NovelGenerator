import json

from fastapi.testclient import TestClient

from app.api.server import create_app


def write_config(config_file):
    config_file.write_text(
        json.dumps(
            {
                "llm_configs": {},
                "embedding_configs": {},
                "other_params": {},
                "choose_configs": {},
                "webdav_config": {
                    "webdav_url": "https://dav.example.com/root",
                    "webdav_username": "user",
                    "webdav_password": "secret",
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_webdav_config_endpoint_masks_and_preserves_password(tmp_path):
    config_file = tmp_path / "config.json"
    write_config(config_file)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.get("/api/webdav-config")

    assert response.status_code == 200
    assert response.json() == {
        "webdavUrl": "https://dav.example.com/root",
        "username": "user",
        "password": "",
        "hasPassword": True,
    }

    save_response = client.put(
        "/api/webdav-config",
        json={
            "webdavUrl": "https://dav.example.com/changed",
            "username": "changed",
            "password": "",
            "hasPassword": True,
        },
    )

    assert save_response.status_code == 200
    saved = json.loads(config_file.read_text(encoding="utf-8"))
    assert saved["webdav_config"]["webdav_url"] == "https://dav.example.com/changed"
    assert saved["webdav_config"]["webdav_username"] == "changed"
    assert saved["webdav_config"]["webdav_password"] == "secret"


def test_webdav_test_connection_uses_propfind_and_saves_successful_settings(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    write_config(config_file)
    calls = []

    class Response:
        def raise_for_status(self):
            return None

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return Response()

    monkeypatch.setattr("app.api.server.requests.request", fake_request)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/webdav/test",
        json={
            "webdavUrl": "https://dav.example.com/new-root",
            "username": "new-user",
            "password": "new-secret",
            "hasPassword": False,
        },
    )

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "WebDAV 连接成功"}
    assert calls[0][0] == "PROPFIND"
    saved = json.loads(config_file.read_text(encoding="utf-8"))
    assert saved["webdav_config"]["webdav_password"] == "new-secret"


def test_webdav_backup_uploads_config_file(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    write_config(config_file)
    uploaded = {}

    class Response:
        def raise_for_status(self):
            return None

    def fake_put(url, data, **kwargs):
        uploaded["url"] = url
        uploaded["content"] = data.read().decode("utf-8")
        return Response()

    monkeypatch.setattr("app.api.server.requests.put", fake_put)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post("/api/webdav/backup")

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "配置备份成功"}
    assert uploaded["url"] == "https://dav.example.com/root/AI_Novel_Generator/config.json"
    assert "webdav_config" in uploaded["content"]


def test_webdav_restore_creates_local_backup_and_replaces_config(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    write_config(config_file)
    restored_config = {
        "llm_configs": {"Restored": {}},
        "embedding_configs": {},
        "other_params": {},
        "choose_configs": {},
    }

    class Response:
        content = json.dumps(restored_config).encode("utf-8")

        def raise_for_status(self):
            return None

    monkeypatch.setattr("app.api.server.requests.get", lambda *args, **kwargs: Response())
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post("/api/webdav/restore")

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "配置恢复成功"}
    assert json.loads(config_file.read_text(encoding="utf-8")) == restored_config
    backups = list((tmp_path / "backup").glob("config_*_bak.json"))
    assert len(backups) == 1
