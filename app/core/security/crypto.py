"""Low-level cryptographic primitives: Argon2id key derivation and
AES-256-GCM authenticated encryption.

This module is the ONLY place in the application allowed to call directly
into the argon2-cffi and cryptography libraries. All other vault code goes
through these wrappers, so the actual cryptographic choices are made in
exactly one place.
"""
from __future__ import annotations

import os
import secrets
from dataclasses import dataclass

from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY_LENGTH_BYTES = 32  # 256-bit key, required by AES-256
SALT_LENGTH_BYTES = 16
NONCE_LENGTH_BYTES = 12

# Argon2id tuning. Higher memory/time cost = slower to brute-force, but
# also slower for the legitimate user to unlock. These values target
# roughly 0.3-1 second on typical modern hardware.
ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST_KIB = 256 * 1024  # 256 MB
ARGON2_PARALLELISM = 4

RECOVERY_KEY_GROUPS = 6
RECOVERY_KEY_GROUP_LENGTH = 5
# Alphabet excludes visually ambiguous characters (0/O, 1/I) to reduce
# transcription errors when the user copies the recovery key by hand.
RECOVERY_KEY_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


@dataclass(frozen=True)
class Argon2Params:
    """Argon2id parameters used to derive a key.

    These are stored alongside the salt (in plaintext, since they are not
    secret) so the exact same derivation can be reproduced later, even if
    the default tuning changes in a future version of the application.
    """

    time_cost: int
    memory_cost_kib: int
    parallelism: int

    @classmethod
    def default(cls) -> "Argon2Params":
        return cls(
            time_cost=ARGON2_TIME_COST,
            memory_cost_kib=ARGON2_MEMORY_COST_KIB,
            parallelism=ARGON2_PARALLELISM,
        )

    def to_dict(self) -> dict:
        return {
            "time_cost": self.time_cost,
            "memory_cost_kib": self.memory_cost_kib,
            "parallelism": self.parallelism,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Argon2Params":
        return cls(
            time_cost=data["time_cost"],
            memory_cost_kib=data["memory_cost_kib"],
            parallelism=data["parallelism"],
        )


def generate_salt() -> bytes:
    """Generate a new cryptographically random salt."""
    return os.urandom(SALT_LENGTH_BYTES)


def generate_key() -> bytes:
    """Generate a new random 256-bit key (used as the vault's Master Key)."""
    return os.urandom(KEY_LENGTH_BYTES)


def generate_recovery_key() -> str:
    """Generate a human-writable random recovery key.

    Example: 'ABCDE-FGHJK-LMNPQ-RSTUV-WXYZ2-34567'
    """
    groups = [
        "".join(
            secrets.choice(RECOVERY_KEY_ALPHABET)
            for _ in range(RECOVERY_KEY_GROUP_LENGTH)
        )
        for _ in range(RECOVERY_KEY_GROUPS)
    ]
    return "-".join(groups)


def derive_key(secret: str, salt: bytes, params: Argon2Params) -> bytes:
    """Derive a 256-bit key from a password or recovery key using Argon2id.

    Args:
        secret: The password or recovery key, as typed by the user.
        salt: A random, unique-per-secret salt.
        params: Argon2id tuning parameters.

    Returns:
        A 32-byte derived key suitable for use as an AES-256 key.
    """
    return hash_secret_raw(
        secret=secret.encode("utf-8"),
        salt=salt,
        time_cost=params.time_cost,
        memory_cost=params.memory_cost_kib,
        parallelism=params.parallelism,
        hash_len=KEY_LENGTH_BYTES,
        type=Type.ID,
    )


def encrypt(key: bytes, plaintext: bytes, associated_data: bytes = b"") -> tuple[bytes, bytes]:
    """Encrypt plaintext with AES-256-GCM.

    Returns:
        A tuple of (nonce, ciphertext_with_authentication_tag).
    """
    nonce = os.urandom(NONCE_LENGTH_BYTES)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, associated_data)
    return nonce, ciphertext


def decrypt(
    key: bytes, nonce: bytes, ciphertext: bytes, associated_data: bytes = b""
) -> bytes:
    """Decrypt AES-256-GCM ciphertext.

    Raises:
        cryptography.exceptions.InvalidTag: If the key is wrong, or the
            ciphertext has been corrupted or tampered with.
    """
    return AESGCM(key).decrypt(nonce, ciphertext, associated_data)