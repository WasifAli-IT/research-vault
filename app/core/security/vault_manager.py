"""VaultManager: creates, lists, and deletes multiple independent named vaults."""
from __future__ import annotations

import re
from pathlib import Path

from core.security.vault_service import VaultService
from core.services.exceptions import ValidationError

_NAME_PATTERN = re.compile(r"^[A-Za-z0-9 _-]+$")
_MAX_NAME_LENGTH = 50


class VaultManager:
    """Manages multiple independent, named Secure Vaults on disk."""

    def __init__(self, vaults_dir: Path) -> None:
        self._vaults_dir = vaults_dir

    def list_vault_names(self) -> list[str]:
        """Return the names of all vaults that have completed setup, sorted."""
        if not self._vaults_dir.exists():
            return []
        names = [path.stem for path in self._vaults_dir.glob("*.json")]
        return sorted(names, key=str.lower)

    def vault_exists(self, name: str) -> bool:
        """Return True if a vault with this name (case-insensitive) exists."""
        return self._resolve_existing_name(name.strip()) is not None

    def create_vault_service(self, name: str) -> VaultService:
        """Validate a new vault name and return a VaultService for it (not yet set up)."""
        clean_name = self._validate_name(name)
        if self.vault_exists(clean_name):
            raise ValidationError(f"A vault named '{clean_name}' already exists.")
        return VaultService(self._path_for(clean_name))

    def get_vault_service(self, name: str) -> VaultService:
        """Return a VaultService for an existing vault name."""
        clean_name = self._validate_name(name)
        actual_name = self._resolve_existing_name(clean_name)
        if actual_name is None:
            raise ValidationError(f"No vault named '{clean_name}' was found.")
        return VaultService(self._path_for(actual_name))

    def delete_vault(self, name: str) -> None:
        """Permanently delete a vault's encrypted file from disk."""
        clean_name = self._validate_name(name)
        actual_name = self._resolve_existing_name(clean_name)
        if actual_name is None:
            raise ValidationError(f"No vault named '{clean_name}' was found.")
        self._path_for(actual_name).unlink()

    def _resolve_existing_name(self, clean_name: str) -> str | None:
        for existing in self.list_vault_names():
            if existing.lower() == clean_name.lower():
                return existing
        return None

    def _validate_name(self, name: str) -> str:
        clean_name = name.strip()
        if not clean_name:
            raise ValidationError("Vault name cannot be empty.")
        if len(clean_name) > _MAX_NAME_LENGTH:
            raise ValidationError(f"Vault name cannot exceed {_MAX_NAME_LENGTH} characters.")
        if not _NAME_PATTERN.match(clean_name):
            raise ValidationError(
                "Vault name can only contain letters, numbers, spaces, hyphens, and underscores."
            )
        return clean_name

    def _path_for(self, name: str) -> Path:
        return self._vaults_dir / f"{name}.json"