import json

from fastapi.testclient import TestClient

from app.api.server import create_app
from novel_generator.knowledge import KnowledgeImportResult
from novel_generator.vectorstore_utils import load_vector_store


def write_config(config_file, output_path, embedding_config=None):
    config = {"other_params": {"filepath": str(output_path)}}
    if embedding_config is not None:
        config.update(embedding_config)
    config_file.write_text(
        json.dumps(config, ensure_ascii=False),
        encoding="utf-8",
    )


def embedding_config(
    *,
    selected="Ollama",
    model_name="nomic-embed-text",
    api_key="",
    interface_format="Ollama",
):
    return {
        "last_embedding_interface_format": selected,
        "embedding_configs": {
            selected: {
                "api_key": api_key,
                "base_url": "http://localhost:11434/api",
                "model_name": model_name,
                "retrieval_k": 4,
                "interface_format": interface_format,
            }
        },
    }


def test_knowledge_import_vectorizes_and_copies_file(tmp_path, monkeypatch):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    source_file = tmp_path / "world.txt"
    source_file.write_text("世界观资料", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path, embedding_config())
    calls = []

    def fake_import_knowledge_file(**kwargs):
        calls.append(kwargs)
        vectorstore = output_path / "vectorstore"
        vectorstore.mkdir(parents=True, exist_ok=True)
        (vectorstore / "chroma.sqlite3").write_text("vector", encoding="utf-8")
        return KnowledgeImportResult(success=True, message="导入成功", segment_count=2)

    monkeypatch.setattr("app.api.server.import_knowledge_to_vectorstore", fake_import_knowledge_file)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post("/api/knowledge/import", json={"filePath": str(source_file)})

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "已导入 world.txt 并写入向量库，共 2 个片段"}
    assert calls == [
        {
            "embedding_api_key": "",
            "embedding_url": "http://localhost:11434/api",
            "embedding_interface_format": "Ollama",
            "embedding_model_name": "nomic-embed-text",
            "file_path": str(source_file),
            "filepath": str(output_path),
        }
    ]
    imported_file = output_path / "vectorstore" / "imported" / "world.txt"
    assert imported_file.read_text(encoding="utf-8") == "世界观资料"
    list_response = client.get("/api/knowledge")
    assert list_response.status_code == 200
    [knowledge_file] = [item for item in list_response.json() if item["type"] == "file"]
    assert knowledge_file["tags"] == ["导入文件", "已向量化"]


def test_knowledge_import_requires_embedding_config(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    source_file = tmp_path / "world.txt"
    source_file.write_text("世界观资料", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post("/api/knowledge/import", json={"filePath": str(source_file)})

    assert response.status_code == 400
    assert response.json()["detail"] == "请先配置 Embedding 模型"


def test_knowledge_import_requires_embedding_model_name(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    source_file = tmp_path / "world.txt"
    source_file.write_text("世界观资料", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path, embedding_config(model_name=""))
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post("/api/knowledge/import", json={"filePath": str(source_file)})

    assert response.status_code == 400
    assert response.json()["detail"] == "Embedding 配置缺少模型名称"


def test_knowledge_import_requires_api_key_for_remote_embedding(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    source_file = tmp_path / "world.txt"
    source_file.write_text("世界观资料", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_config(
        config_file,
        output_path,
        embedding_config(selected="OpenAI", interface_format="OpenAI", model_name="text-embedding-ada-002"),
    )
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post("/api/knowledge/import", json={"filePath": str(source_file)})

    assert response.status_code == 400
    assert response.json()["detail"] == "Embedding 配置缺少 API Key"


def test_knowledge_import_allows_local_embedding_without_api_key(tmp_path, monkeypatch):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    source_file = tmp_path / "world.txt"
    source_file.write_text("世界观资料", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_config(
        config_file,
        output_path,
        embedding_config(selected="LM Studio", interface_format="ML Studio", model_name="text-embedding-nomic-embed-text-v1.5"),
    )

    def fake_import_knowledge_file(**kwargs):
        return KnowledgeImportResult(success=True, message="导入成功", segment_count=1)

    monkeypatch.setattr("app.api.server.import_knowledge_to_vectorstore", fake_import_knowledge_file)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post("/api/knowledge/import", json={"filePath": str(source_file)})

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_knowledge_import_returns_error_when_vectorization_fails(tmp_path, monkeypatch):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    source_file = tmp_path / "world.txt"
    source_file.write_text("世界观资料", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path, embedding_config())

    def fake_import_knowledge_file(**kwargs):
        return KnowledgeImportResult(success=False, message="向量库导入失败", segment_count=0)

    monkeypatch.setattr("app.api.server.import_knowledge_to_vectorstore", fake_import_knowledge_file)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post("/api/knowledge/import", json={"filePath": str(source_file)})

    assert response.status_code == 400
    assert response.json()["detail"] == "向量库导入失败"
    assert not (output_path / "vectorstore" / "imported" / "world.txt").exists()


def test_legacy_knowledge_import_writes_retrievable_vectorstore(tmp_path, monkeypatch):
    class FakeEmbeddingAdapter:
        def embed_documents(self, texts):
            return [self.embed_query(text) for text in texts]

        def embed_query(self, query):
            return [1.0, 0.0] if "港城" in query else [0.0, 1.0]

    import embedding_adapters
    from novel_generator import knowledge

    output_path = tmp_path / "novel"
    output_path.mkdir()
    source_file = tmp_path / "knowledge.txt"
    source_file.write_text("港城知识：记忆可以被典当。", encoding="utf-8")
    embedding_adapter = FakeEmbeddingAdapter()

    monkeypatch.setattr(knowledge, "advanced_split_content", lambda content: [content])
    monkeypatch.setattr(embedding_adapters, "create_embedding_adapter", lambda *args: embedding_adapter)

    result = knowledge.import_knowledge_file(
        embedding_api_key="",
        embedding_url="http://localhost:11434/api",
        embedding_interface_format="Ollama",
        embedding_model_name="nomic-embed-text",
        file_path=str(source_file),
        filepath=str(output_path),
    )

    assert result == KnowledgeImportResult(success=True, message="知识库文件已导入至向量库", segment_count=1)
    store = load_vector_store(embedding_adapter, str(output_path))
    docs = store.similarity_search("港城", k=1)
    assert docs[0].page_content == "港城知识：记忆可以被典当。"


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
