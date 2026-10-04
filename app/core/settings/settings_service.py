"""Persisted application settings (theme, font size, backup preferences,
vault auto-lock duration, window size, and other user preferences).

Settings are stored as plain JSON on disk. No secrets are stored here,
so no encryption is needed. Writes are atomic (write to a temporary
file, then replace) to avoid corrupting the settings file if the
application is closed mid-write.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from core.services.exceptions import ValidationError

VALID_THEMES = ("light", "dark")
VALID_EXPORT_FORMATS = ("json", "markdown", "text")
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 32
MIN_AUTO_LOCK_MINUTES = 0  # 0 means "never auto-lock"
MAX_AUTO_LOCK_MINUTES = 240
MIN_WINDOW_WIDTH = 800
MAX_WINDOW_WIDTH = 7680
MIN_WINDOW_HEIGHT = 600
MAX_WINDOW_HEIGHT = 4320


@dataclass
class AppSettings:
    """A single snapshot of all user-configurable application settings."""

    theme: str = "light"
    font_size: int = 13
    default_save_location: str = ""
    auto_backup_enabled: bool = False
    auto_backup_folder: str = ""
    vault_auto_lock_minutes: int = 5
    default_export_format: str = "json"
    window_maximized: bool = True
    window_width: int = 1200
    window_height: int = 800


class SettingsService:
    """Loads, validates, and persists :class:`AppSettings`."""

    def __init__(self, settings_path: Path) -> None:
        self._settings_path = settings_path
        self._settings = self._load()

    def get(self) -> AppSettings:
        """Return the current in-memory settings snapshot."""
        return self._settings

    def update(self, **changes: object) -> AppSettings:
        """Validate and apply the given field changes, then persist them.

        Only fields defined on AppSettings may be passed. Raises
        ValidationError if any field name or value is invalid.
        """
        unknown_fields = set(changes) - set(asdict(self._settings))
        if unknown_fields:
            raise ValidationError(
                f"Unknown setting(s): {', '.join(sorted(unknown_fields))}"
            )

        candidate = replace(self._settings, **changes)
        self._validate(candidate)
        self._settings = candidate
        self._save()
        return self._settings

    def _validate(self, settings: AppSettings) -> None:
        if settings.theme not in VALID_THEMES:
            raise ValidationError(f"Theme must be one of: {', '.join(VALID_THEMES)}")

        if not isinstance(settings.font_size, int) or not (
            MIN_FONT_SIZE <= settings.font_size <= MAX_FONT_SIZE
        ):
            raise ValidationError(
                f"Font size must be an integer between {MIN_FONT_SIZE} and {MAX_FONT_SIZE}."
            )

        if not isinstance(settings.vault_auto_lock_minutes, int) or not (
            MIN_AUTO_LOCK_MINUTES <= settings.vault_auto_lock_minutes <= MAX_AUTO_LOCK_MINUTES
        ):
            raise ValidationError(
                "Vault auto-lock minutes must be an integer between "
                f"{MIN_AUTO_LOCK_MINUTES} and {MAX_AUTO_LOCK_MINUTES}."
            )

        if settings.default_export_format not in VALID_EXPORT_FORMATS:
            raise ValidationError(
                f"Default export format must be one of: {', '.join(VALID_EXPORT_FORMATS)}"
            )

        if not isinstance(settings.window_width, int) or not (
            MIN_WINDOW_WIDTH <= settings.window_width <= MAX_WINDOW_WIDTH
        ):
            raise ValidationError(
                f"Window width must be an integer between {MIN_WINDOW_WIDTH} and {MAX_WINDOW_WIDTH}."
            )

        if not isinstance(settings.window_height, int) or not (
            MIN_WINDOW_HEIGHT <= settings.window_height <= MAX_WINDOW_HEIGHT
        ):
            raise ValidationError(
                f"Window height must be an integer between {MIN_WINDOW_HEIGHT} and {MAX_WINDOW_HEIGHT}."
            )

    def _load(self) -> AppSettings:
        if not self._settings_path.exists():
            return AppSettings()

        try:
            raw_text = self._settings_path.read_text(encoding="utf-8")
            data = json.loads(raw_text)
            defaults = asdict(AppSettings())
            # Ignore unknown keys, fill in missing keys with defaults, so
            # older/newer settings files never crash the app.
            merged = {key: data.get(key, default) for key, default in defaults.items()}
            candidate = AppSettings(**merged)
            self._validate(candidate)
            return candidate
        except (json.JSONDecodeError, OSError, TypeError, ValidationError):
            return AppSettings()

    def _save(self) -> None:
        self._settings_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self._settings_path.with_suffix(".tmp")
        temp_path.write_text(
            json.dumps(asdict(self._settings), indent=2), encoding="utf-8"
        )
        temp_path.replace(self._settings_path)