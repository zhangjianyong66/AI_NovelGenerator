import json

from fastapi.testclient import TestClient

from app.api.server import create_app


def write_model_config(config_file):
    config_file.write_text(
        json.dumps(
            {
                "last_interface_format": "OpenAI",
                "last_embedding_interface_format": "Ollama",
                "llm_configs": {
                    "Default": {
                        "api_key": "secret-key",
                        "base_url": "https://api.example.com/v1",
                        "model_name": "test-model",
                        "temperature": 0.7,
                        "max_tokens": 4096,
                        "timeout": 600,
                        "interface_format": "OpenAI",
                    }
                },
                "embedding_configs": {
                    "Ollama": {
                        "api_key": "",
                        "base_url": "http://127.0.0.1:11434",
                        "model_name": "nomic-embed-text",
                        "retrieval_k": 4,
                        "interface_format": "Ollama",
                    }
                },
                "choose_configs": {
                    "prompt_draft_llm": "Default",
                    "chapter_outline_llm": "Default",
                    "architecture_llm": "Default",
                    "final_chapter_llm": "Default",
                    "consistency_review_llm": "Default",
                },
                "proxy_setting": {
                    "proxy_url": "127.0.0.1",
                    "proxy_port": "7890",
                    "enabled": True,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_model_settings_endpoint_loads_configs_without_exposing_secrets(tmp_path):
    config_file = tmp_path / "config.json"
    write_model_config(config_file)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.get("/api/model-settings")

    assert response.status_code == 200
    data = response.json()
    assert data["selectedLlmConfig"] == "Default"
    assert data["selectedEmbeddingConfig"] == "Ollama"
    assert data["llmConfigs"][0]["name"] == "Default"
    assert data["llmConfigs"][0]["apiKey"] == ""
    assert data["llmConfigs"][0]["hasApiKey"] is True
    assert data["embeddingConfigs"][0]["name"] == "Ollama"
    assert data["proxySetting"] == {
        "proxyUrl": "127.0.0.1",
        "proxyPort": "7890",
        "enabled": True,
    }
    assert data["stageModelSelection"]["architecture"] == "Default"


def test_model_settings_endpoint_replaces_missing_stage_selection_with_existing_config(tmp_path):
    config_file = tmp_path / "config.json"
    write_model_config(config_file)
    config = json.loads(config_file.read_text(encoding="utf-8"))
    config["llm_configs"]["Backup"] = {
        "api_key": "backup-secret",
        "base_url": "https://backup.example.com/v1",
        "model_name": "backup-model",
        "temperature": 0.8,
        "max_tokens": 4096,
        "timeout": 600,
        "interface_format": "OpenAI",
    }
    config["choose_configs"]["architecture_llm"] = "Deleted Gemini"
    config_file.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.get("/api/model-settings")

    assert response.status_code == 200
    data = response.json()
    assert data["stageModelSelection"]["architecture"] == "Default"


def test_model_settings_endpoint_saves_legacy_config_and_preserves_masked_secret(tmp_path):
    config_file = tmp_path / "config.json"
    write_model_config(config_file)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.put(
        "/api/model-settings",
        json={
            "selectedLlmConfig": "Default",
            "selectedEmbeddingConfig": "Ollama",
            "llmConfigs": [
                {
                    "name": "Default",
                    "apiKey": "",
                    "hasApiKey": True,
                    "baseUrl": "https://api.changed.test/v1",
                    "modelName": "changed-model",
                    "temperature": 0.6,
                    "maxTokens": 8192,
                    "timeout": 300,
                    "interfaceFormat": "OpenAI",
                },
                {
                    "name": "Backup",
                    "apiKey": "new-secret",
                    "hasApiKey": True,
                    "baseUrl": "https://backup.example.com/v1",
                    "modelName": "backup-model",
                    "temperature": 0.8,
                    "maxTokens": 4096,
                    "timeout": 600,
                    "interfaceFormat": "OpenAI",
                },
            ],
            "embeddingConfigs": [
                {
                    "name": "Ollama",
                    "apiKey": "",
                    "hasApiKey": False,
                    "baseUrl": "http://127.0.0.1:11434",
                    "modelName": "nomic-embed-text",
                    "retrievalK": 6,
                    "interfaceFormat": "Ollama",
                }
            ],
            "proxySetting": {
                "proxyUrl": "127.0.0.1",
                "proxyPort": "7891",
                "enabled": False,
            },
            "stageModelSelection": {
                "promptDraft": "Backup",
                "chapterOutline": "Default",
                "architecture": "Default",
                "finalChapter": "Backup",
                "consistencyReview": "Default",
            },
        },
    )

    assert response.status_code == 200
    saved = json.loads(config_file.read_text(encoding="utf-8"))
    assert saved["llm_configs"]["Default"]["api_key"] == "secret-key"
    assert saved["llm_configs"]["Default"]["base_url"] == "https://api.changed.test/v1"
    assert saved["llm_configs"]["Backup"]["api_key"] == "new-secret"
    assert saved["embedding_configs"]["Ollama"]["retrieval_k"] == 6
    assert saved["proxy_setting"]["proxy_port"] == "7891"
    assert saved["choose_configs"]["prompt_draft_llm"] == "Backup"
    assert saved["choose_configs"]["chapter_outline_llm"] == "Default"
    assert saved["choose_configs"]["architecture_llm"] == "Default"
    assert saved["choose_configs"]["final_chapter_llm"] == "Backup"
    assert saved["choose_configs"]["consistency_review_llm"] == "Default"


def test_llm_config_test_reports_missing_secret_without_network_call(tmp_path):
    config_file = tmp_path / "config.json"
    write_model_config(config_file)
    config = json.loads(config_file.read_text(encoding="utf-8"))
    config["llm_configs"]["Default"]["api_key"] = ""
    config_file.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post("/api/model-settings/test-llm", json={"configName": "Default"})

    assert response.status_code == 200
    assert response.json() == {
        "success": False,
        "message": "LLM 配置缺少 API Key",
    }
