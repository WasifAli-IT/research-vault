"""Tests for Master Key wrapping via password/recovery-key slots."""
import pytest
from cryptography.exceptions import InvalidTag

from core.security.crypto import generate_key
from core.security.vault_keys import create_key_slot, unwrap_key_slot


def test_wrap_and_unwrap_roundtrip():
    master_key = generate_key()
    slot = create_key_slot("my-password", master_key)

    recovered = unwrap_key_slot("my-password", slot)

    assert recovered == master_key


def test_unwrap_with_wrong_secret_fails():
    master_key = generate_key()
    slot = create_key_slot("correct-password", master_key)

    with pytest.raises(InvalidTag):
        unwrap_key_slot("wrong-password", slot)


def test_slot_serialization_roundtrip():
    from core.security.vault_keys import KeySlot

    master_key = generate_key()
    slot = create_key_slot("my-password", master_key)

    restored = KeySlot.from_dict(slot.to_dict())
    recovered = unwrap_key_slot("my-password", restored)

    assert recovered == master_key