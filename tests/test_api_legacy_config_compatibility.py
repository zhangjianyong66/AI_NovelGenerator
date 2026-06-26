from fastapi.testclient import TestClient

from app.api.server import create_app
from config_manager import load_config


def test_frontend_saved_config_remains_readable_by_legacy_config_manager(tmp_path):
    config_file = tmp_path / "config.json"
    client = TestClient(create_app(config_file=str(config_file)))

    project_response = client.put(
        "/api/project-config",
        json={
            "outputPath": str(tmp_path / "novel"),
            "novelParams": {
                "topic": "旧 GUI 兼容主题",
                "genre": "测试",
                "numChapters": 12,
                "wordNumber": 3000,
                "chapterNum": "2",
                "userGuidance": "保持兼容",
                "charactersInvolved": "林澈",
                "keyItems": "钥匙",
                "sceneLocation": "港口",
                "timeConstraint": "夜晚",
            },
        },
    )
    assert project_response.status_code == 200

    webdav_response = client.put(
        "/api/webdav-config",
        json={
            "webdavUrl": "https://dav.example.com/root",
            "username": "user",
            "password": "secret",
            "hasPassword": False,
        },
    )
    assert webdav_response.status_code == 200

    loaded = load_config(str(config_file))

    assert loaded["other_params"]["filepath"] == str(tmp_path / "novel")
    assert loaded["other_params"]["topic"] == "旧 GUI 兼容主题"
    assert loaded["other_params"]["characters_involved"] == "林澈"
    assert loaded["webdav_config"]["webdav_url"] == "https://dav.example.com/root"
    assert loaded["webdav_config"]["webdav_password"] == "secret"
