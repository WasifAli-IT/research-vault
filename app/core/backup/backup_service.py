"""BackupService: create and restore full database backups using SQLite's online backup API."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from core.backup.exceptions import BackupFileExistsError


class BackupService:
    """Creates and restores full-database backups via SQLite's online backup API."""

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def create_backup(self, destination_path: Path) -> None:
        """
        Copy the live database to destination_path using SQLite's online
        backup API (safe even while the app has the database open).

        Raises:
            BackupFileExistsError: destination_path already exists. Backups
                are never silently overwritten.
        """
        if destination_path.exists():
            raise BackupFileExistsError(
                f"A file already exists at '{destination_path}'. "
                "Choose a different location or delete it first."
            )
        destination_path.parent.mkdir(parents=True, exist_ok=True)

        source_connection = sqlite3.connect(str(self._database_path))
        try:
            destination_connection = sqlite3.connect(str(destination_path))
            try:
                source_connection.backup(destination_connection)
            finally:
                destination_connection.close()
        finally:
            source_connection.close()

    def restore_backup(self, source_backup_path: Path) -> None:
        """
        Replace the live database with the contents of a backup file.

        This intentionally overwrites the live database -- restoring is,
        by definition, meant to replace current data with the backup.
        The caller (UI layer) is responsible for confirming this
        destructive action with the user before calling this method.

        Raises:
            FileNotFoundError: source_backup_path does not exist.
        """
        if not source_backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: '{source_backup_path}'")

        source_connection = sqlite3.connect(str(source_backup_path))
        try:
            destination_connection = sqlite3.connect(str(self._database_path))
            try:
                source_connection.backup(destination_connection)
            finally:
                destination_connection.close()
        finally:
            source_connection.close()