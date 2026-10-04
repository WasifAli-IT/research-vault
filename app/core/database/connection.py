"""
SQLite connection management.

This is the ONLY module allowed to call sqlite3.connect() directly.
All other code obtains connections through this module, ensuring
consistent PRAGMA settings (foreign keys, row factory) everywhere.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


def create_connection(database_path: Path) -> sqlite3.Connection:
    """
    Create a new SQLite connection configured for this application.

    - Foreign key constraints are enforced (SQLite disables this by
      default for backward compatibility reasons).
    - Rows are returned as sqlite3.Row objects so columns can be
      accessed by name (e.g. row["title"]) instead of only by index.
    """
    connection = sqlite3.connect(str(database_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


@contextmanager
def connection_scope(database_path: Path) -> Iterator[sqlite3.Connection]:
    """
    Context manager that opens a connection, commits on success,
    rolls back on error, and always closes the connection.

    Usage:
        with connection_scope(db_path) as conn:
            conn.execute("INSERT INTO ...")
    """
    connection = create_connection(database_path)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
        