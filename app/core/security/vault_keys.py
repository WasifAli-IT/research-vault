"""Key wrapping: the vault's Master Key is independently wrapped by the
user's password and by their recovery key (envelope encryption)."""
from __future__ import annotations

from dataclasses import dataclass

from core.security.crypto import (
    Argon2Params,
    decrypt,
    derive_key,
    encrypt,
    generate_salt,
)


@dataclass
class KeySlot:
    """One way of unlocking the Master Key (e.g. via password or recovery
    key). Contains no plaintext secrets, only what is needed to verify a
    provided secret and, if correct, recover the Master Key."""

    salt: bytes
    params: Argon2Params
    nonce: bytes
    wrapped_key: bytes

    def to_dict(self) -> dict:
        return {
            "salt": self.salt.hex(),
            "params": self.params.to_dict(),
            "nonce": self.nonce.hex(),
            "wrapped_key": self.wrapped_key.hex(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "KeySlot":
        return cls(
            salt=bytes.fromhex(data["salt"]),
            params=Argon2Params.from_dict(data["params"]),
            nonce=bytes.fromhex(data["nonce"]),
            wrapped_key=bytes.fromhex(data["wrapped_key"]),
        )


def create_key_slot(secret: str, master_key: bytes) -> KeySlot:
    """Wrap the Master Key using a secret (a password or recovery key)."""
    salt = generate_salt()
    params = Argon2Params.default()
    derived = derive_key(secret, salt, params)
    nonce, wrapped_key = encrypt(derived, master_key)
    return KeySlot(salt=salt, params=params, nonce=nonce, wrapped_key=wrapped_key)


def unwrap_key_slot(secret: str, slot: KeySlot) -> bytes:
    """Attempt to recover the Master Key from a key slot using a secret.

    Raises:
        cryptography.exceptions.InvalidTag: If the secret is incorrect.
    """
    derived = derive_key(secret, slot.salt, slot.params)
    return decrypt(derived, slot.nonce, slot.wrapped_key)