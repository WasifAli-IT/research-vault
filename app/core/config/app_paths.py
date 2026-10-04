"""
Centralized filesystem path resolution for the application.

This is the ONLY module in the codebase allowed to know about
OS-specific storage locations. Every other module must obtain
paths through the AppPaths class instead of hard-coding them.

This design also makes future Android support easier: a different
AppPaths implementation (or platformdirs' Android support) can be
swapped in without touching any other code.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from platformdirs import PlatformDirs

_APP_NAME = "ResearchVault"
_APP_AUTHOR = "ResearchVault"  # used by platformdirs on Windows


@dataclass(frozen=True)
class AppPaths:
    """Resolved, guaranteed-to-exist application directories."""

    data_dir: Path
    config_dir: Path
    cache_dir: Path
    log_dir: Path

    @property
    def database_file(self) -> Path:
        return self.data_dir / "research.db"

    @property
    def vault_dir(self) -> Path:
        return self.data_dir / "vault"

    @property
    def backups_dir(self) -> Path:
        return self.data_dir / "backups"

    @property
    def settings_file(self) -> Path:
        return self.config_dir / "settings.json"

    @property
    def log_file(self) -> Path:
        return self.log_dir / "app.log"


def resolve_app_paths() -> AppPaths:
    """
    Resolve all application directories for the current OS and
    ensure they exist on disk. Safe to call multiple times.
    """
    dirs = PlatformDirs(appname=_APP_NAME, appauthor=_APP_AUTHOR)

    data_dir = Path(dirs.user_data_dir)
    config_dir = Path(dirs.user_config_dir)
    cache_dir = Path(dirs.user_cache_dir)
    log_dir = Path(dirs.user_log_dir)

    paths = AppPaths(
        data_dir=data_dir,
        config_dir=config_dir,
        cache_dir=cache_dir,
        log_dir=log_dir,
    )

    for directory in (
        paths.data_dir,
        paths.config_dir,
        paths.cache_dir,
        paths.log_dir,
        paths.vault_dir,
        paths.backups_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    return paths