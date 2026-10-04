from core.config.app_paths import resolve_app_paths


def test_resolve_app_paths_creates_directories() -> None:
    paths = resolve_app_paths()

    assert paths.data_dir.exists()
    assert paths.vault_dir.exists()
    assert paths.backups_dir.exists()
    assert paths.config_dir.exists()
    