"""Exceptions raised by the backup subsystem."""
from __future__ import annotations


class BackupError(Exception):
    """Base class for all backup-related errors."""


class BackupFileExistsError(BackupError):
    """Raised when a backup destination file already exists."""