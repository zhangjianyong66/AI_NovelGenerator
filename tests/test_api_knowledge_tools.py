import json

from fastapi.testclient import TestClient

from app.api.server import create_app


def write_config(config_file, output_path):
    config_file.write_text(
        json.dumps({"other_params": {"filepath": str(output_path)}}, ensure_ascii=False),
        encoding="utf-8",
    )


def test_knowledge_import_copies_file_into_project_vectorstore(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    source_file = tmp_path / "world.txt"
    source_file.write_text("世界观资料", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post("/api/knowledge/import", json={"filePath": str(source_file)})

    assert response.status_code == 200
    assert response.json()["success"] is True
    imported_file = output_path / "vectorstore" / "imported" / "world.txt"
    assert imported_file.read_text(encoding="utf-8") == "世界观资料"


def test_knowledge_import_rejects_missing_file(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post("/api/knowledge/import", json={"filePath": str(tmp_path / "missing.txt")})

    assert response.status_code == 400
    assert response.json()["detail"] == "知识文件不存在"


def test_vectorstore_clear_removes_project_vectorstore(tmp_path):
    output_path = tmp_path / "novel"
    vectorstore = output_path / "vectorstore"
    vectorstore.mkdir(parents=True)
    (vectorstore / "index.bin").write_text("vector", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post("/api/knowledge/clear-vectorstore")

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "向量库已清理"}
    assert not vectorstore.exists()


def test_plot_arcs_endpoint_reads_existing_or_missing_file(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    missing_response = client.get("/api/knowledge/plot-arcs")
    assert missing_response.status_code == 200
    assert missing_response.json() == {"exists": False, "content": "", "wordCount": 0}

    (output_path / "plot_arcs.txt").write_text("主线A\n支线B", encoding="utf-8")
    existing_response = client.get("/api/knowledge/plot-arcs")
    assert existing_response.status_code == 200
    assert existing_response.json() == {"exists": True, "content": "主线A\n支线B", "wordCount": 6}
