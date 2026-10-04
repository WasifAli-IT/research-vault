"""Tests for VaultManager: creating, listing, and deleting named vaults."""
from __future__ import annotations

import pytest

from core.security.vault_manager import VaultManager
from core.services.exceptions import ValidationError


@pytest.fixture
def manager(tmp_path):
    return VaultManager(tmp_path / "vaults")


def test_new_manager_has_no_vaults(manager):
    assert manager.list_vault_names() == []


def test_create_and_setup_vault_appears_in_list(manager):
    service = manager.create_vault_service("Personal")
    service.setup_vault("correct-password")

    assert manager.list_vault_names() == ["Personal"]


def test_create_vault_with_empty_name_raises(manager):
    with pytest.raises(ValidationError):
        manager.create_vault_service("   ")


def test_create_vault_with_invalid_characters_raises(manager):
    with pytest.raises(ValidationError):
        manager.create_vault_service("bad/name")


def test_create_duplicate_vault_name_raises(manager):
    service = manager.create_vault_service("Personal")
    service.setup_vault("correct-password")

    with pytest.raises(ValidationError):
        manager.create_vault_service("Personal")


def test_create_duplicate_vault_name_case_insensitive_raises(manager):
    service = manager.create_vault_service("Personal")
    service.setup_vault("correct-password")

    with pytest.raises(ValidationError):
        manager.create_vault_service("personal")


def test_get_vault_service_for_existing_vault_succeeds(manager):
    service = manager.create_vault_service("Personal")
    service.setup_vault("correct-password")

    fetched = manager.get_vault_service("Personal")
    assert fetched.is_set_up() is True


def test_get_vault_service_for_missing_vault_raises(manager):
    with pytest.raises(ValidationError):
        manager.get_vault_service("Nonexistent")


def test_delete_vault_removes_it(manager):
    service = manager.create_vault_service("Personal")
    service.setup_vault("correct-password")

    manager.delete_vault("Personal")

    assert manager.list_vault_names() == []


def test_delete_missing_vault_raises(manager):
    with pytest.raises(ValidationError):
        manager.delete_vault("Nonexistent")