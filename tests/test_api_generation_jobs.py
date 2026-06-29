import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.server import create_app
from novel_generator.finalization import finalize_chapter


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
                    "prompt_draft_llm": "Default",
                    "final_chapter_llm": "Default",
                    "consistency_review_llm": "Default",
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
                "embedding_configs": {
                    "DefaultEmbedding": {
                        "api_key": "embedding-key",
                        "base_url": "https://example.invalid/embedding",
                        "model_name": "embedding-model",
                        "retrieval_k": 4,
                        "interface_format": "OpenAI",
                    }
                },
                "last_embedding_interface_format": "DefaultEmbedding",
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


def fake_generate_chapter_draft(**kwargs):
    filepath = Path(kwargs["filepath"])
    chapters_path = filepath / "chapters"
    chapters_path.mkdir(parents=True, exist_ok=True)
    (chapters_path / f"chapter_{kwargs['novel_number']}.txt").write_text(
        f"第{kwargs['novel_number']}章草稿正文",
        encoding="utf-8",
    )
    return f"第{kwargs['novel_number']}章草稿正文"


def fake_finalize_chapter(**kwargs):
    filepath = Path(kwargs["filepath"])
    (filepath / "global_summary.txt").write_text(
        f"第{kwargs['novel_number']}章后摘要",
        encoding="utf-8",
    )
    (filepath / "character_state.txt").write_text(
        f"第{kwargs['novel_number']}章后角色状态",
        encoding="utf-8",
    )


def fake_check_consistency(**kwargs):
    assert kwargs["novel_setting"] == "测试小说设定"
    assert kwargs["character_state"] == "角色状态"
    assert kwargs["global_summary"] == "全局摘要"
    assert kwargs["plot_arcs"] == "剧情要点"
    assert kwargs["chapter_text"] == "章节正文"
    assert kwargs["api_key"] == "test-key"
    assert kwargs["model_name"] == "test-model"
    return "无明显冲突"


def test_finalize_chapter_polishes_and_rewrites_chapter_with_context(tmp_path, monkeypatch):
    output_path = tmp_path / "novel"
    chapters_path = output_path / "chapters"
    chapters_path.mkdir(parents=True)
    (chapters_path / "chapter_1.txt").write_text("前章最后一段：门外响起潮声。", encoding="utf-8")
    (chapters_path / "chapter_2.txt").write_text("草稿原文：林澈推门进入码头。", encoding="utf-8")
    (output_path / "Novel_directory.txt").write_text(
        "第2章：码头密谈\n章节简述：林澈在码头见到线人。\n第3章：雾钟\n章节简述：雾钟敲响后危机升级。",
        encoding="utf-8",
    )
    captured_prompts = []

    class FakeAdapter:
        def invoke(self, prompt):
            captured_prompts.append(prompt)
            if "定稿润色" in prompt:
                return "润色后正文：林澈推门进入码头，潮声承接了门外的等待。"
            if "前文摘要" in prompt:
                return "更新后的全局摘要"
            if "角色状态" in prompt:
                return "更新后的角色状态"
            return ""

    monkeypatch.setattr("novel_generator.finalization.create_llm_adapter", lambda **kwargs: FakeAdapter())
    monkeypatch.setattr("novel_generator.finalization.create_embedding_adapter", lambda *args, **kwargs: object())
    monkeypatch.setattr("novel_generator.finalization.update_vector_store", lambda **kwargs: None)

    finalize_chapter(
        novel_number=2,
        word_number=1200,
        api_key="test-key",
        base_url="https://example.invalid/v1",
        model_name="test-model",
        temperature=0.7,
        filepath=str(output_path),
        embedding_api_key="embedding-key",
        embedding_url="https://example.invalid/embedding",
        embedding_interface_format="OpenAI",
        embedding_model_name="embedding-model",
        interface_format="OpenAI",
        max_tokens=4096,
    )

    polished_prompt = captured_prompts[0]
    assert (chapters_path / "chapter_2.txt").read_text(encoding="utf-8") == (
        "润色后正文：林澈推门进入码头，潮声承接了门外的等待。"
    )
    assert "前章最后一段：门外响起潮声。" in polished_prompt
    assert "草稿原文：林澈推门进入码头。" in polished_prompt
    assert "第3章：雾钟" in polished_prompt
    assert (output_path / "global_summary.txt").read_text(encoding="utf-8") == "更新后的全局摘要"
    assert (output_path / "character_state.txt").read_text(encoding="utf-8") == "更新后的角色状态"


def test_generation_job_endpoint_creates_lists_and_reads_job(tmp_path, monkeypatch):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    (output_path / "Novel_setting.txt").write_text("测试小说设定", encoding="utf-8")
    (output_path / "character_state.txt").write_text("角色状态", encoding="utf-8")
    (output_path / "global_summary.txt").write_text("全局摘要", encoding="utf-8")
    (output_path / "plot_arcs.txt").write_text("剧情要点", encoding="utf-8")
    (output_path / "chapter_2.txt").write_text("章节正文", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_generation_config(config_file, output_path)
    monkeypatch.setattr(
        "app.services.generation_executor.check_consistency",
        fake_check_consistency,
    )
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "consistency", "chapterNumber": 2},
    )

    assert response.status_code == 200
    job = response.json()
    assert job["projectId"] == "current"
    assert job["stage"] == "consistency"
    assert job["status"] == "done"
    assert job["progress"] == 100
    assert job["error"] is None
    assert "无明显冲突" in job["log"]

    list_response = client.get("/api/projects/current/jobs")
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [job["id"]]

    read_response = client.get(f"/api/generation-jobs/{job['id']}")
    assert read_response.status_code == 200
    assert read_response.json()["id"] == job["id"]


def test_generation_job_endpoint_persists_consistency_result_across_app_restart(tmp_path, monkeypatch):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    (output_path / "Novel_setting.txt").write_text("测试小说设定", encoding="utf-8")
    (output_path / "chapter_2.txt").write_text("章节正文", encoding="utf-8")
    config_file = tmp_path / "config.json"
    state_db_file = tmp_path / "state.sqlite3"
    write_generation_config(config_file, output_path)
    monkeypatch.setattr(
        "app.services.generation_executor.check_consistency",
        lambda **kwargs: "审校结果：角色动机一致",
    )
    client = TestClient(create_app(config_file=str(config_file), state_db_file=str(state_db_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "consistency", "chapterNumber": 2},
    )

    assert response.status_code == 200
    job = response.json()

    restarted_client = TestClient(create_app(config_file=str(config_file), state_db_file=str(state_db_file)))
    list_response = restarted_client.get("/api/projects/current/jobs")
    read_response = restarted_client.get(f"/api/generation-jobs/{job['id']}")

    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [job["id"]]
    assert read_response.status_code == 200
    assert read_response.json()["status"] == "done"
    assert "审校结果：角色动机一致" in read_response.json()["log"]
    assert read_response.json()["log"] == job["log"]


def test_generation_job_endpoint_persists_done_job_across_app_restart(tmp_path, monkeypatch):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    config_file = tmp_path / "config.json"
    state_db_file = tmp_path / "state.sqlite3"
    write_generation_config(config_file, output_path)
    monkeypatch.setattr(
        "app.services.generation_executor.Novel_architecture_generate",
        fake_architecture_generate,
    )
    client = TestClient(create_app(config_file=str(config_file), state_db_file=str(state_db_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "architecture"},
    )

    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "done"

    restarted_client = TestClient(create_app(config_file=str(config_file), state_db_file=str(state_db_file)))
    read_response = restarted_client.get(f"/api/generation-jobs/{job['id']}")

    assert read_response.status_code == 200
    persisted_job = read_response.json()
    assert persisted_job["status"] == "done"
    assert persisted_job["progress"] == 100
    assert persisted_job["error"] is None
    assert "真实生成执行完成" in persisted_job["log"]


def test_generation_job_endpoint_persists_failed_job_across_app_restart(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    config_file = tmp_path / "config.json"
    state_db_file = tmp_path / "state.sqlite3"
    write_generation_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file), state_db_file=str(state_db_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "draft", "chapterNumber": 1},
    )

    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "failed"

    restarted_client = TestClient(create_app(config_file=str(config_file), state_db_file=str(state_db_file)))
    read_response = restarted_client.get(f"/api/generation-jobs/{job['id']}")

    assert read_response.status_code == 200
    persisted_job = read_response.json()
    assert persisted_job["status"] == "failed"
    assert "请先生成章节目录" in persisted_job["error"]
    assert any("执行失败：请先生成章节目录" in line for line in persisted_job["log"])


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
    monkeypatch.setattr(
        "app.services.generation_executor.generate_chapter_draft",
        fake_generate_chapter_draft,
    )
    monkeypatch.setattr(
        "app.services.generation_executor.finalize_chapter",
        fake_finalize_chapter,
    )
    monkeypatch.setattr(
        "app.services.generation_executor.check_consistency",
        lambda **kwargs: "无明显冲突",
    )
    client = TestClient(create_app(config_file=str(config_file)))

    for stage in ["architecture", "directory", "draft", "finalization", "consistency"]:
        payload = {"projectId": "current", "stage": stage}
        if stage in {"finalization", "consistency"}:
            (output_path / "chapter_2.txt").write_text("章节正文", encoding="utf-8")
            payload["chapterNumber"] = 2
        if stage == "draft":
            (output_path / "Novel_directory.txt").write_text("第2章：雾港来信", encoding="utf-8")
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


def test_draft_generation_job_runs_executor_and_syncs_frontend_chapter(tmp_path, monkeypatch):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    (output_path / "Novel_directory.txt").write_text("第1章：雾港来信", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_generation_config(config_file, output_path)
    monkeypatch.setattr(
        "app.services.generation_executor.generate_chapter_draft",
        fake_generate_chapter_draft,
    )
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "draft", "chapterNumber": 1},
    )

    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "done"
    assert job["progress"] == 100
    assert job["error"] is None
    assert (output_path / "chapters" / "chapter_1.txt").read_text(encoding="utf-8") == "第1章草稿正文"
    assert (output_path / "chapter_1.txt").read_text(encoding="utf-8") == "第1章草稿正文"

    chapters_response = client.get("/api/projects/current/chapters")
    assert chapters_response.status_code == 200
    assert chapters_response.json()[0]["order"] == 1
    assert chapters_response.json()[0]["content"] == "第1章草稿正文"


def test_finalization_generation_job_runs_executor_and_updates_project_files(tmp_path, monkeypatch):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    (output_path / "chapter_2.txt").write_text("编辑后的第2章正文", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_generation_config(config_file, output_path)
    monkeypatch.setattr(
        "app.services.generation_executor.finalize_chapter",
        fake_finalize_chapter,
    )
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "finalization", "chapterNumber": 2},
    )

    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "done"
    assert job["progress"] == 100
    assert job["error"] is None
    assert (output_path / "chapters" / "chapter_2.txt").read_text(encoding="utf-8") == "编辑后的第2章正文"
    assert (output_path / "chapter_2.txt").read_text(encoding="utf-8") == "编辑后的第2章正文"
    assert (output_path / "global_summary.txt").read_text(encoding="utf-8") == "第2章后摘要"
    assert (output_path / "character_state.txt").read_text(encoding="utf-8") == "第2章后角色状态"


def test_consistency_generation_job_runs_executor_with_architecture_fallback(tmp_path, monkeypatch):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    (output_path / "Novel_architecture.txt").write_text("测试小说设定", encoding="utf-8")
    (output_path / "chapter_2.txt").write_text("章节正文", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_generation_config(config_file, output_path)
    monkeypatch.setattr(
        "app.services.generation_executor.check_consistency",
        lambda **kwargs: f"审校读取设定：{kwargs['novel_setting']}",
    )
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "consistency", "chapterNumber": 2},
    )

    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "done"
    assert "审校读取设定：测试小说设定" in job["log"]


def test_consistency_generation_job_does_not_modify_project_files(tmp_path, monkeypatch):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    files = {
        "Novel_setting.txt": "测试小说设定",
        "chapter_2.txt": "章节正文",
        "global_summary.txt": "全局摘要",
        "character_state.txt": "角色状态",
        "plot_arcs.txt": "剧情要点",
    }
    for filename, content in files.items():
        (output_path / filename).write_text(content, encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_generation_config(config_file, output_path)
    monkeypatch.setattr(
        "app.services.generation_executor.check_consistency",
        lambda **kwargs: "无明显冲突",
    )
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "consistency", "chapterNumber": 2},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "done"
    for filename, content in files.items():
        assert (output_path / filename).read_text(encoding="utf-8") == content


def test_draft_generation_job_fails_when_directory_missing(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    config_file = tmp_path / "config.json"
    write_generation_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "draft", "chapterNumber": 1},
    )

    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "failed"
    assert "请先生成章节目录" in job["error"]


def test_draft_generation_job_fails_when_api_key_missing(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    (output_path / "Novel_directory.txt").write_text("第1章：雾港来信", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_generation_config(config_file, output_path, api_key="")
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "draft", "chapterNumber": 1},
    )

    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "failed"
    assert "缺少 API Key" in job["error"]


def test_finalization_generation_job_fails_when_chapter_missing(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    config_file = tmp_path / "config.json"
    write_generation_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "finalization", "chapterNumber": 3},
    )

    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "failed"
    assert "请先生成或保存章节正文" in job["error"]


def test_consistency_generation_job_fails_when_setting_missing(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    (output_path / "chapter_2.txt").write_text("章节正文", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_generation_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "consistency", "chapterNumber": 2},
    )

    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "failed"
    assert "请先准备小说设定" in job["error"]


def test_consistency_generation_job_fails_when_chapter_empty(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    (output_path / "Novel_setting.txt").write_text("测试小说设定", encoding="utf-8")
    (output_path / "chapter_2.txt").write_text("  ", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_generation_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "consistency", "chapterNumber": 2},
    )

    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "failed"
    assert "请先生成或保存章节正文" in job["error"]


def test_consistency_generation_job_fails_when_review_llm_not_selected(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    (output_path / "Novel_setting.txt").write_text("测试小说设定", encoding="utf-8")
    (output_path / "chapter_2.txt").write_text("章节正文", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_generation_config(config_file, output_path)
    config = json.loads(config_file.read_text(encoding="utf-8"))
    config["choose_configs"]["consistency_review_llm"] = ""
    config_file.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "consistency", "chapterNumber": 2},
    )

    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "failed"
    assert "一致性审校未选择 LLM 配置" in job["error"]


def test_consistency_generation_job_fails_when_api_key_missing(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    (output_path / "Novel_setting.txt").write_text("测试小说设定", encoding="utf-8")
    (output_path / "chapter_2.txt").write_text("章节正文", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_generation_config(config_file, output_path, api_key="")
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post(
        "/api/generation-jobs",
        json={"projectId": "current", "stage": "consistency", "chapterNumber": 2},
    )

    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "failed"
    assert "缺少 API Key" in job["error"]


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
        json={"projectId": "current", "stage": "consistency", "chapterNumber": 99},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "章节文件不存在"
