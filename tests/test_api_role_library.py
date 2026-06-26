import json

from fastapi.testclient import TestClient

from app.api.server import create_app


def write_config(config_file, output_path):
    config_file.write_text(
        json.dumps(
            {
                "other_params": {
                    "filepath": str(output_path),
                    "characters_involved": "",
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_role_library_endpoint_lists_categories_and_roles(tmp_path):
    output_path = tmp_path / "novel"
    role_dir = output_path / "角色库" / "主角"
    role_dir.mkdir(parents=True)
    (role_dir / "林澈.txt").write_text("林澈：调查员", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.get("/api/roles")

    assert response.status_code == 200
    assert response.json() == [
        {
            "name": "主角",
            "roles": [
                {
                    "id": "主角/林澈",
                    "category": "主角",
                    "name": "林澈",
                    "filename": "林澈.txt",
                    "wordCount": 6,
                }
            ],
        }
    ]


def test_role_library_endpoint_reads_and_saves_role_content(tmp_path):
    output_path = tmp_path / "novel"
    role_dir = output_path / "角色库" / "主角"
    role_dir.mkdir(parents=True)
    (role_dir / "林澈.txt").write_text("旧内容", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    read_response = client.get("/api/roles/主角/林澈")
    assert read_response.status_code == 200
    assert read_response.json()["content"] == "旧内容"

    save_response = client.put("/api/roles/主角/林澈", json={"content": "新内容"})
    assert save_response.status_code == 200
    assert save_response.json()["content"] == "新内容"
    assert (role_dir / "林澈.txt").read_text(encoding="utf-8") == "新内容"


def test_role_library_import_copies_role_file_to_category(tmp_path):
    output_path = tmp_path / "novel"
    source_file = tmp_path / "米拉.txt"
    source_file.write_text("米拉：领航员", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post("/api/roles/import", json={"category": "配角", "filePath": str(source_file)})

    assert response.status_code == 200
    assert response.json()["name"] == "米拉"
    assert (output_path / "角色库" / "配角" / "米拉.txt").read_text(encoding="utf-8") == "米拉：领航员"


def test_role_library_rejects_invalid_role_name(tmp_path):
    output_path = tmp_path / "novel"
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.put("/api/roles/主角/%5C坏角色", json={"content": ""})

    assert response.status_code == 400
