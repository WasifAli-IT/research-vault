import sqlite3
from pathlib import Path

import pytest

from core.database.connection import create_connection
from core.database.migration_runner import run_migrations, get_schema_version


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_research.db"


def test_migrations_create_all_tables(temp_db_path: Path) -> None:
    run_migrations(temp_db_path)

    connection = create_connection(temp_db_path)
    try:
        cursor = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        table_names = {row["name"] for row in cursor.fetchall()}
    finally:
        connection.close()

    expected_tables = {
        "categories",
        "research_projects",
        "sections",
        "notes",
        "sources",
        "search_index",
        "search_index_data",   # internal FTS5 shadow table
        "search_index_idx",    # internal FTS5 shadow table
        "search_index_docsize",  # internal FTS5 shadow table
        "search_index_config",   # internal FTS5 shadow table
    }
    assert expected_tables.issubset(table_names)


def test_migrations_are_idempotent(temp_db_path: Path) -> None:
    # Running migrations twice must not raise or duplicate anything.
    run_migrations(temp_db_path)
    run_migrations(temp_db_path)

    connection = create_connection(temp_db_path)
    try:
        version = get_schema_version(connection)
    finally:
        connection.close()

    assert version == 1


def test_foreign_keys_are_enforced(temp_db_path: Path) -> None:
    run_migrations(temp_db_path)

    connection = create_connection(temp_db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO sections (research_id, title, content, position, "
                "created_at, updated_at) VALUES (9999, 'Test', '', 0, '', '');"
            )
            connection.commit()
    finally:
        connection.close()


def test_search_index_updates_on_research_insert(temp_db_path: Path) -> None:
    run_migrations(temp_db_path)

    connection = create_connection(temp_db_path)
    try:
        connection.execute(
            "INSERT INTO research_projects (title, description, category_id, "
            "is_favorite, position, created_at, updated_at) VALUES "
            "('Artificial Intelligence', 'Overview of AI', NULL, 0, 0, '', '');"
        )
        connection.commit()

        cursor = connection.execute(
            "SELECT * FROM search_index WHERE entity_type = 'research';"
        )
        rows = cursor.fetchall()
        assert len(rows) == 1
        assert rows[0]["title"] == "Artificial Intelligence"
    finally:
        connection.close()
        