import json

from fastapi.testclient import TestClient

from app.api.server import create_app


def write_config(config_file, output_path, **other_params):
    params = {
        "filepath": str(output_path),
        "topic": "雾城余烬",
        "genre": "悬疑",
        "num_chapters": 4,
        "word_number": 3000,
        "chapter_num": "2",
        **other_params,
    }
    config_file.write_text(
        json.dumps({"other_params": params}, ensure_ascii=False),
        encoding="utf-8",
    )


def test_projects_endpoint_returns_current_project_from_config_and_output_files(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    (output_path / "chapter_1.txt").write_text("第一章正文", encoding="utf-8")
    (output_path / "chapter_3.txt").write_text("第三章正文", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.get("/api/projects")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "current",
            "title": "雾城余烬",
            "genre": "悬疑",
            "status": "active",
            "summary": str(output_path),
            "updatedAt": "",
            "chaptersTotal": 4,
            "chaptersCompleted": 2,
        }
    ]


def test_knowledge_endpoint_lists_imported_files_and_role_files(tmp_path):
    output_path = tmp_path / "novel"
    imported_dir = output_path / "vectorstore" / "imported"
    imported_dir.mkdir(parents=True)
    (imported_dir / "world.txt").write_text("世界资料", encoding="utf-8")
    role_dir = output_path / "角色库" / "主角"
    role_dir.mkdir(parents=True)
    (role_dir / "林澈.txt").write_text("侦探", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.get("/api/knowledge")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "file/world.txt",
            "type": "file",
            "name": "world.txt",
            "description": "vectorstore/imported/world.txt",
            "tags": ["导入文件"],
            "updatedAt": "",
        },
        {
            "id": "role/主角/林澈",
            "type": "role",
            "name": "林澈",
            "description": "主角/林澈.txt",
            "tags": ["角色库", "主角"],
            "updatedAt": "",
        },
    ]
