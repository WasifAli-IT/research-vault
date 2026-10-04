"""Exceptions raised by the service layer for business-rule violations."""

from __future__ import annotations


class ValidationError(Exception):
    """Raised when input data fails a business validation rule."""
    