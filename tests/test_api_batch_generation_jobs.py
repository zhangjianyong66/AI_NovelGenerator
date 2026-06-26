import json

from fastapi.testclient import TestClient

from app.api.server import create_app


def write_config(config_file, output_path):
    config_file.write_text(
        json.dumps({"other_params": {"filepath": str(output_path)}}, ensure_ascii=False),
        encoding="utf-8",
    )


def test_batch_generation_job_endpoint_creates_batch_job(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    for chapter_number in range(1, 4):
        (output_path / f"chapter_{chapter_number}.txt").write_text("旧正文", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={
            "projectId": "current",
            "stage": "batch",
            "startChapter": 1,
            "endChapter": 3,
            "targetWords": 4200,
            "minimumWords": 3000,
            "autoEnrich": True,
        },
    )

    assert response.status_code == 200
    job = response.json()
    assert job["stage"] == "batch"
    assert job["title"] == "批量生成草稿"
    assert "章节范围：1-3" in job["log"]
    assert "目标字数：4200，最低字数：3000，自动扩写：是" in job["log"]


def test_batch_generation_job_rejects_invalid_range(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={
            "projectId": "current",
            "stage": "batch",
            "startChapter": 5,
            "endChapter": 3,
            "targetWords": 4200,
            "minimumWords": 3000,
            "autoEnrich": False,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "批量生成章节范围无效"


def test_batch_generation_job_rejects_missing_chapter_in_range(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    (output_path / "chapter_1.txt").write_text("正文", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={
            "projectId": "current",
            "stage": "batch",
            "startChapter": 1,
            "endChapter": 2,
            "targetWords": 4200,
            "minimumWords": 3000,
            "autoEnrich": False,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "章节文件不存在：2"
