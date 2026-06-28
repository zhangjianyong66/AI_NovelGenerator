import json

from fastapi.testclient import TestClient

from app.api.server import create_app


def write_config(config_file, output_path, **other_params):
    params = {
        "filepath": str(output_path),
        "topic": "雾城余烬",
        "genre": "悬疑",
        "num_chapters": 4,
        "word_number": 3000,
        "chapter_num": "1",
        **other_params,
    }
    config_file.write_text(
        json.dumps(
            {
                "llm_configs": {"Default": {"model_name": "test-model"}},
                "other_params": params,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_create_project_creates_output_path_updates_config_and_persists_recent_project(tmp_path):
    config_file = tmp_path / "config.json"
    state_db_file = tmp_path / "state.sqlite3"
    current_output = tmp_path / "current"
    current_output.mkdir()
    write_config(config_file, current_output)
    client = TestClient(create_app(config_file=str(config_file), state_db_file=str(state_db_file)))

    new_output = tmp_path / "new-project"
    response = client.post(
        "/api/projects",
        json={
            "outputPath": str(new_output),
            "topic": "群星回声",
            "genre": "太空歌剧",
            "numChapters": 12,
            "wordNumber": 2500,
        },
    )

    assert response.status_code == 200
    assert new_output.is_dir()
    assert response.json()["title"] == "群星回声"
    assert response.json()["status"] == "active"

    saved = json.loads(config_file.read_text(encoding="utf-8"))
    assert saved["other_params"]["filepath"] == str(new_output)
    assert saved["other_params"]["topic"] == "群星回声"
    assert saved["other_params"]["genre"] == "太空歌剧"
    assert saved["other_params"]["num_chapters"] == 12
    assert saved["other_params"]["word_number"] == 2500
    assert "llm_configs" in saved

    restarted_client = TestClient(
        create_app(config_file=str(config_file), state_db_file=str(state_db_file))
    )
    list_response = restarted_client.get("/api/projects")
    assert list_response.status_code == 200
    assert list_response.json()[0]["summary"] == str(new_output)
    assert list_response.json()[0]["status"] == "active"


def test_switch_project_by_existing_output_path_updates_config_without_overwriting_files(tmp_path):
    config_file = tmp_path / "config.json"
    state_db_file = tmp_path / "state.sqlite3"
    current_output = tmp_path / "current"
    target_output = tmp_path / "existing"
    current_output.mkdir()
    target_output.mkdir()
    (target_output / "Novel_setting.txt").write_text("已有设定", encoding="utf-8")
    (target_output / "chapter_1.txt").write_text("已有正文", encoding="utf-8")
    write_config(config_file, current_output)
    client = TestClient(create_app(config_file=str(config_file), state_db_file=str(state_db_file)))

    response = client.post("/api/projects/switch", json={"outputPath": str(target_output)})

    assert response.status_code == 200
    assert response.json()["summary"] == str(target_output)
    assert (target_output / "Novel_setting.txt").read_text(encoding="utf-8") == "已有设定"
    assert (target_output / "chapter_1.txt").read_text(encoding="utf-8") == "已有正文"

    saved = json.loads(config_file.read_text(encoding="utf-8"))
    assert saved["other_params"]["filepath"] == str(target_output)

    restarted_client = TestClient(
        create_app(config_file=str(config_file), state_db_file=str(state_db_file))
    )
    list_response = restarted_client.get("/api/projects")
    assert list_response.status_code == 200
    assert list_response.json()[0]["summary"] == str(target_output)
    assert list_response.json()[0]["chaptersCompleted"] == 1


def test_switch_new_existing_output_path_does_not_inherit_previous_project_params(tmp_path):
    config_file = tmp_path / "config.json"
    state_db_file = tmp_path / "state.sqlite3"
    current_output = tmp_path / "current"
    target_output = tmp_path / "existing"
    current_output.mkdir()
    target_output.mkdir()
    write_config(
        config_file,
        current_output,
        topic="旧项目",
        genre="旧类型",
        num_chapters=8,
        word_number=2200,
        chapter_num="4",
        user_guidance="旧指导",
        characters_involved="旧角色",
        key_items="旧物品",
        scene_location="旧场景",
        time_constraint="旧时间",
    )
    client = TestClient(create_app(config_file=str(config_file), state_db_file=str(state_db_file)))

    response = client.post("/api/projects/switch", json={"outputPath": str(target_output)})
    config_response = client.get("/api/project-config")

    assert response.status_code == 200
    assert config_response.status_code == 200
    switched_config = config_response.json()
    assert switched_config["outputPath"] == str(target_output)
    assert switched_config["novelParams"]["topic"] == ""
    assert switched_config["novelParams"]["genre"] == ""
    assert switched_config["novelParams"]["numChapters"] == 0
    assert switched_config["novelParams"]["wordNumber"] == 0
    assert switched_config["novelParams"]["chapterNum"] == ""
    assert switched_config["novelParams"]["userGuidance"] == ""
    assert switched_config["novelParams"]["charactersInvolved"] == ""
    assert switched_config["novelParams"]["keyItems"] == ""
    assert switched_config["novelParams"]["sceneLocation"] == ""
    assert switched_config["novelParams"]["timeConstraint"] == ""


def test_switch_project_by_recent_project_id_updates_config(tmp_path):
    config_file = tmp_path / "config.json"
    state_db_file = tmp_path / "state.sqlite3"
    current_output = tmp_path / "current"
    first_output = tmp_path / "first"
    second_output = tmp_path / "second"
    current_output.mkdir()
    first_output.mkdir()
    second_output.mkdir()
    write_config(config_file, current_output)
    client = TestClient(create_app(config_file=str(config_file), state_db_file=str(state_db_file)))

    first_response = client.post("/api/projects/switch", json={"outputPath": str(first_output)})
    second_response = client.post("/api/projects/switch", json={"outputPath": str(second_output)})
    assert first_response.status_code == 200
    assert second_response.status_code == 200
    projects_response = client.get("/api/projects")
    assert projects_response.status_code == 200
    first_project_id = next(
        project["id"] for project in projects_response.json() if project["summary"] == str(first_output)
    )

    response = client.post("/api/projects/switch", json={"projectId": first_project_id})

    assert response.status_code == 200
    assert response.json()["summary"] == str(first_output)
    saved = json.loads(config_file.read_text(encoding="utf-8"))
    assert saved["other_params"]["filepath"] == str(first_output)


def test_project_switch_preserves_project_params_per_project_but_keeps_model_settings_global(tmp_path):
    config_file = tmp_path / "config.json"
    state_db_file = tmp_path / "state.sqlite3"
    first_output = tmp_path / "first"
    second_output = tmp_path / "second"
    first_output.mkdir()
    second_output.mkdir()
    write_config(config_file, first_output, topic="项目A", genre="奇幻", num_chapters=6, chapter_num="2")
    client = TestClient(create_app(config_file=str(config_file), state_db_file=str(state_db_file)))

    first_save = client.put(
        "/api/project-config",
        json={
            "outputPath": str(first_output),
            "novelParams": {
                "topic": "项目A",
                "genre": "奇幻",
                "numChapters": 6,
                "wordNumber": 1800,
                "chapterNum": "2",
                "userGuidance": "A 指导",
                "charactersInvolved": "A 角色",
                "keyItems": "A 物品",
                "sceneLocation": "A 场景",
                "timeConstraint": "A 时间",
            },
        },
    )
    assert first_save.status_code == 200

    switch_to_second = client.post("/api/projects/switch", json={"outputPath": str(second_output)})
    assert switch_to_second.status_code == 200
    second_save = client.put(
        "/api/project-config",
        json={
            "outputPath": str(second_output),
            "novelParams": {
                "topic": "项目B",
                "genre": "科幻",
                "numChapters": 9,
                "wordNumber": 2600,
                "chapterNum": "5",
                "userGuidance": "B 指导",
                "charactersInvolved": "B 角色",
                "keyItems": "B 物品",
                "sceneLocation": "B 场景",
                "timeConstraint": "B 时间",
            },
        },
    )
    assert second_save.status_code == 200

    projects_response = client.get("/api/projects")
    assert projects_response.status_code == 200
    first_project_id = next(
        project["id"] for project in projects_response.json() if project["summary"] == str(first_output)
    )
    switch_back = client.post("/api/projects/switch", json={"projectId": first_project_id})
    config_response = client.get("/api/project-config")

    assert switch_back.status_code == 200
    assert config_response.status_code == 200
    restored = config_response.json()
    assert restored["outputPath"] == str(first_output)
    assert restored["novelParams"]["topic"] == "项目A"
    assert restored["novelParams"]["genre"] == "奇幻"
    assert restored["novelParams"]["numChapters"] == 6
    assert restored["novelParams"]["wordNumber"] == 1800
    assert restored["novelParams"]["chapterNum"] == "2"
    assert restored["novelParams"]["userGuidance"] == "A 指导"
    assert restored["novelParams"]["charactersInvolved"] == "A 角色"
    assert restored["novelParams"]["keyItems"] == "A 物品"
    assert restored["novelParams"]["sceneLocation"] == "A 场景"
    assert restored["novelParams"]["timeConstraint"] == "A 时间"

    saved = json.loads(config_file.read_text(encoding="utf-8"))
    assert saved["llm_configs"] == {"Default": {"model_name": "test-model"}}


def test_project_switch_rejects_invalid_path_and_unknown_id(tmp_path):
    config_file = tmp_path / "config.json"
    state_db_file = tmp_path / "state.sqlite3"
    current_output = tmp_path / "current"
    current_output.mkdir()
    write_config(config_file, current_output)
    client = TestClient(create_app(config_file=str(config_file), state_db_file=str(state_db_file)))

    path_response = client.post("/api/projects/switch", json={"outputPath": str(tmp_path / "missing")})
    id_response = client.post("/api/projects/switch", json={"projectId": "missing"})

    assert path_response.status_code == 400
    assert path_response.json()["detail"] == "项目输出路径不存在"
    assert id_response.status_code == 404
    assert id_response.json()["detail"] == "项目不存在"
