"""Data model representing a single search result."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SearchResult:
    """
    A single match returned by SearchService.

    Attributes:
        entity_type: One of "research", "section", "note", "source".
        entity_id: The database id of the matched entity.
        research_id: The id of the research project this result belongs to.
        title: Display title (may be empty, e.g. for notes).
        snippet: A short excerpt of matching text for display.
    """

    entity_type: str
    entity_id: int
    research_id: int
    title: str
    snippet: str
    