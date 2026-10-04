"""Tests for low-level cryptographic primitives."""
import pytest
from cryptography.exceptions import InvalidTag

from core.security.crypto import (
    Argon2Params,
    decrypt,
    derive_key,
    encrypt,
    generate_key,
    generate_recovery_key,
    generate_salt,
)


def test_derive_key_is_deterministic_for_same_inputs():
    salt = generate_salt()
    params = Argon2Params.default()

    key_one = derive_key("correct horse battery staple", salt, params)
    key_two = derive_key("correct horse battery staple", salt, params)

    assert key_one == key_two
    assert len(key_one) == 32


def test_derive_key_differs_for_different_passwords():
    salt = generate_salt()
    params = Argon2Params.default()

    key_one = derive_key("password-one", salt, params)
    key_two = derive_key("password-two", salt, params)

    assert key_one != key_two


def test_encrypt_decrypt_roundtrip():
    key = generate_key()
    plaintext = b"secret research notes"

    nonce, ciphertext = encrypt(key, plaintext)
    decrypted = decrypt(key, nonce, ciphertext)

    assert decrypted == plaintext


def test_decrypt_with_wrong_key_fails():
    key = generate_key()
    wrong_key = generate_key()
    nonce, ciphertext = encrypt(key, b"secret data")

    with pytest.raises(InvalidTag):
        decrypt(wrong_key, nonce, ciphertext)


def test_generate_recovery_key_format():
    recovery_key = generate_recovery_key()

    groups = recovery_key.split("-")
    assert len(groups) == 6
    for group in groups:
        assert len(group) == 5