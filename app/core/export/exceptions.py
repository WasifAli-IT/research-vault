"""Exceptions raised by the export/import subsystem."""
from __future__ import annotations


class ExportError(Exception):
    """Base class for all export-related errors."""


class ExportFileExistsError(ExportError):
    """Raised when an export destination file already exists."""


class ImportError_(ExportError):
    """Raised when an import file is missing, unreadable, or malformed."""