"""Exceptions raised by the Secure Vault subsystem."""
from __future__ import annotations


class VaultError(Exception):
    """Base class for all vault-related errors."""


class VaultNotSetUpError(VaultError):
    """Raised when an operation requires the vault to be set up first."""


class VaultAlreadySetUpError(VaultError):
    """Raised when trying to set up a vault that already exists."""


class VaultLockedError(VaultError):
    """Raised when an operation requires the vault to be unlocked."""


class IncorrectCredentialError(VaultError):
    """Raised when a password or recovery key does not unlock the vault."""


class VaultThrottledError(VaultError):
    """Raised when too many failed unlock attempts require a cooldown."""

    def __init__(self, retry_after_seconds: float) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            f"Too many failed attempts. Try again in "
            f"{retry_after_seconds:.0f} seconds."
        )