import json

from fastapi.testclient import TestClient

from app.api.server import create_app


def write_config(config_file, output_path):
    config_file.write_text(
        json.dumps({"other_params": {"filepath": str(output_path), "chapter_num": "2"}}, ensure_ascii=False),
        encoding="utf-8",
    )


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


def test_generation_job_endpoint_supports_core_stages(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    for stage in ["architecture", "directory", "draft", "finalization", "consistency"]:
        payload = {"projectId": "current", "stage": stage}
        if stage in {"draft", "finalization", "consistency"}:
            (output_path / "chapter_2.txt").write_text("章节正文", encoding="utf-8")
            payload["chapterNumber"] = 2
        response = client.post("/api/generation-jobs", json=payload)
        assert response.status_code == 200
        assert response.json()["stage"] == stage


def test_generation_job_endpoint_rejects_missing_output_path(tmp_path):
    config_file = tmp_path / "config.json"
    write_config(config_file, "")
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "architecture"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "请先设置项目输出路径"


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
