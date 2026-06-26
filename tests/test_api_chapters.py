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
