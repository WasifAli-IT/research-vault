# Secure Vault: Security Design & Limitations

This document explains how the Secure Vault protects your data, and is
honest about what it does *not* protect against. Please read this before
storing anything sensitive in the vault.

## How it works

- Your vault data is encrypted with a randomly generated 256-bit **Master
  Key**, using **AES-256-GCM** (authenticated encryption).
- The Master Key itself is never stored directly. Instead, it is
  "wrapped" (encrypted) twice: once using a key derived from your
  **password**, and once using a key derived from a randomly generated
  **recovery key**. Both derivations use **Argon2id**, a slow,
  memory-hard function designed to resist brute-force and GPU/ASIC
  cracking attempts.
- Only the wrapped (encrypted) Master Key, salts, and Argon2 parameters
  are stored on disk — never your password, never your recovery key,
  never the Master Key in plain form.
- Failed unlock attempts are throttled with an exponentially increasing
  delay, to slow down brute-force guessing.

## Multiple independent vaults

You may create more than one named vault (e.g., "Personal", "Work").
Each vault is **completely independent**:

- Its own password, its own recovery key, its own Master Key, its own
  throttle/lockout state, and its own encrypted storage file.
- Unlocking, locking, or forgetting the credentials for one vault has
  **no effect whatsoever** on any other vault.

Creating multiple vaults is useful for organizing sensitive data and for
limiting how much is at risk if one vault's credentials are lost. It is
**not** a recovery mechanism: creating a new vault never restores access
to a different vault whose password and recovery key have both been
lost. Each vault must be recovered (or accepted as permanently lost) on
its own terms, exactly as described below.

## No backdoor, no bypass

There is intentionally **no "forgot password" recovery flow** beyond the
recovery key generated at setup, for any vault. No security question,
hint system, or support-based recovery exists or will be added, because
any such mechanism would itself become the weakest link in the
encryption and would undermine the guarantees above.

**If you lose both a vault's password and its recovery key, the data
stored in that vault is permanently and irreversibly unrecoverable.**
This is by design, not a bug. This applies only to that specific vault's
contents — any other vaults, and the rest of the application (your
research projects, notes, sources), are stored separately and are
completely unaffected.

## Known limitations

- **Python cannot guarantee memory is wiped.** While a vault is
  unlocked, its Master Key and decrypted content exist in your
  computer's RAM. Python's memory management (garbage collection,
  string/bytes immutability, and lack of manual memory control) means
  we cannot guarantee this data is actively overwritten/erased the
  moment the vault is locked — only that our own references to it are
  dropped, making it eligible for garbage collection. In principle,
  forensic memory analysis of a running or hibernated system could
  recover fragments of previously-unlocked vault data. This is a
  limitation of the Python language/runtime, not something this
  application can fully solve.
- **This vault does not protect against malware or keyloggers** running
  on your computer while you type your password, or against an attacker
  who already has arbitrary code execution on your machine.
- **This vault does not protect against physical access combined with
  memory/disk forensics** on a machine where a vault was recently
  unlocked (see memory limitation above).
- **Backups of a vault file are only as safe as where you store them.**
  The vault file itself is always encrypted, but if you copy it insecurely
  alongside a copy of its recovery key, that defeats its protection.

## Practical recommendations

- Choose a strong, unique password for each vault.
- Save each vault's recovery key immediately at setup time, somewhere
  durable and separate from this computer (password manager, printed
  copy, USB drive) — not just another file on the same machine.
- Only store data in a vault that specifically requires this level of
  protection.
- If you use multiple vaults, keep track of which recovery key belongs
  to which vault name — a recovery key only works for the vault it was
  generated for.