"""Business logic for managing sources/references."""

from __future__ import annotations

import sqlite3

from core.database.repositories.source_repository import SourceRepository
from core.models.source import Source
from core.services.exceptions import ValidationError
from core.utils.time_utils import utc_now_iso


class SourceService:
    """Validates input and coordinates source persistence."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._repository = SourceRepository(connection)

    def add_source(
        self,
        research_id: int,
        title: str,
        url: str | None = None,
        author: str | None = None,
        publication_date: str | None = None,
        notes: str = "",
    ) -> Source:
        clean_title = title.strip()
        if not clean_title:
            raise ValidationError("Source title cannot be empty.")

        now = utc_now_iso()
        source = Source(
            id=None,
            research_id=research_id,
            title=clean_title,
            url=url,
            author=author,
            publication_date=publication_date,
            notes=notes,
            created_at=now,
            updated_at=now,
        )
        return self._repository.create(source)

    def list_sources(self, research_id: int) -> list[Source]:
        return self._repository.list_by_research(research_id)

    def update_source(self, source_id: int, **fields: str | None) -> Source:
        source = self._repository.get_by_id(source_id)
        if source is None:
            raise ValidationError(f"Source {source_id} does not exist.")

        if "title" in fields:
            clean_title = (fields["title"] or "").strip()
            if not clean_title:
                raise ValidationError("Source title cannot be empty.")
            source.title = clean_title
        if "url" in fields:
            source.url = fields["url"]
        if "author" in fields:
            source.author = fields["author"]
        if "publication_date" in fields:
            source.publication_date = fields["publication_date"]
        if "notes" in fields:
            source.notes = fields["notes"] or ""

        source.updated_at = utc_now_iso()
        self._repository.update(source)
        return source

    def delete_source(self, source_id: int) -> None:
        self._repository.delete(source_id)
        