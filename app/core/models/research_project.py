"""Data model representing a single research project."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ResearchProject:
    """
    A research project is the top-level container: a title, a
    description/introduction, and (elsewhere) a set of sections,
    notes, and sources that belong to it.

    Attributes:
        id: Database primary key. None if not yet saved.
        title: The research topic/title.
        description: Short introduction/overview text (Markdown).
        category_id: Optional foreign key to a Category.
        is_favorite: Reserved for a future "favorites" feature.
        position: Sort order among research projects.
        created_at: ISO-8601 UTC timestamp string.
        updated_at: ISO-8601 UTC timestamp string.
    """

    id: int | None
    title: str
    description: str
    category_id: int | None
    is_favorite: bool
    position: int
    created_at: str
    updated_at: str
    