"""Business logic for managing research sections."""

from __future__ import annotations

import sqlite3

from core.database.repositories.section_repository import SectionRepository
from core.models.section import Section
from core.services.exceptions import ValidationError
from core.utils.time_utils import utc_now_iso


class SectionService:
    """Validates input and coordinates section persistence and ordering."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._repository = SectionRepository(connection)

    def add_section(self, research_id: int, title: str, content: str = "") -> Section:
        clean_title = title.strip()
        if not clean_title:
            raise ValidationError("Section title cannot be empty.")

        position = len(self._repository.list_by_research(research_id))
        now = utc_now_iso()

        section = Section(
            id=None,
            research_id=research_id,
            title=clean_title,
            content=content,
            position=position,
            created_at=now,
            updated_at=now,
        )
        return self._repository.create(section)

    def list_sections(self, research_id: int) -> list[Section]:
        return self._repository.list_by_research(research_id)

    def rename_section(self, section_id: int, new_title: str) -> Section:
        clean_title = new_title.strip()
        if not clean_title:
            raise ValidationError("Section title cannot be empty.")

        section = self._require_section(section_id)
        section.title = clean_title
        section.updated_at = utc_now_iso()
        self._repository.update(section)
        return section

    def update_content(self, section_id: int, new_content: str) -> Section:
        section = self._require_section(section_id)
        section.content = new_content
        section.updated_at = utc_now_iso()
        self._repository.update(section)
        return section

    def reorder_sections(self, research_id: int, ordered_section_ids: list[int]) -> None:
        """
        Apply a new order to all sections of a research project.

        ordered_section_ids must contain exactly the same section IDs
        already belonging to research_id, listed in the desired order.
        """
        current = self._repository.list_by_research(research_id)
        current_ids = {section.id for section in current}

        if set(ordered_section_ids) != current_ids:
            raise ValidationError(
                "Reorder list must contain exactly the sections belonging "
                "to this research project."
            )

        for position, section_id in enumerate(ordered_section_ids):
            self._repository.reorder(section_id, position)

    def delete_section(self, section_id: int) -> None:
        self._repository.delete(section_id)

    def _require_section(self, section_id: int) -> Section:
        section = self._repository.get_by_id(section_id)
        if section is None:
            raise ValidationError(f"Section {section_id} does not exist.")
        return section
    