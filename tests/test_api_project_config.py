import json

from fastapi.testclient import TestClient

from app.api.server import create_app


def write_default_config(config_file):
    config_file.write_text(
        json.dumps(
            {
                "llm_configs": {"Default": {"model_name": "test-model"}},
                "other_params": {
                    "topic": "",
                    "genre": "",
                    "num_chapters": 0,
                    "word_number": 0,
                    "filepath": "",
                    "chapter_num": "1",
                    "user_guidance": "",
                    "characters_involved": "",
                    "key_items": "",
                    "scene_location": "",
                    "time_constraint": "",
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_project_config_endpoint_loads_existing_output_path_and_novel_params(tmp_path):
    config_file = tmp_path / "config.json"
    write_default_config(config_file)
    config = json.loads(config_file.read_text(encoding="utf-8"))
    config["other_params"].update(
        {
            "filepath": str(tmp_path / "novel-output"),
            "topic": "海底城旧案",
            "genre": "科幻悬疑",
            "num_chapters": 24,
            "word_number": 3200,
            "chapter_num": "7",
            "user_guidance": "保持冷峻叙事",
            "characters_involved": "林澈,沈闻",
            "key_items": "蓝色芯片",
            "scene_location": "海底中央站",
            "time_constraint": "三小时内",
        }
    )
    config_file.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")

    client = TestClient(create_app(config_file=str(config_file)))

    response = client.get("/api/project-config")

    assert response.status_code == 200
    assert response.json() == {
        "outputPath": str(tmp_path / "novel-output"),
        "novelParams": {
            "topic": "海底城旧案",
            "genre": "科幻悬疑",
            "numChapters": 24,
            "wordNumber": 3200,
            "chapterNum": "7",
            "userGuidance": "保持冷峻叙事",
            "charactersInvolved": "林澈,沈闻",
            "keyItems": "蓝色芯片",
            "sceneLocation": "海底中央站",
            "timeConstraint": "三小时内",
        },
    }


def test_project_config_endpoint_saves_path_and_novel_params_in_legacy_config(tmp_path):
    config_file = tmp_path / "config.json"
    write_default_config(config_file)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.put(
        "/api/project-config",
        json={
            "outputPath": str(tmp_path / "saved-output"),
            "novelParams": {
                "topic": "群星回声",
                "genre": "太空歌剧",
                "numChapters": 36,
                "wordNumber": 4500,
                "chapterNum": "12",
                "userGuidance": "增强群像冲突",
                "charactersInvolved": "乔安,米拉",
                "keyItems": "星图",
                "sceneLocation": "边境舰桥",
                "timeConstraint": "跃迁前",
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["outputPath"] == str(tmp_path / "saved-output")

    saved = json.loads(config_file.read_text(encoding="utf-8"))
    assert saved["other_params"]["filepath"] == str(tmp_path / "saved-output")
    assert saved["other_params"]["topic"] == "群星回声"
    assert saved["other_params"]["genre"] == "太空歌剧"
    assert saved["other_params"]["num_chapters"] == 36
    assert saved["other_params"]["word_number"] == 4500
    assert saved["other_params"]["chapter_num"] == "12"
    assert "llm_configs" in saved


def test_project_config_rejects_negative_counts(tmp_path):
    config_file = tmp_path / "config.json"
    write_default_config(config_file)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.put(
        "/api/project-config",
        json={
            "outputPath": "",
            "novelParams": {
                "topic": "",
                "genre": "",
                "numChapters": -1,
                "wordNumber": 3000,
                "chapterNum": "1",
                "userGuidance": "",
                "charactersInvolved": "",
                "keyItems": "",
                "sceneLocation": "",
                "timeConstraint": "",
            },
        },
    )

    assert response.status_code == 422
