"""
VaultItemService: CRUD operations for items stored inside the Secure Vault.

Vault items are simple title/body records (e.g. secret notes) that live
inside the vault's encrypted content blob. All reads/writes go through
VaultService, so items only ever exist in decrypted form in memory while
the vault is unlocked.
"""
from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass

from core.security.vault_service import VaultService
from core.services.exceptions import ValidationError
from core.utils.time_utils import utc_now_iso


@dataclass
class VaultItem:
    id: str
    title: str
    body: str
    created_at: str
    updated_at: str


class VaultItemService:
    """Provides create/read/update/delete access to vault items."""

    def __init__(self, vault_service: VaultService) -> None:
        self._vault_service = vault_service

    def list_items(self) -> list[VaultItem]:
        """Return all vault items, in stored order."""
        content = self._vault_service.read_content()
        return [VaultItem(**item) for item in content.get("items", [])]

    def get_item(self, item_id: str) -> VaultItem:
        """Return a single vault item by id, or raise ValidationError."""
        for item in self.list_items():
            if item.id == item_id:
                return item
        raise ValidationError(f"No vault item with id '{item_id}' was found.")

    def add_item(self, title: str, body: str = "") -> VaultItem:
        """Create and persist a new vault item."""
        title = title.strip()
        if not title:
            raise ValidationError("Vault item title cannot be empty.")

        content = self._vault_service.read_content()
        now = utc_now_iso()
        new_item = VaultItem(
            id=uuid.uuid4().hex,
            title=title,
            body=body,
            created_at=now,
            updated_at=now,
        )
        content.setdefault("items", []).append(asdict(new_item))
        self._vault_service.write_content(content)
        return new_item

    def update_item(
        self,
        item_id: str,
        title: str | None = None,
        body: str | None = None,
    ) -> VaultItem:
        """Update the title and/or body of an existing vault item."""
        content = self._vault_service.read_content()
        items = content.get("items", [])
        for stored in items:
            if stored["id"] == item_id:
                if title is not None:
                    title = title.strip()
                    if not title:
                        raise ValidationError("Vault item title cannot be empty.")
                    stored["title"] = title
                if body is not None:
                    stored["body"] = body
                stored["updated_at"] = utc_now_iso()
                self._vault_service.write_content(content)
                return VaultItem(**stored)
        raise ValidationError(f"No vault item with id '{item_id}' was found.")

    def delete_item(self, item_id: str) -> None:
        """Delete a vault item by id."""
        content = self._vault_service.read_content()
        items = content.get("items", [])
        remaining = [item for item in items if item["id"] != item_id]
        if len(remaining) == len(items):
            raise ValidationError(f"No vault item with id '{item_id}' was found.")
        content["items"] = remaining
        self._vault_service.write_content(content)