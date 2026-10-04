# Research Vault

A private, offline-first desktop application for organizing research projects — with a built-in encrypted vault for sensitive notes. Built with Python and PySide6.

## Features

- **Organize research projects**: each project has a title, description, and unlimited sections with long-form Markdown content, notes, and sources/references.
- **Full Markdown editor**: headings, bold, italic, bullet/numbered lists, quotes, links, and code blocks, with live preview.
- **Fast local search**: full-text search across titles, descriptions, section headings/content, notes, and sources (SQLite FTS5, with automatic fallback to LIKE-based search if FTS5 is unavailable).
- **Categories**: organize projects into user-defined categories/folders.
- **Secure Vault**: a separate, independently encrypted space protected by a password, using industry-standard cryptography:
  - Argon2id for password-based key derivation
  - AES-256-GCM authenticated encryption
  - Envelope encryption (a random Master Key, wrapped separately by your password and by a recovery key)
  - Brute-force throttling with increasing delay between failed attempts
  - Configurable auto-lock after inactivity
  - Multiple independent vaults supported
  - See [SECURITY.md](SECURITY.md) for full details and limitations.
- **Backups**: create and restore full database backups locally, with automatic backups on close if enabled.
- **Export/Import**: export individual projects to Markdown, JSON, or plain text; import projects from this app's own JSON export format.
- **Settings**: theme (light/dark), font size, window size, default save location, backup preferences, vault auto-lock duration, export format.
- **Fully offline**: no network access, no cloud sync, no telemetry. All data stays on your computer.

## Screenshots

*(Add screenshots here — e.g. `docs/screenshots/main-window.png`)*

## Installation

### Option 1: Windows Installer (recommended for most users)

Download the latest `ResearchVault-Setup.exe` from the [Releases](../../releases) page and run it. The installer lets you choose your install location and creates Start Menu shortcuts.

> Note: since this installer isn't code-signed, Windows SmartScreen may show a warning on first run. Click "More info" → "Run anyway" to proceed.

### Option 2: Run from source

Requirements: Python 3.14+

```bash
git clone https://github.com/WasifAli-IT/research-vault.git
cd research-vault
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python app/main.py