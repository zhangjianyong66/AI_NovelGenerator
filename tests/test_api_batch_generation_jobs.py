import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.server import create_app


def write_config(config_file, output_path):
    config_file.write_text(
        json.dumps({"other_params": {"filepath": str(output_path)}}, ensure_ascii=False),
        encoding="utf-8",
    )


def write_generation_config(config_file, output_path):
    config_file.write_text(
        json.dumps(
            {
                "other_params": {
                    "filepath": str(output_path),
                    "topic": "记忆交易港城",
                    "genre": "悬疑奇幻",
                    "num_chapters": 3,
                    "word_number": 1200,
                    "chapter_num": "1",
                },
                "choose_configs": {
                    "prompt_draft_llm": "Default",
                    "final_chapter_llm": "Default",
                    "consistency_review_llm": "Default",
                },
                "llm_configs": {
                    "Default": {
                        "api_key": "test-key",
                        "base_url": "https://example.invalid/v1",
                        "model_name": "test-model",
                        "temperature": 0.7,
                        "max_tokens": 4096,
                        "timeout": 600,
                        "interface_format": "OpenAI",
                    }
                },
                "embedding_configs": {},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def fake_finalize_chapter(**kwargs):
    filepath = Path(kwargs["filepath"])
    novel_number = kwargs["novel_number"]
    legacy_path = filepath / "chapters" / f"chapter_{novel_number}.txt"
    legacy_path.write_text(f"第{novel_number}章定稿正文", encoding="utf-8")
    (filepath / "global_summary.txt").write_text(f"第{novel_number}章后摘要", encoding="utf-8")
    (filepath / "character_state.txt").write_text(f"第{novel_number}章后角色状态", encoding="utf-8")


def fake_generate_chapter_draft(**kwargs):
    filepath = Path(kwargs["filepath"])
    novel_number = kwargs["novel_number"]
    legacy_dir = filepath / "chapters"
    legacy_dir.mkdir(parents=True, exist_ok=True)
    (legacy_dir / f"chapter_{novel_number}.txt").write_text(f"第{novel_number}章草稿正文", encoding="utf-8")


def test_batch_generation_job_runs_real_finalization_for_each_chapter(tmp_path, monkeypatch):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    for chapter_number in range(1, 4):
        (output_path / f"chapter_{chapter_number}.txt").write_text(f"第{chapter_number}章旧正文", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_generation_config(config_file, output_path)
    calls = []

    def track_finalize_chapter(**kwargs):
        calls.append(kwargs["novel_number"])
        fake_finalize_chapter(**kwargs)

    monkeypatch.setattr("app.services.generation_executor.finalize_chapter", track_finalize_chapter)
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
            "autoEnrich": False,
        },
    )

    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "done"
    assert job["progress"] == 100
    assert job["error"] is None
    assert calls == [1, 2, 3]
    assert "批量定稿完成：成功 3 章，失败 0 章" in job["log"]
    for chapter_number in range(1, 4):
        assert (output_path / f"chapter_{chapter_number}.txt").read_text(encoding="utf-8") == f"第{chapter_number}章定稿正文"


def test_batch_draft_generation_job_creates_missing_chapters_and_skips_existing(tmp_path, monkeypatch):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    (output_path / "Novel_directory.txt").write_text("第1章：雾港来信\n第2章：暗巷回声\n第3章：钟楼密语", encoding="utf-8")
    (output_path / "chapter_1.txt").write_text("第1章已有正文", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_generation_config(config_file, output_path)
    calls = []

    def track_generate_chapter_draft(**kwargs):
        calls.append(kwargs["novel_number"])
        fake_generate_chapter_draft(**kwargs)

    monkeypatch.setattr("app.services.generation_executor.generate_chapter_draft", track_generate_chapter_draft)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={
            "projectId": "current",
            "stage": "batchDraft",
            "startChapter": 1,
            "endChapter": 3,
            "targetWords": 4200,
            "minimumWords": 3000,
            "autoEnrich": False,
        },
    )

    assert response.status_code == 200
    job = response.json()
    assert job["stage"] == "batchDraft"
    assert job["title"] == "批量生成草稿"
    assert job["status"] == "done"
    assert job["error"] is None
    assert calls == [2, 3]
    assert (output_path / "chapter_1.txt").read_text(encoding="utf-8") == "第1章已有正文"
    assert (output_path / "chapter_2.txt").read_text(encoding="utf-8") == "第2章草稿正文"
    assert (output_path / "chapter_3.txt").read_text(encoding="utf-8") == "第3章草稿正文"
    assert "第 1 章已有正文，跳过草稿生成" in job["log"]
    assert "批量草稿完成：成功 2 章，跳过 1 章，失败 0 章" in job["log"]


def test_batch_draft_generation_job_continues_after_chapter_failure(tmp_path, monkeypatch):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    (output_path / "Novel_directory.txt").write_text("章节目录", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_generation_config(config_file, output_path)
    calls = []

    def partly_failing_generate_chapter_draft(**kwargs):
        calls.append(kwargs["novel_number"])
        if kwargs["novel_number"] == 2:
            raise RuntimeError("模拟第2章失败")
        fake_generate_chapter_draft(**kwargs)

    monkeypatch.setattr("app.services.generation_executor.generate_chapter_draft", partly_failing_generate_chapter_draft)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "batchDraft", "startChapter": 1, "endChapter": 3},
    )

    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "failed"
    assert calls == [1, 2, 3]
    assert "批量草稿部分失败：成功章节 1、3；失败章节 2" in job["error"]
    assert "第 2 章草稿失败：生成执行失败：模拟第2章失败" in job["log"]
    assert (output_path / "chapter_1.txt").read_text(encoding="utf-8") == "第1章草稿正文"
    assert not (output_path / "chapter_2.txt").exists()
    assert (output_path / "chapter_3.txt").read_text(encoding="utf-8") == "第3章草稿正文"


def test_batch_finalization_generation_job_accepts_explicit_stage(tmp_path, monkeypatch):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    for chapter_number in range(1, 3):
        (output_path / f"chapter_{chapter_number}.txt").write_text(f"第{chapter_number}章旧正文", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_generation_config(config_file, output_path)
    calls = []

    def track_finalize_chapter(**kwargs):
        calls.append(kwargs["novel_number"])
        fake_finalize_chapter(**kwargs)

    monkeypatch.setattr("app.services.generation_executor.finalize_chapter", track_finalize_chapter)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "batchFinalization", "startChapter": 1, "endChapter": 2},
    )

    assert response.status_code == 200
    job = response.json()
    assert job["stage"] == "batchFinalization"
    assert job["title"] == "批量定稿章节"
    assert job["status"] == "done"
    assert calls == [1, 2]
    assert "批量定稿完成：成功 2 章，失败 0 章" in job["log"]


def test_batch_consistency_generation_job_reviews_each_chapter_without_modifying_files(tmp_path, monkeypatch):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    files = {
        "Novel_setting.txt": "测试小说设定",
        "chapter_1.txt": "第1章正文",
        "chapter_2.txt": "第2章正文",
        "global_summary.txt": "全局摘要",
        "character_state.txt": "角色状态",
        "plot_arcs.txt": "剧情要点",
    }
    for filename, content in files.items():
        (output_path / filename).write_text(content, encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_generation_config(config_file, output_path)
    reviewed_chapters = []

    def track_check_consistency(**kwargs):
        reviewed_chapters.append(kwargs["chapter_text"])
        return f"审校结果：{kwargs['chapter_text']}"

    monkeypatch.setattr("app.services.generation_executor.check_consistency", track_check_consistency)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "batchConsistency", "startChapter": 1, "endChapter": 2},
    )

    assert response.status_code == 200
    job = response.json()
    assert job["stage"] == "batchConsistency"
    assert job["title"] == "批量一致性审校"
    assert job["status"] == "done"
    assert reviewed_chapters == ["第1章正文", "第2章正文"]
    assert "审校结果：第1章正文" in job["log"]
    assert "审校结果：第2章正文" in job["log"]
    assert "批量审校完成：成功 2 章，失败 0 章" in job["log"]
    for filename, content in files.items():
        assert (output_path / filename).read_text(encoding="utf-8") == content


def test_batch_generation_job_continues_after_chapter_failure_and_summarizes(tmp_path, monkeypatch):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    for chapter_number in range(1, 4):
        (output_path / f"chapter_{chapter_number}.txt").write_text(f"第{chapter_number}章旧正文", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_generation_config(config_file, output_path)
    calls = []

    def partly_failing_finalize_chapter(**kwargs):
        calls.append(kwargs["novel_number"])
        if kwargs["novel_number"] == 2:
            raise RuntimeError("模拟第2章失败")
        fake_finalize_chapter(**kwargs)

    monkeypatch.setattr("app.services.generation_executor.finalize_chapter", partly_failing_finalize_chapter)
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
            "autoEnrich": False,
        },
    )

    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "failed"
    assert job["progress"] == 100
    assert calls == [1, 2, 3]
    assert "批量定稿部分失败：成功章节 1、3；失败章节 2" in job["error"]
    assert "第 2 章定稿失败：生成执行失败：模拟第2章失败" in job["log"]
    assert "批量定稿完成：成功 2 章，失败 1 章" in job["log"]
    assert (output_path / "chapter_1.txt").read_text(encoding="utf-8") == "第1章定稿正文"
    assert (output_path / "chapter_2.txt").read_text(encoding="utf-8") == "第2章旧正文"
    assert (output_path / "chapter_3.txt").read_text(encoding="utf-8") == "第3章定稿正文"


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
    assert job["title"] == "批量定稿章节"
    assert job["status"] == "failed"
    assert job["error"] == "批量定稿部分失败：成功章节 无；失败章节 1、2、3"
    assert "章节范围：1-3" in job["log"]
    assert "目标字数：4200，最低字数：3000，自动扩写：是" in job["log"]
    assert "第 1 章定稿失败：润色章节定稿未选择 LLM 配置" in job["log"]


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


def test_batch_consistency_generation_job_rejects_missing_chapter_in_range(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    (output_path / "chapter_1.txt").write_text("正文", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "batchConsistency", "startChapter": 1, "endChapter": 2},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "章节文件不存在：2"
