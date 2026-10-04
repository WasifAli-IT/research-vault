from pathlib import Path

import pytest

from core.database.connection import create_connection
from core.database.migration_runner import run_migrations


@pytest.fixture
def connection(tmp_path: Path):
    db_path = tmp_path / "test_research.db"
    run_migrations(db_path)
    conn = create_connection(db_path)
    yield conn
    conn.close()
    