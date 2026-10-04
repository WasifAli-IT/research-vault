"""
LIKE-based fallback search backend.

Used only when the SQLite build in use does not support the FTS5
extension. Slower than FTS5 and does not rank results, but works on
any standard SQLite installation.
"""

from __future__ import annotations

import sqlite3

from core.models.search_result import SearchResult


class LikeFallbackSearchBackend:
    """Performs a simple substring search across all research content."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def search(self, query: str, limit: int = 50) -> list[SearchResult]:
        clean_query = query.strip()
        if not clean_query:
            return []

        pattern = f"%{clean_query}%"
        results: list[SearchResult] = []

        for row in self._connection.execute(
            "SELECT id, title, description FROM research_projects "
            "WHERE title LIKE ? OR description LIKE ? LIMIT ?;",
            (pattern, pattern, limit),
        ).fetchall():
            results.append(
                SearchResult(
                    entity_type="research",
                    entity_id=row["id"],
                    research_id=row["id"],
                    title=row["title"],
                    snippet=self._truncate(row["description"]),
                )
            )

        for row in self._connection.execute(
            "SELECT id, research_id, title, content FROM sections "
            "WHERE title LIKE ? OR content LIKE ? LIMIT ?;",
            (pattern, pattern, limit),
        ).fetchall():
            results.append(
                SearchResult(
                    entity_type="section",
                    entity_id=row["id"],
                    research_id=row["research_id"],
                    title=row["title"],
                    snippet=self._truncate(row["content"]),
                )
            )

        for row in self._connection.execute(
            "SELECT id, research_id, content FROM notes WHERE content LIKE ? LIMIT ?;",
            (pattern, limit),
        ).fetchall():
            results.append(
                SearchResult(
                    entity_type="note",
                    entity_id=row["id"],
                    research_id=row["research_id"],
                    title="",
                    snippet=self._truncate(row["content"]),
                )
            )

        for row in self._connection.execute(
            "SELECT id, research_id, title, notes FROM sources "
            "WHERE title LIKE ? OR notes LIKE ? LIMIT ?;",
            (pattern, pattern, limit),
        ).fetchall():
            results.append(
                SearchResult(
                    entity_type="source",
                    entity_id=row["id"],
                    research_id=row["research_id"],
                    title=row["title"],
                    snippet=self._truncate(row["notes"]),
                )
            )

        return results[:limit]

    @staticmethod
    def _truncate(text: str, length: int = 120) -> str:
        text = text or ""
        return text if len(text) <= length else text[:length] + "..."
    