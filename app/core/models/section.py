"""Data model representing a section (subheading) within a research project."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Section:
    """
    A section is a titled block of long-form Markdown content that
    belongs to exactly one research project (e.g. "History of AI",
    "Machine Learning", etc.).

    Attributes:
        id: Database primary key. None if not yet saved.
        research_id: Foreign key to the owning ResearchProject.
        title: The section heading.
        content: Long-form Markdown content.
        position: Sort order among sections within the same project.
        created_at: ISO-8601 UTC timestamp string.
        updated_at: ISO-8601 UTC timestamp string.
    """

    id: int | None
    research_id: int
    title: str
    content: str
    position: int
    created_at: str
    updated_at: str
    