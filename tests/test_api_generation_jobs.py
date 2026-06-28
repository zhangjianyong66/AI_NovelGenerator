import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.server import create_app


def write_config(config_file, output_path):
    config_file.write_text(
        json.dumps({"other_params": {"filepath": str(output_path), "chapter_num": "2"}}, ensure_ascii=False),
        encoding="utf-8",
    )


def write_generation_config(config_file, output_path, api_key="test-key"):
    config_file.write_text(
        json.dumps(
            {
                "other_params": {
                    "filepath": str(output_path),
                    "topic": "记忆交易港城",
                    "genre": "悬疑奇幻",
                    "num_chapters": 3,
                    "word_number": 1200,
                    "chapter_num": "2",
                    "user_guidance": "保持悬疑感",
                },
                "choose_configs": {
                    "architecture_llm": "Default",
                    "chapter_outline_llm": "Default",
                },
                "llm_configs": {
                    "Default": {
                        "api_key": api_key,
                        "base_url": "https://example.invalid/v1",
                        "model_name": "test-model",
                        "temperature": 0.7,
                        "max_tokens": 4096,
                        "timeout": 600,
                        "interface_format": "OpenAI",
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def fake_architecture_generate(**kwargs):
    filepath = Path(kwargs["filepath"])
    (filepath / "Novel_architecture.txt").write_text("测试小说设定", encoding="utf-8")


def fake_blueprint_generate(**kwargs):
    filepath = Path(kwargs["filepath"])
    (filepath / "Novel_directory.txt").write_text("第1章：雾港来信", encoding="utf-8")


def test_generation_job_endpoint_creates_lists_and_reads_job(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    (output_path / "chapter_2.txt").write_text("章节正文", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "draft", "chapterNumber": 2},
    )

    assert response.status_code == 200
    job = response.json()
    assert job["projectId"] == "current"
    assert job["stage"] == "draft"
    assert job["status"] == "queued"
    assert job["progress"] == 0
    assert job["error"] is None
    assert "等待执行器接入" in job["log"][-1]

    list_response = client.get("/api/projects/current/jobs")
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [job["id"]]

    read_response = client.get(f"/api/generation-jobs/{job['id']}")
    assert read_response.status_code == 200
    assert read_response.json()["id"] == job["id"]


def test_generation_job_endpoint_supports_core_stages(tmp_path, monkeypatch):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    config_file = tmp_path / "config.json"
    write_generation_config(config_file, output_path)
    monkeypatch.setattr(
        "app.services.generation_executor.Novel_architecture_generate",
        fake_architecture_generate,
    )
    monkeypatch.setattr(
        "app.services.generation_executor.Chapter_blueprint_generate",
        fake_blueprint_generate,
    )
    client = TestClient(create_app(config_file=str(config_file)))

    for stage in ["architecture", "directory", "draft", "finalization", "consistency"]:
        payload = {"projectId": "current", "stage": stage}
        if stage in {"draft", "finalization", "consistency"}:
            (output_path / "chapter_2.txt").write_text("章节正文", encoding="utf-8")
            payload["chapterNumber"] = 2
        response = client.post("/api/generation-jobs", json=payload)
        assert response.status_code == 200
        assert response.json()["stage"] == stage


def test_architecture_generation_job_runs_executor_and_writes_setting(tmp_path, monkeypatch):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    config_file = tmp_path / "config.json"
    write_generation_config(config_file, output_path)
    monkeypatch.setattr(
        "app.services.generation_executor.Novel_architecture_generate",
        fake_architecture_generate,
    )
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "architecture"},
    )

    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "done"
    assert job["progress"] == 100
    assert job["error"] is None
    assert (output_path / "Novel_architecture.txt").read_text(encoding="utf-8") == "测试小说设定"
    assert (output_path / "Novel_setting.txt").read_text(encoding="utf-8") == "测试小说设定"


def test_directory_generation_job_runs_executor_and_writes_directory(tmp_path, monkeypatch):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    (output_path / "Novel_architecture.txt").write_text("测试小说设定", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_generation_config(config_file, output_path)
    monkeypatch.setattr(
        "app.services.generation_executor.Chapter_blueprint_generate",
        fake_blueprint_generate,
    )
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "directory"},
    )

    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "done"
    assert job["progress"] == 100
    assert job["error"] is None
    assert (output_path / "Novel_directory.txt").read_text(encoding="utf-8") == "第1章：雾港来信"


def test_architecture_generation_job_fails_when_api_key_missing(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    config_file = tmp_path / "config.json"
    write_generation_config(config_file, output_path, api_key="")
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "architecture"},
    )

    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "failed"
    assert "缺少 API Key" in job["error"]


def test_directory_generation_job_fails_when_setting_missing(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    config_file = tmp_path / "config.json"
    write_generation_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "directory"},
    )

    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "failed"
    assert "请先生成小说设定" in job["error"]


def test_generation_job_endpoint_uses_default_output_path_when_missing(tmp_path):
    config_file = tmp_path / "config.json"
    write_config(config_file, "")
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "architecture"},
    )

    assert response.status_code == 200
    assert response.json()["stage"] == "architecture"
    assert f"输出路径：{tmp_path / 'output'}" in response.json()["log"]
    assert (tmp_path / "output").is_dir()


def test_generation_job_endpoint_rejects_missing_chapter_for_chapter_stage(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "draft", "chapterNumber": 99},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "章节文件不存在"
