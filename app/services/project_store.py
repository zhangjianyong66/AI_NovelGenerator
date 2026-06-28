from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


class ProjectStore:
    def __init__(self, db_file: str | Path):
        self.db_file = Path(db_file)
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @staticmethod
    def project_id_for_path(output_path: str | Path) -> str:
        normalized = str(Path(output_path).expanduser().resolve())
        digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:12]
        return f"project-{digest}"

    def upsert_project(
        self,
        output_path: str | Path,
        title: str,
        genre: str,
        params: dict[str, Any] | None = None,
    ) -> str:
        normalized_path = str(Path(output_path).expanduser().resolve())
        project_id = self.project_id_for_path(normalized_path)
        updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        params_json = json.dumps(params or {}, ensure_ascii=False)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO recent_projects (
                    id,
                    output_path,
                    title,
                    genre,
                    params_json,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(output_path) DO UPDATE SET
                    title = excluded.title,
                    genre = excluded.genre,
                    params_json = excluded.params_json,
                    updated_at = excluded.updated_at
                """,
                (project_id, normalized_path, title, genre, params_json, updated_at),
            )
        return project_id

    def get_project(self, project_id: str) -> dict[str, str] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, output_path, title, genre, params_json, updated_at
                FROM recent_projects
                WHERE id = ?
                """,
                (project_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_project(row)

    def list_projects(self) -> list[dict[str, str]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, output_path, title, genre, params_json, updated_at
                FROM recent_projects
                ORDER BY updated_at DESC, id DESC
                """
            ).fetchall()
        return [self._row_to_project(row) for row in rows]

    def _init_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS recent_projects (
                    id TEXT PRIMARY KEY,
                    output_path TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    genre TEXT NOT NULL,
                    params_json TEXT NOT NULL DEFAULT '{}',
                    updated_at TEXT NOT NULL
                )
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(recent_projects)").fetchall()
            }
            if "params_json" not in columns:
                connection.execute("ALTER TABLE recent_projects ADD COLUMN params_json TEXT NOT NULL DEFAULT '{}'")
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_recent_projects_updated
                ON recent_projects(updated_at)
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_file)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _row_to_project(row: sqlite3.Row) -> dict[str, str]:
        return {
            "id": row["id"],
            "output_path": row["output_path"],
            "title": row["title"],
            "genre": row["genre"],
            "params": ProjectStore._decode_params(row["params_json"]),
            "updated_at": row["updated_at"],
        }

    @staticmethod
    def _decode_params(params_json: str) -> dict[str, Any]:
        try:
            params = json.loads(params_json or "{}")
        except json.JSONDecodeError:
            return {}
        return params if isinstance(params, dict) else {}
