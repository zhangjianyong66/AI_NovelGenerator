import json

from fastapi.testclient import TestClient

from app.api.server import create_app


def write_config(config_file, output_path):
    config_file.write_text(
        json.dumps({"other_params": {"filepath": str(output_path)}}, ensure_ascii=False),
        encoding="utf-8",
    )


def test_chapters_endpoint_lists_chapter_files_in_number_order(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    (output_path / "chapter_10.txt").write_text("第十章正文", encoding="utf-8")
    (output_path / "chapter_2.txt").write_text("第二章正文", encoding="utf-8")
    (output_path / "Novel_directory.txt").write_text(
        "第2章 - [失落档案]\n本章简述：[主角找到关键档案]\n第10章 - [终局钟声]\n本章简述：[真相揭晓]",
        encoding="utf-8",
    )
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.get("/api/projects/current/chapters")

    assert response.status_code == 200
    chapters = response.json()
    assert [chapter["order"] for chapter in chapters] == [2, 10]
    assert chapters[0]["id"] == "chapter-2"
    assert chapters[0]["title"] == "失落档案"
    assert chapters[0]["synopsis"] == "主角找到关键档案"
    assert chapters[0]["content"] == "第二章正文"
    assert chapters[0]["words"] == 5


def test_chapters_endpoint_includes_planned_chapters_from_directory_and_config(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    (output_path / "chapter_1.txt").write_text("第一章正文", encoding="utf-8")
    (output_path / "Novel_directory.txt").write_text(
        "第1章 - [雾港来信]\n本章简述：[主角收到线索]\n第2章 - [失落档案]\n本章简述：[主角找到关键档案]",
        encoding="utf-8",
    )
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "other_params": {
                    "filepath": str(output_path),
                    "num_chapters": 3,
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.get("/api/projects/current/chapters")

    assert response.status_code == 200
    chapters = response.json()
    assert [chapter["order"] for chapter in chapters] == [1, 2, 3]
    assert chapters[0]["status"] == "draft"
    assert chapters[0]["content"] == "第一章正文"
    assert chapters[1]["status"] == "planned"
    assert chapters[1]["title"] == "失落档案"
    assert chapters[1]["synopsis"] == "主角找到关键档案"
    assert chapters[1]["content"] == ""
    assert chapters[1]["words"] == 0
    assert chapters[2]["status"] == "planned"
    assert chapters[2]["title"] == "第3章"


def test_chapter_endpoint_creates_missing_chapter_file(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    (output_path / "Novel_directory.txt").write_text(
        "第2章 - [失落档案]\n本章简述：[主角找到关键档案]",
        encoding="utf-8",
    )
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post("/api/chapters/2")

    assert response.status_code == 200
    chapter = response.json()
    assert chapter["order"] == 2
    assert chapter["status"] == "draft"
    assert chapter["title"] == "失落档案"
    assert chapter["content"] == ""
    assert (output_path / "chapter_2.txt").exists()


def test_chapter_endpoint_rejects_creating_existing_chapter_file(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    (output_path / "chapter_2.txt").write_text("已有正文", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.post("/api/chapters/2")

    assert response.status_code == 409
    assert (output_path / "chapter_2.txt").read_text(encoding="utf-8") == "已有正文"


def test_chapter_endpoint_saves_existing_chapter_content(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    (output_path / "chapter_2.txt").write_text("旧正文", encoding="utf-8")
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.put("/api/chapters/2", json={"content": "新正文\n第二行"})

    assert response.status_code == 200
    assert response.json()["content"] == "新正文\n第二行"
    assert response.json()["words"] == 6
    assert (output_path / "chapter_2.txt").read_text(encoding="utf-8") == "新正文\n第二行"


def test_chapter_endpoint_saves_newly_created_chapter_content(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    create_response = client.post("/api/chapters/3")
    save_response = client.put("/api/chapters/3", json={"content": "第三章正文"})

    assert create_response.status_code == 200
    assert save_response.status_code == 200
    assert save_response.json()["content"] == "第三章正文"
    assert (output_path / "chapter_3.txt").read_text(encoding="utf-8") == "第三章正文"


def test_chapter_endpoint_rejects_missing_chapter_file(tmp_path):
    output_path = tmp_path / "novel"
    output_path.mkdir()
    config_file = tmp_path / "config.json"
    write_config(config_file, output_path)
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.put("/api/chapters/9", json={"content": "不会创建缺失章节"})

    assert response.status_code == 404


def test_chapters_endpoint_uses_default_output_path_when_missing(tmp_path):
    config_file = tmp_path / "config.json"
    write_config(config_file, "")
    client = TestClient(create_app(config_file=str(config_file)))

    response = client.get("/api/projects/current/chapters")

    assert response.status_code == 200
    assert response.json() == []
    assert (tmp_path / "output").is_dir()
