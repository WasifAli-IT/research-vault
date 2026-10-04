"""
Migration runner.

Applies pending schema migrations to a SQLite database, tracking
the currently-applied schema version using SQLite's built-in
PRAGMA user_version. Safe to call every time the application starts.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from core.database.connection import create_connection
from core.database.migrations import m0001_initial_schema

logger = logging.getLogger(__name__)

# Ordered list of all migrations. Each module must define VERSION (int)
# and upgrade(connection) -> None. New migrations are appended here,
# never inserted in the middle or renumbered.
_MIGRATIONS = [
    m0001_initial_schema,
]


def get_schema_version(connection: sqlite3.Connection) -> int:
    cursor = connection.execute("PRAGMA user_version;")
    row = cursor.fetchone()
    return int(row[0]) if row else 0


def set_schema_version(connection: sqlite3.Connection, version: int) -> None:
    # PRAGMA statements do not support parameter binding, so the
    # integer is validated as an int (never raw user input) before
    # being interpolated.
    connection.execute(f"PRAGMA user_version = {int(version)};")


def run_migrations(database_path: Path) -> None:
    """
    Apply all pending migrations to the database at database_path,
    creating the file if it does not already exist.
    """
    connection = create_connection(database_path)
    try:
        current_version = get_schema_version(connection)
        logger.info("Current database schema version: %s", current_version)

        for migration in _MIGRATIONS:
            if migration.VERSION <= current_version:
                continue

            logger.info("Applying migration to version %s", migration.VERSION)
            migration.upgrade(connection)
            set_schema_version(connection, migration.VERSION)
            connection.commit()

        logger.info("Database schema is up to date (version %s)", get_schema_version(connection))
    finally:
        connection.close()
        