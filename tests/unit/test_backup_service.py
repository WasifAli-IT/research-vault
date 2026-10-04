"""Tests for BackupService: full-database backup and restore."""
from __future__ import annotations

import pytest

from core.backup.backup_service import BackupService
from core.backup.exceptions import BackupFileExistsError
from core.database.connection import create_connection
from core.database.migration_runner import run_migrations
from core.services.research_service import ResearchService


@pytest.fixture
def database_path(tmp_path):
    path = tmp_path / "research.db"
    run_migrations(path)
    return path


def test_create_backup_copies_data(database_path, tmp_path):
    connection = create_connection(database_path)
    research_service = ResearchService(connection)
    research_service.create_project("Original Project")
    connection.close()

    backup_service = BackupService(database_path)
    backup_path = tmp_path / "backup.db"
    backup_service.create_backup(backup_path)

    assert backup_path.exists()

    backup_connection = create_connection(backup_path)
    backup_research_service = ResearchService(backup_connection)
    projects = backup_research_service.list_projects()
    backup_connection.close()

    assert len(projects) == 1
    assert projects[0].title == "Original Project"


def test_create_backup_never_overwrites_existing_file(database_path, tmp_path):
    backup_service = BackupService(database_path)
    backup_path = tmp_path / "backup.db"
    backup_path.write_text("not a real backup")

    with pytest.raises(BackupFileExistsError):
        backup_service.create_backup(backup_path)


def test_restore_backup_replaces_live_database(database_path, tmp_path):
    connection = create_connection(database_path)
    research_service = ResearchService(connection)
    research_service.create_project("Project A")
    connection.close()

    backup_service = BackupService(database_path)
    backup_path = tmp_path / "backup.db"
    backup_service.create_backup(backup_path)

    connection = create_connection(database_path)
    research_service = ResearchService(connection)
    research_service.create_project("Project B")
    connection.close()

    backup_service.restore_backup(backup_path)

    connection = create_connection(database_path)
    research_service = ResearchService(connection)
    projects = research_service.list_projects()
    connection.close()

    titles = [project.title for project in projects]
    assert titles == ["Project A"]


def test_restore_backup_missing_file_raises(database_path, tmp_path):
    backup_service = BackupService(database_path)
    missing_path = tmp_path / "does_not_exist.db"

    with pytest.raises(FileNotFoundError):
        backup_service.restore_backup(missing_path)