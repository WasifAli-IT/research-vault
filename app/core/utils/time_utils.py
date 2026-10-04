"""Time utilities for consistent timestamp handling across the application."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now_iso() -> str:
    """
    Return the current UTC time as a millisecond-precision ISO-8601
    string, e.g. "2025-01-01T12:00:00.123Z".

    A single shared function is used everywhere timestamps are needed
    so that created_at/updated_at values are always consistent and
    sortable as plain text.
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
