"""Fast full-text search backend using SQLite's FTS5 extension."""

from __future__ import annotations

import sqlite3

from core.models.search_result import SearchResult


class Fts5SearchBackend:
    """Performs full-text search using the search_index FTS5 table."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def search(self, query: str, limit: int = 50) -> list[SearchResult]:
        clean_query = query.strip()
        if not clean_query:
            return []

        # Treat each word as a prefix match for forgiving, "as you type"
        # style results (e.g. "neur" matches "neural").
        fts_query = " ".join(f"{word}*" for word in clean_query.split())

        rows = self._connection.execute(
            """
            SELECT entity_type, entity_id, research_id, title,
                   snippet(search_index, 4, '[', ']', '...', 8) AS snippet
            FROM search_index
            WHERE search_index MATCH ?
            ORDER BY rank
            LIMIT ?;
            """,
            (fts_query, limit),
        ).fetchall()

        return [
            SearchResult(
                entity_type=row["entity_type"],
                entity_id=row["entity_id"],
                research_id=row["research_id"],
                title=row["title"],
                snippet=row["snippet"],
            )
            for row in rows
        ]
    