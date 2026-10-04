"""
Application-wide logging configuration.

Security note: this module installs a filter that redacts common
sensitive field names before any log record is written, as a
defense-in-depth measure. It is NOT a substitute for simply never
logging secrets in the first place -- calling code must still never
pass raw passwords, encryption keys, or decrypted vault content into
log calls.
"""

from __future__ import annotations

import logging
import logging.handlers
import re
from pathlib import Path

_REDACT_PATTERNS = [
    re.compile(r"(password\s*=\s*)([^\s,)]+)", re.IGNORECASE),
    re.compile(r"(passphrase\s*=\s*)([^\s,)]+)", re.IGNORECASE),
    re.compile(r"(pin\s*=\s*)([^\s,)]+)", re.IGNORECASE),
    re.compile(r"(key\s*=\s*)([^\s,)]+)", re.IGNORECASE),
    re.compile(r"(secret\s*=\s*)([^\s,)]+)", re.IGNORECASE),
]


class RedactionFilter(logging.Filter):
    """Scrubs likely-sensitive values out of log messages before they are emitted."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:
            return True

        redacted = message
        for pattern in _REDACT_PATTERNS:
            redacted = pattern.sub(r"\1[REDACTED]", redacted)

        if redacted != message:
            record.msg = redacted
            record.args = ()

        return True


def configure_logging(log_file: Path, level: int = logging.INFO) -> None:
    """
    Configure the root logger with a rotating file handler and a
    console handler. Safe to call once at application startup.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(RedactionFilter())

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RedactionFilter())

    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)