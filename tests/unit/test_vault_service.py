"""Tests for VaultService: setup, unlock, lock, and content access."""
from __future__ import annotations

import pytest

from core.security.exceptions import (
    IncorrectCredentialError,
    VaultAlreadySetUpError,
    VaultLockedError,
    VaultNotSetUpError,
    VaultThrottledError,
)
from core.security.vault_service import VaultService


def test_new_vault_is_not_set_up(tmp_path):
    service = VaultService(tmp_path / "vault.json")
    assert service.is_set_up() is False
    assert service.is_unlocked() is False


def test_setup_creates_vault_and_unlocks_it(tmp_path):
    service = VaultService(tmp_path / "vault.json")
    recovery_key = service.setup_vault("correct-password")

    assert service.is_set_up() is True
    assert service.is_unlocked() is True
    assert len(recovery_key.split("-")) == 6


def test_setup_twice_raises_already_set_up(tmp_path):
    service = VaultService(tmp_path / "vault.json")
    service.setup_vault("correct-password")

    with pytest.raises(VaultAlreadySetUpError):
        service.setup_vault("another-password")


def test_lock_then_unlock_with_password_succeeds(tmp_path):
    service = VaultService(tmp_path / "vault.json")
    service.setup_vault("correct-password")
    service.lock_vault()
    assert service.is_unlocked() is False

    service.unlock_vault("correct-password")
    assert service.is_unlocked() is True


def test_unlock_with_recovery_key_succeeds(tmp_path):
    service = VaultService(tmp_path / "vault.json")
    recovery_key = service.setup_vault("correct-password")
    service.lock_vault()

    service.unlock_vault(recovery_key)
    assert service.is_unlocked() is True


def test_unlock_with_wrong_secret_raises(tmp_path):
    service = VaultService(tmp_path / "vault.json")
    service.setup_vault("correct-password")
    service.lock_vault()

    with pytest.raises(IncorrectCredentialError):
        service.unlock_vault("wrong-password")
    assert service.is_unlocked() is False


def test_unlock_before_setup_raises_not_set_up(tmp_path):
    service = VaultService(tmp_path / "vault.json")

    with pytest.raises(VaultNotSetUpError):
        service.unlock_vault("anything")


def test_read_content_while_locked_raises(tmp_path):
    service = VaultService(tmp_path / "vault.json")
    service.setup_vault("correct-password")
    service.lock_vault()

    with pytest.raises(VaultLockedError):
        service.read_content()


def test_write_and_read_content_roundtrip(tmp_path):
    service = VaultService(tmp_path / "vault.json")
    service.setup_vault("correct-password")

    service.write_content({"items": [{"title": "My secret note"}]})
    service.lock_vault()

    service.unlock_vault("correct-password")
    content = service.read_content()
    assert content == {"items": [{"title": "My secret note"}]}


def test_throttle_blocks_immediate_retry_after_failure(tmp_path):
    service = VaultService(tmp_path / "vault.json")
    service.setup_vault("correct-password")
    service.lock_vault()

    with pytest.raises(IncorrectCredentialError):
        service.unlock_vault("wrong-password")

    with pytest.raises(VaultThrottledError) as exc_info:
        service.unlock_vault("correct-password")

    assert exc_info.value.retry_after_seconds > 0