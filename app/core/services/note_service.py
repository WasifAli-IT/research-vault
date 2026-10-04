"""Business logic for managing notes."""

from __future__ import annotations

import sqlite3

from core.database.repositories.note_repository import NoteRepository
from core.models.note import Note
from core.services.exceptions import ValidationError
from core.utils.time_utils import utc_now_iso


class NoteService:
    """Validates input and coordinates note persistence."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._repository = NoteRepository(connection)

    def add_note(self, research_id: int, content: str, section_id: int | None = None) -> Note:
        clean_content = content.strip()
        if not clean_content:
            raise ValidationError("Note content cannot be empty.")

        now = utc_now_iso()
        note = Note(
            id=None,
            research_id=research_id,
            section_id=section_id,
            content=clean_content,
            created_at=now,
            updated_at=now,
        )
        return self._repository.create(note)

    def list_notes(self, research_id: int) -> list[Note]:
        return self._repository.list_by_research(research_id)

    def update_note(self, note_id: int, new_content: str) -> Note:
        clean_content = new_content.strip()
        if not clean_content:
            raise ValidationError("Note content cannot be empty.")

        note = self._repository.get_by_id(note_id)
        if note is None:
            raise ValidationError(f"Note {note_id} does not exist.")

        note.content = clean_content
        note.updated_at = utc_now_iso()
        self._repository.update(note)
        return note

    def delete_note(self, note_id: int) -> None:
        self._repository.delete(note_id)
        