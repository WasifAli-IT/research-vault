"""Tests for SettingsService: defaults, persistence, and validation."""
from pathlib import Path

import pytest

from core.services.exceptions import ValidationError
from core.settings.settings_service import AppSettings, SettingsService


def test_defaults_when_no_file_exists(tmp_path: Path) -> None:
    service = SettingsService(tmp_path / "settings.json")
    assert service.get() == AppSettings()


def test_save_and_load_round_trip(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    service = SettingsService(settings_path)
    service.update(theme="dark", font_size=16)

    reloaded = SettingsService(settings_path)
    assert reloaded.get().theme == "dark"
    assert reloaded.get().font_size == 16


def test_corrupt_file_falls_back_to_defaults(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    settings_path.write_text("not valid json{{{", encoding="utf-8")

    service = SettingsService(settings_path)
    assert service.get() == AppSettings()


def test_update_theme_invalid_raises(tmp_path: Path) -> None:
    service = SettingsService(tmp_path / "settings.json")
    with pytest.raises(ValidationError):
        service.update(theme="purple")


def test_update_font_size_invalid_raises(tmp_path: Path) -> None:
    service = SettingsService(tmp_path / "settings.json")
    with pytest.raises(ValidationError):
        service.update(font_size=999)


def test_update_vault_auto_lock_minutes_invalid_raises(tmp_path: Path) -> None:
    service = SettingsService(tmp_path / "settings.json")
    with pytest.raises(ValidationError):
        service.update(vault_auto_lock_minutes=-1)


def test_update_default_export_format_invalid_raises(tmp_path: Path) -> None:
    service = SettingsService(tmp_path / "settings.json")
    with pytest.raises(ValidationError):
        service.update(default_export_format="pdf")


def test_update_unknown_field_raises(tmp_path: Path) -> None:
    service = SettingsService(tmp_path / "settings.json")
    with pytest.raises(ValidationError):
        service.update(not_a_real_field=True)


def test_update_persists_multiple_fields(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    service = SettingsService(settings_path)
    service.update(
        auto_backup_enabled=True,
        auto_backup_folder=str(tmp_path),
        vault_auto_lock_minutes=10,
        default_export_format="markdown",
        default_save_location=str(tmp_path),
    )

    reloaded = SettingsService(settings_path).get()
    assert reloaded.auto_backup_enabled is True
    assert reloaded.auto_backup_folder == str(tmp_path)
    assert reloaded.vault_auto_lock_minutes == 10
    assert reloaded.default_export_format == "markdown"
    assert reloaded.default_save_location == str(tmp_path)


def test_ignores_unknown_keys_in_file(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        '{"theme": "dark", "some_future_field": 123}', encoding="utf-8"
    )
    service = SettingsService(settings_path)
    assert service.get().theme == "dark"


def test_update_window_width_invalid_raises(tmp_path: Path) -> None:
    service = SettingsService(tmp_path / "settings.json")
    with pytest.raises(ValidationError):
        service.update(window_width=100)


def test_update_window_height_invalid_raises(tmp_path: Path) -> None:
    service = SettingsService(tmp_path / "settings.json")
    with pytest.raises(ValidationError):
        service.update(window_height=100)


def test_update_window_settings_round_trip(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    service = SettingsService(settings_path)
    service.update(window_maximized=False, window_width=1400, window_height=900)

    reloaded = SettingsService(settings_path).get()
    assert reloaded.window_maximized is False
    assert reloaded.window_width == 1400
    assert reloaded.window_height == 900