"""Repository for Source persistence."""

from __future__ import annotations

import sqlite3

from core.models.source import Source


class SourceRepository:
    """Handles all database access for sources/references."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create(self, source: Source) -> Source:
        cursor = self._connection.execute(
            """
            INSERT INTO sources
                (research_id, title, url, author, publication_date, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                source.research_id,
                source.title,
                source.url,
                source.author,
                source.publication_date,
                source.notes,
                source.created_at,
                source.updated_at,
            ),
        )
        self._connection.commit()
        source.id = cursor.lastrowid
        return source

    def get_by_id(self, source_id: int) -> Source | None:
        row = self._connection.execute(
            "SELECT * FROM sources WHERE id = ?;", (source_id,)
        ).fetchone()
        return self._row_to_model(row) if row else None

    def list_by_research(self, research_id: int) -> list[Source]:
        rows = self._connection.execute(
            "SELECT * FROM sources WHERE research_id = ? ORDER BY created_at ASC;",
            (research_id,),
        ).fetchall()
        return [self._row_to_model(row) for row in rows]

    def update(self, source: Source) -> None:
        self._connection.execute(
            """
            UPDATE sources
            SET title = ?, url = ?, author = ?, publication_date = ?, notes = ?, updated_at = ?
            WHERE id = ?;
            """,
            (
                source.title,
                source.url,
                source.author,
                source.publication_date,
                source.notes,
                source.updated_at,
                source.id,
            ),
        )
        self._connection.commit()

    def delete(self, source_id: int) -> None:
        self._connection.execute("DELETE FROM sources WHERE id = ?;", (source_id,))
        self._connection.commit()

    @staticmethod
    def _row_to_model(row: sqlite3.Row) -> Source:
        return Source(
            id=row["id"],
            research_id=row["research_id"],
            title=row["title"],
            url=row["url"],
            author=row["author"],
            publication_date=row["publication_date"],
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    