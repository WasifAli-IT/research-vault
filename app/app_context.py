"""Composition root helper: builds the database connection and all services."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from core.backup.backup_service import BackupService
from core.database.connection import create_connection
from core.database.migration_runner import run_migrations
from core.export.export_service import ExportService
from core.export.import_service import ImportService
from core.search.search_service import SearchService
from core.security.vault_manager import VaultManager
from core.services.category_service import CategoryService
from core.services.note_service import NoteService
from core.services.research_service import ResearchService
from core.services.section_service import SectionService
from core.services.source_service import SourceService
from core.settings.settings_service import SettingsService

class AppContext:
    def __init__(self, connection: sqlite3.Connection, database_path: Path, vaults_dir: Path) -> None:
        self.connection = connection
        self.category_service = CategoryService(connection)
        self.research_service = ResearchService(connection)
        self.section_service = SectionService(connection)
        self.note_service = NoteService(connection)
        self.source_service = SourceService(connection)
        self.search_service = SearchService(connection)
        self.vault_manager = VaultManager(vaults_dir)
        self.backup_service = BackupService(database_path)
        self.export_service = ExportService(
            self.research_service, self.section_service, self.note_service, self.source_service
        )
        self.import_service = ImportService(
            self.research_service, self.section_service, self.note_service, self.source_service
        )
        self.settings_service = SettingsService(database_path.parent / "settings.json")

    @classmethod
    def create(cls, database_path: Path) -> "AppContext":
        run_migrations(database_path)
        connection = create_connection(database_path)
        vaults_dir = database_path.parent / "vaults"
        return cls(connection, database_path, vaults_dir)

    def close(self) -> None:
        self.connection.close()