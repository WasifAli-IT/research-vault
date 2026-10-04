"""Repository for Note persistence."""

from __future__ import annotations

import sqlite3

from core.models.note import Note


class NoteRepository:
    """Handles all database access for notes."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create(self, note: Note) -> Note:
        cursor = self._connection.execute(
            """
            INSERT INTO notes (research_id, section_id, content, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                note.research_id,
                note.section_id,
                note.content,
                note.created_at,
                note.updated_at,
            ),
        )
        self._connection.commit()
        note.id = cursor.lastrowid
        return note

    def get_by_id(self, note_id: int) -> Note | None:
        row = self._connection.execute(
            "SELECT * FROM notes WHERE id = ?;", (note_id,)
        ).fetchone()
        return self._row_to_model(row) if row else None

    def list_by_research(self, research_id: int) -> list[Note]:
        rows = self._connection.execute(
            "SELECT * FROM notes WHERE research_id = ? ORDER BY created_at ASC;",
            (research_id,),
        ).fetchall()
        return [self._row_to_model(row) for row in rows]

    def update(self, note: Note) -> None:
        self._connection.execute(
            "UPDATE notes SET content = ?, updated_at = ? WHERE id = ?;",
            (note.content, note.updated_at, note.id),
        )
        self._connection.commit()

    def delete(self, note_id: int) -> None:
        self._connection.execute("DELETE FROM notes WHERE id = ?;", (note_id,))
        self._connection.commit()

    @staticmethod
    def _row_to_model(row: sqlite3.Row) -> Note:
        return Note(
            id=row["id"],
            research_id=row["research_id"],
            section_id=row["section_id"],
            content=row["content"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    