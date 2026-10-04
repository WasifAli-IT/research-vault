"""Repository for Section persistence."""

from __future__ import annotations

import sqlite3

from core.models.section import Section


class SectionRepository:
    """Handles all database access for research sections."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create(self, section: Section) -> Section:
        cursor = self._connection.execute(
            """
            INSERT INTO sections (research_id, title, content, position, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (
                section.research_id,
                section.title,
                section.content,
                section.position,
                section.created_at,
                section.updated_at,
            ),
        )
        self._connection.commit()
        section.id = cursor.lastrowid
        return section

    def get_by_id(self, section_id: int) -> Section | None:
        row = self._connection.execute(
            "SELECT * FROM sections WHERE id = ?;", (section_id,)
        ).fetchone()
        return self._row_to_model(row) if row else None

    def list_by_research(self, research_id: int) -> list[Section]:
        rows = self._connection.execute(
            "SELECT * FROM sections WHERE research_id = ? ORDER BY position ASC;",
            (research_id,),
        ).fetchall()
        return [self._row_to_model(row) for row in rows]

    def update(self, section: Section) -> None:
        self._connection.execute(
            """
            UPDATE sections
            SET title = ?, content = ?, position = ?, updated_at = ?
            WHERE id = ?;
            """,
            (
                section.title,
                section.content,
                section.position,
                section.updated_at,
                section.id,
            ),
        )
        self._connection.commit()

    def reorder(self, section_id: int, new_position: int) -> None:
        self._connection.execute(
            "UPDATE sections SET position = ? WHERE id = ?;",
            (new_position, section_id),
        )
        self._connection.commit()

    def delete(self, section_id: int) -> None:
        self._connection.execute(
            "DELETE FROM sections WHERE id = ?;", (section_id,)
        )
        self._connection.commit()

    @staticmethod
    def _row_to_model(row: sqlite3.Row) -> Section:
        return Section(
            id=row["id"],
            research_id=row["research_id"],
            title=row["title"],
            content=row["content"],
            position=row["position"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    