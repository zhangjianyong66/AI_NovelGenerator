import json

from fastapi.testclient import TestClient

from app.api.server import create_app


def write_config(config_file, output_path):
    config_file.write_text(
        json.dumps(
            {
                "other_params": {
                    "filepath": str(output_path),
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_project_files_endpoint_loads_core_files_and_word_counts(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    (output_path / "Novel_setting.txt").write_text("世界观设定\n主角登场", encoding="utf-8")
    (output_path / "Novel_directory.txt").write_text("第一章 雨夜\n第二章 旧案", encoding="utf-8")
    (output_path / "character_state.txt").write_text("林澈：怀疑旧记忆", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.get("/api/project-files")

    assert response.status_code == 200
    files = response.json()
    assert [item["id"] for item in files] == [
        "novelSetting",
        "novelDirectory",
        "characterState",
        "globalSummary",
    ]
    setting = files[0]
    assert setting["filename"] == "Novel_setting.txt"
    assert setting["content"] == "世界观设定\n主角登场"
    assert setting["exists"] is True
    assert setting["wordCount"] == 9
    assert files[3]["filename"] == "global_summary.txt"
    assert files[3]["content"] == ""
    assert files[3]["exists"] is False


def test_project_file_endpoint_saves_core_file_in_active_output_path(tmp_path):
    output_path = tmp_path / "novel"
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.put(
        "/api/project-files/globalSummary",
        json={"content": "全局摘要\n第二行"},
    )

    assert response.status_code == 200
    assert response.json()["content"] == "全局摘要\n第二行"
    assert response.json()["wordCount"] == 7
    assert (output_path / "global_summary.txt").read_text(encoding="utf-8") == "全局摘要\n第二行"


def test_project_files_endpoint_uses_default_output_path_when_missing(tmp_path):
    config_file = tmp_path / "config.json"
    write_config(config_file, "")
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.get("/api/project-files")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [
        "novelSetting",
        "novelDirectory",
        "characterState",
        "globalSummary",
    ]
    assert all(item["exists"] is False for item in response.json())
    assert (tmp_path / "output").is_dir()


def test_project_file_endpoint_rejects_unknown_file_id(tmp_path):
    output_path = tmp_path / "novel"
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.put("/api/project-files/unknown", json={"content": ""})

    assert response.status_code == 404
