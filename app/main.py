"""
Application entry point (composition root).

This module is responsible for wiring together the application's
top-level dependencies (paths, logging, database) and launching the
Qt event loop. Business logic must never live here.
"""

from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from app_context import AppContext
from core.config.app_paths import resolve_app_paths
from core.utils.logging_setup import configure_logging
from ui.main_window import MainWindow

logger = logging.getLogger(__name__)


def main() -> int:
    paths = resolve_app_paths()
    configure_logging(paths.log_file)

    logger.info("Starting Research Vault application")
    logger.info("Data directory: %s", paths.data_dir)

    context = AppContext.create(paths.database_file)

    app = QApplication(sys.argv)
    app.setApplicationName("Research Vault")

    window = MainWindow(context)
    window.show()

    exit_code = app.exec()

    context.close()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())