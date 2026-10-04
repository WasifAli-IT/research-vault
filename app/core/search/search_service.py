"""Public search interface used by the rest of the application."""

from __future__ import annotations

import logging
import sqlite3

from core.models.search_result import SearchResult
from core.search.fts5_backend import Fts5SearchBackend
from core.search.like_fallback_backend import LikeFallbackSearchBackend

logger = logging.getLogger(__name__)


class SearchService:
    """
    Provides full-text search across research projects, sections,
    notes, and sources. Automatically uses SQLite FTS5 when available,
    and transparently falls back to a slower LIKE-based search
    otherwise. Callers never need to know which backend is active.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        if self._fts5_is_available(connection):
            logger.info("Using FTS5 search backend")
            self._backend = Fts5SearchBackend(connection)
        else:
            logger.warning("FTS5 unavailable, using LIKE fallback search backend")
            self._backend = LikeFallbackSearchBackend(connection)

    def search(self, query: str, limit: int = 50) -> list[SearchResult]:
        return self._backend.search(query, limit=limit)

    @staticmethod
    def _fts5_is_available(connection: sqlite3.Connection) -> bool:
        row = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='search_index';"
        ).fetchone()
        return row is not None
    