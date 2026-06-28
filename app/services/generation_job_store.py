from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


class GenerationJobStore:
    def __init__(self, db_file: str | Path):
        self.db_file = Path(db_file)
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def save_job(self, job: dict[str, Any], request: dict[str, Any]) -> None:
        updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO generation_jobs (
                    id,
                    project_id,
                    title,
                    stage,
                    status,
                    progress,
                    started_at,
                    log_json,
                    error,
                    request_json,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    project_id = excluded.project_id,
                    title = excluded.title,
                    stage = excluded.stage,
                    status = excluded.status,
                    progress = excluded.progress,
                    started_at = excluded.started_at,
                    log_json = excluded.log_json,
                    error = excluded.error,
                    request_json = excluded.request_json,
                    updated_at = excluded.updated_at
                """,
                (
                    job["id"],
                    job["projectId"],
                    job["title"],
                    job["stage"],
                    job["status"],
                    int(job["progress"]),
                    job["startedAt"],
                    json.dumps(job.get("log") or [], ensure_ascii=False),
                    job.get("error"),
                    json.dumps(request, ensure_ascii=False),
                    updated_at,
                ),
            )

    def list_jobs(self, project_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM generation_jobs
                WHERE project_id = ?
                ORDER BY updated_at DESC, started_at DESC, id DESC
                """,
                (project_id,),
            ).fetchall()
        return [self._row_to_job(row) for row in rows]

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM generation_jobs WHERE id = ?",
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_job(row)

    def _init_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS generation_jobs (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress INTEGER NOT NULL,
                    started_at TEXT NOT NULL,
                    log_json TEXT NOT NULL,
                    error TEXT,
                    request_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_generation_jobs_project_updated
                ON generation_jobs(project_id, updated_at)
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_file)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _row_to_job(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "projectId": row["project_id"],
            "title": row["title"],
            "stage": row["stage"],
            "status": row["status"],
            "progress": row["progress"],
            "startedAt": row["started_at"],
            "log": json.loads(row["log_json"]),
            "error": row["error"],
        }
