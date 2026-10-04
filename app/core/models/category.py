"""Data model representing a research category/folder."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Category:
    """
    A category is a simple grouping/folder for research projects.

    Attributes:
        id: Database primary key. None if not yet saved.
        name: Display name of the category.
        color: Optional hex color string (e.g. "#3498db") for UI display.
        position: Sort order among categories.
        created_at: ISO-8601 UTC timestamp string.
        updated_at: ISO-8601 UTC timestamp string.
    """

    id: int | None
    name: str
    color: str | None
    position: int
    created_at: str
    updated_at: str
    