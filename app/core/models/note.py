"""Data model representing a note attached to a research project."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Note:
    """
    A note is a free-form Markdown remark attached to a research
    project, and optionally scoped to one specific section within it.

    Attributes:
        id: Database primary key. None if not yet saved.
        research_id: Foreign key to the owning ResearchProject.
        section_id: Optional foreign key to a specific Section.
        content: Markdown note content.
        created_at: ISO-8601 UTC timestamp string.
        updated_at: ISO-8601 UTC timestamp string.
    """

    id: int | None
    research_id: int
    section_id: int | None
    content: str
    created_at: str
    updated_at: str
    