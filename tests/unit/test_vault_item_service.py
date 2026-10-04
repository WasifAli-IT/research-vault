"""Tests for VaultItemService: CRUD access to items stored in the vault."""
from __future__ import annotations

import pytest

from core.security.vault_item_service import VaultItemService
from core.security.vault_service import VaultService
from core.services.exceptions import ValidationError


@pytest.fixture
def service(tmp_path):
    vault_service = VaultService(tmp_path / "vault.json")
    vault_service.setup_vault("correct-password")
    return VaultItemService(vault_service)


def test_new_vault_has_no_items(service):
    assert service.list_items() == []


def test_add_item_appears_in_list(service):
    item = service.add_item("My secret", "Some body text")

    items = service.list_items()
    assert len(items) == 1
    assert items[0].id == item.id
    assert items[0].title == "My secret"
    assert items[0].body == "Some body text"


def test_add_item_with_empty_title_raises(service):
    with pytest.raises(ValidationError):
        service.add_item("   ", "body")


def test_get_item_returns_matching_item(service):
    added = service.add_item("Find me", "body")

    found = service.get_item(added.id)
    assert found.title == "Find me"


def test_get_item_missing_raises(service):
    with pytest.raises(ValidationError):
        service.get_item("does-not-exist")


def test_update_item_changes_title_and_body(service):
    added = service.add_item("Old title", "Old body")

    updated = service.update_item(added.id, title="New title", body="New body")

    assert updated.title == "New title"
    assert updated.body == "New body"
    assert service.get_item(added.id).title == "New title"


def test_update_item_with_empty_title_raises(service):
    added = service.add_item("Title", "body")

    with pytest.raises(ValidationError):
        service.update_item(added.id, title="   ")


def test_update_item_missing_raises(service):
    with pytest.raises(ValidationError):
        service.update_item("does-not-exist", title="New")


def test_delete_item_removes_it(service):
    added = service.add_item("To delete", "body")

    service.delete_item(added.id)

    assert service.list_items() == []


def test_delete_item_missing_raises(service):
    with pytest.raises(ValidationError):
        service.delete_item("does-not-exist")