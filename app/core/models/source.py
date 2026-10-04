"""Data model representing a source/reference for a research project."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Source:
    """
    A source is a reference/citation attached to a research project
    (e.g. a book, article, or website used during research).

    Attributes:
        id: Database primary key. None if not yet saved.
        research_id: Foreign key to the owning ResearchProject.
        title: Title of the source.
        url: Optional URL.
        author: Optional author name.
        publication_date: Optional free-form date string.
        notes: Optional free-form notes about this source.
        created_at: ISO-8601 UTC timestamp string.
        updated_at: ISO-8601 UTC timestamp string.
    """

    id: int | None
    research_id: int
    title: str
    url: str | None
    author: str | None
    publication_date: str | None
    notes: str
    created_at: str
    updated_at: str
    