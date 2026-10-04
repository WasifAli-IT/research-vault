"""
VaultService: setup, unlock, lock, and encrypted content access for the
Secure Vault.

The vault's entire persistent state lives in a single JSON file (the
"vault file"). That file never contains a plaintext password, recovery
key, or Master Key -- only salts, Argon2 parameters, already-encrypted
("wrapped") key material, throttle bookkeeping, and encrypted content.

Unlocking accepts either the password or the recovery key transparently:
whichever one successfully unwraps the Master Key is accepted.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from cryptography.exceptions import InvalidTag

from core.security.crypto import decrypt, encrypt, generate_key, generate_recovery_key
from core.security.exceptions import (
    IncorrectCredentialError,
    VaultAlreadySetUpError,
    VaultLockedError,
    VaultNotSetUpError,
    VaultThrottledError,
)
from core.security.throttle import (
    ThrottleState,
    record_failed_attempt,
    record_successful_attempt,
    seconds_until_unlocked,
)
from core.security.vault_keys import KeySlot, create_key_slot, unwrap_key_slot

_SCHEMA_VERSION = 1
_EMPTY_VAULT_CONTENT: dict = {"items": []}


class VaultService:
    """Manages the Secure Vault's lifecycle and encrypted content access."""

    def __init__(self, vault_file: Path) -> None:
        self._vault_file = vault_file
        self._master_key: Optional[bytes] = None

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def is_set_up(self) -> bool:
        """Return True if a vault already exists on disk."""
        return self._vault_file.exists()

    def is_unlocked(self) -> bool:
        """Return True if the Master Key is currently held in memory."""
        return self._master_key is not None

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def setup_vault(self, password: str) -> str:
        """
        Create a brand-new vault protected by the given password.

        Returns the freshly generated recovery key. This is the ONLY
        time the recovery key is available -- it is never stored in
        plaintext anywhere. The caller must show it to the user and
        instruct them to save it somewhere safe, with a clear warning
        that losing both the password and the recovery key makes the
        vault's contents permanently unrecoverable.

        Raises:
            VaultAlreadySetUpError: a vault already exists at this path.
        """
        if self.is_set_up():
            raise VaultAlreadySetUpError("A vault already exists.")

        master_key = generate_key()
        recovery_key = generate_recovery_key()

        password_slot = create_key_slot(password, master_key)
        recovery_slot = create_key_slot(recovery_key, master_key)

        content_nonce, content_ciphertext = encrypt(
            master_key, json.dumps(_EMPTY_VAULT_CONTENT).encode("utf-8")
        )

        state = {
            "schema_version": _SCHEMA_VERSION,
            "password_slot": password_slot.to_dict(),
            "recovery_slot": recovery_slot.to_dict(),
            "throttle": ThrottleState().to_dict(),
            "content_nonce": content_nonce.hex(),
            "content_ciphertext": content_ciphertext.hex(),
        }
        self._write_state(state)
        self._master_key = master_key
        return recovery_key

    # ------------------------------------------------------------------
    # Unlock / lock
    # ------------------------------------------------------------------

    def unlock_vault(self, secret: str) -> None:
        """
        Attempt to unlock the vault using either the password or the
        recovery key -- whichever one is correct is accepted.

        Raises:
            VaultNotSetUpError: no vault exists yet.
            VaultThrottledError: too many recent failed attempts.
            IncorrectCredentialError: the secret matched neither slot.
        """
        state = self._read_state()
        throttle_state = ThrottleState.from_dict(state["throttle"])

        remaining = seconds_until_unlocked(throttle_state)
        if remaining > 0:
            raise VaultThrottledError(remaining)

        password_slot = KeySlot.from_dict(state["password_slot"])
        recovery_slot = KeySlot.from_dict(state["recovery_slot"])

        master_key = self._try_unwrap(secret, password_slot)
        if master_key is None:
            master_key = self._try_unwrap(secret, recovery_slot)

        if master_key is None:
            new_throttle = record_failed_attempt(throttle_state)
            state["throttle"] = new_throttle.to_dict()
            self._write_state(state)
            raise IncorrectCredentialError("Incorrect password or recovery key.")

        new_throttle = record_successful_attempt()
        state["throttle"] = new_throttle.to_dict()
        self._write_state(state)
        self._master_key = master_key

    def lock_vault(self) -> None:
        """Discard the in-memory Master Key. Safe to call even if already locked."""
        self._master_key = None

    # ------------------------------------------------------------------
    # Content access
    # ------------------------------------------------------------------

    def read_content(self) -> dict:
        """Decrypt and return the vault's content as a dict. Requires unlock."""
        self._require_unlocked()
        state = self._read_state()
        nonce = bytes.fromhex(state["content_nonce"])
        ciphertext = bytes.fromhex(state["content_ciphertext"])
        plaintext = decrypt(self._master_key, nonce, ciphertext)
        return json.loads(plaintext.decode("utf-8"))

    def write_content(self, content: dict) -> None:
        """Encrypt and persist new vault content. Requires unlock."""
        self._require_unlocked()
        state = self._read_state()
        nonce, ciphertext = encrypt(
            self._master_key, json.dumps(content).encode("utf-8")
        )
        state["content_nonce"] = nonce.hex()
        state["content_ciphertext"] = ciphertext.hex()
        self._write_state(state)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_unlocked(self) -> None:
        if not self.is_set_up():
            raise VaultNotSetUpError("The vault has not been set up yet.")
        if self._master_key is None:
            raise VaultLockedError("The vault is locked.")

    @staticmethod
    def _try_unwrap(secret: str, slot: KeySlot) -> Optional[bytes]:
        try:
            return unwrap_key_slot(secret, slot)
        except InvalidTag:
            return None

    def _read_state(self) -> dict:
        if not self._vault_file.exists():
            raise VaultNotSetUpError("The vault has not been set up yet.")
        with self._vault_file.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write_state(self, state: dict) -> None:
        self._vault_file.parent.mkdir(parents=True, exist_ok=True)
        tmp_file = self._vault_file.with_suffix(".tmp")
        with tmp_file.open("w", encoding="utf-8") as f:
            json.dump(state, f)
        tmp_file.replace(self._vault_file)