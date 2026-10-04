"""Main application window: menu bar + sidebar + tabbed content view shell."""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import QEvent, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QTabWidget,
    QWidget,
)
from app_context import AppContext
from core.export.exceptions import ImportError_
from core.security.vault_item_service import VaultItemService
from ui.content.content_view import ContentView
from ui.content.notes_panel import NotesPanel
from ui.content.sources_panel import SourcesPanel
from ui.dialogs.settings_dialog import SettingsDialog
from ui.dialogs.vault_selection_dialog import VaultSelectionDialog
from ui.dialogs.vault_setup_dialog import VaultSetupDialog
from ui.dialogs.vault_unlock_dialog import VaultUnlockDialog
from ui.sidebar.project_list_widget import ProjectListWidget
from ui.theme import apply_font_size, apply_theme
from ui.vault.vault_content_view import VaultContentView

_EXPORT_FORMAT_FILTERS = {
    "json": "JSON Files (*.json)",
    "markdown": "Markdown Files (*.md)",
    "text": "Text Files (*.txt)",
}


class MainWindow(QMainWindow):
    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self._context = context
        self._vault_content_view: VaultContentView | None = None
        self._active_vault_service = None
        self._active_vault_name: str | None = None
        self._current_research_id: int | None = None
        self._auto_lock_enabled = True
        self.setWindowTitle("Research Vault")

        self._apply_appearance_settings()

        self._sidebar = ProjectListWidget(
            context.research_service, context.search_service, context.category_service
        )
        self._content_view = ContentView(
            context.research_service, context.section_service, context.category_service
        )
        self._notes_panel = NotesPanel(context.note_service)
        self._sources_panel = SourcesPanel(context.source_service)
        self._tabs = QTabWidget()
        self._tabs.addTab(self._content_view, "Sections")
        self._tabs.addTab(self._notes_panel, "Notes")
        self._tabs.addTab(self._sources_panel, "Sources")
        splitter = QSplitter()
        splitter.addWidget(self._sidebar)
        splitter.addWidget(self._tabs)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([280, 920])
        central_widget = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(splitter)
        layout.setContentsMargins(0, 0, 0, 0)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self._build_menu_bar()

        self._sidebar.project_selected.connect(self._content_view.show_project)
        self._sidebar.project_selected.connect(self._notes_panel.show_project)
        self._sidebar.project_selected.connect(self._sources_panel.show_project)
        self._sidebar.project_selected.connect(self._set_current_research_id)
        self._content_view.project_updated.connect(self._sidebar.refresh)
        self._content_view.project_deleted.connect(self._on_project_deleted)
        self._sidebar.search_result_selected.connect(self._on_search_result_selected)
        self._sidebar.vault_requested.connect(self._on_vault_requested)
        self._sidebar.settings_requested.connect(self._on_settings_requested)

        self._auto_lock_timer = QTimer(self)
        self._auto_lock_timer.setSingleShot(True)
        self._auto_lock_timer.timeout.connect(self._on_auto_lock_timeout)
        self._apply_auto_lock_setting()

        app_instance = QApplication.instance()
        if app_instance is not None:
            app_instance.installEventFilter(self)

    # ------------------------------------------------------------------
    # Window show / sizing
    # ------------------------------------------------------------------

    def show(self) -> None:
        """Show the window, applying the configured maximized/custom size."""
        self._apply_window_settings()

    def _apply_window_settings(self) -> None:
        settings = self._context.settings_service.get()
        if settings.window_maximized:
            super().showMaximized()
        else:
            super().showNormal()
            self.resize(settings.window_width, settings.window_height)

    # ------------------------------------------------------------------
    # Menu bar
    # ------------------------------------------------------------------

    def _build_menu_bar(self) -> None:
        file_menu = self.menuBar().addMenu("&File")

        backup_action = file_menu.addAction("Backup Database...")
        backup_action.triggered.connect(self._on_backup_database)

        restore_action = file_menu.addAction("Restore Database...")
        restore_action.triggered.connect(self._on_restore_database)

        file_menu.addSeparator()

        export_action = file_menu.addAction("Export Project...")
        export_action.triggered.connect(self._on_export_project)

        import_action = file_menu.addAction("Import Project...")
        import_action.triggered.connect(self._on_import_project)

    def _set_current_research_id(self, research_id: int) -> None:
        self._current_research_id = research_id

    def _on_project_deleted(self) -> None:
        self._current_research_id = None
        self._sidebar.refresh()
        self._notes_panel.clear()
        self._sources_panel.clear()

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def _on_settings_requested(self) -> None:
        dialog = SettingsDialog(self._context.settings_service, self)
        if dialog.exec() == dialog.DialogCode.Accepted and dialog.settings_changed:
            self._apply_auto_lock_setting()
            self._apply_appearance_settings()
            self._apply_window_settings()

    def _apply_appearance_settings(self) -> None:
        """Apply the current theme and font size to the whole application."""
        app_instance = QApplication.instance()
        if app_instance is None:
            return
        settings = self._context.settings_service.get()
        apply_theme(app_instance, settings.theme)
        apply_font_size(app_instance, settings.font_size)

    def _apply_auto_lock_setting(self) -> None:
        """Read the configured vault auto-lock duration and apply it to the
        auto-lock timer. A value of 0 minutes disables auto-lock entirely."""
        minutes = self._context.settings_service.get().vault_auto_lock_minutes
        if minutes <= 0:
            self._auto_lock_enabled = False
            self._auto_lock_timer.stop()
        else:
            self._auto_lock_enabled = True
            self._auto_lock_timer.setInterval(minutes * 60 * 1000)
            if (
                self._active_vault_service is not None
                and self._active_vault_service.is_unlocked()
            ):
                self._auto_lock_timer.start()

    # ------------------------------------------------------------------
    # Backup / Restore
    # ------------------------------------------------------------------

    def _default_save_directory(self) -> str:
        return self._context.settings_service.get().default_save_location

    def _on_backup_database(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Backup Database", self._default_save_directory(), "Database Files (*.db)"
        )
        if not file_path:
            return

        target = Path(file_path)
        if target.exists():
            confirm = QMessageBox.question(
                self,
                "File Already Exists",
                f"'{target.name}' already exists. Overwrite it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return
            target.unlink()

        try:
            self._context.backup_service.create_backup(target)
        except Exception as error:
            QMessageBox.warning(self, "Backup Failed", str(error))
            return

        QMessageBox.information(self, "Backup Complete", f"Database backed up to:\n{target}")

    def _on_restore_database(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Restore Database", self._default_save_directory(), "Database Files (*.db)"
        )
        if not file_path:
            return

        confirm = QMessageBox.warning(
            self,
            "Restore Database",
            "Restoring will REPLACE all current research projects, notes, "
            "and sources with the contents of the selected backup. This "
            "cannot be undone.\n\n"
            "The application will close after restoring; reopen it "
            "afterward to see the restored data.\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self._context.connection.close()
        try:
            self._context.backup_service.restore_backup(Path(file_path))
        except Exception as error:
            QMessageBox.critical(self, "Restore Failed", str(error))
        else:
            QMessageBox.information(
                self, "Restore Complete", "Restore complete. The application will now close."
            )
        QApplication.instance().quit()

    # ------------------------------------------------------------------
    # Export / Import
    # ------------------------------------------------------------------

    def _on_export_project(self) -> None:
        if self._current_research_id is None:
            QMessageBox.information(
                self, "No Project Selected", "Select a research project first."
            )
            return

        default_format = self._context.settings_service.get().default_export_format
        preferred_filter = _EXPORT_FORMAT_FILTERS.get(
            default_format, _EXPORT_FORMAT_FILTERS["json"]
        )

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Project",
            self._default_save_directory(),
            "JSON Files (*.json);;Markdown Files (*.md);;Text Files (*.txt)",
            preferred_filter,
        )
        if not file_path:
            return

        if "JSON" in selected_filter:
            export_format = "json"
        elif "Markdown" in selected_filter:
            export_format = "markdown"
        else:
            export_format = "text"

        target = Path(file_path)
        if target.exists():
            confirm = QMessageBox.question(
                self,
                "File Already Exists",
                f"'{target.name}' already exists. Overwrite it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return
            target.unlink()

        try:
            self._context.export_service.export_to_file(
                self._current_research_id, target, export_format
            )
        except Exception as error:
            QMessageBox.warning(self, "Export Failed", str(error))
            return

        QMessageBox.information(self, "Export Complete", f"Project exported to:\n{target}")

    def _on_import_project(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Project", self._default_save_directory(), "JSON Files (*.json)"
        )
        if not file_path:
            return

        try:
            new_research_id = self._context.import_service.import_from_file(Path(file_path))
        except ImportError_ as error:
            QMessageBox.warning(self, "Import Failed", str(error))
            return

        self._sidebar.refresh()
        self._sidebar.select_project(new_research_id)
        self._content_view.show_project(new_research_id)
        self._notes_panel.show_project(new_research_id)
        self._sources_panel.show_project(new_research_id)
        self._current_research_id = new_research_id

        QMessageBox.information(self, "Import Complete", "Project imported successfully.")

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def _on_search_result_selected(self, entity_type: str, entity_id: int, research_id: int) -> None:
        self._sidebar.clear_search()
        self._sidebar.select_project(research_id)
        self._content_view.show_project(research_id)
        self._notes_panel.show_project(research_id)
        self._sources_panel.show_project(research_id)
        self._current_research_id = research_id
        if entity_type == "section":
            self._tabs.setCurrentWidget(self._content_view)
            self._content_view.select_section(entity_id)
        elif entity_type == "note":
            self._tabs.setCurrentWidget(self._notes_panel)
        elif entity_type == "source":
            self._tabs.setCurrentWidget(self._sources_panel)
        else:
            self._tabs.setCurrentWidget(self._content_view)

    # ------------------------------------------------------------------
    # Vault
    # ------------------------------------------------------------------

    def eventFilter(self, watched, event):
        if event.type() in (
            QEvent.Type.MouseMove,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.KeyPress,
        ):
            if (
                self._auto_lock_enabled
                and self._active_vault_service is not None
                and self._active_vault_service.is_unlocked()
            ):
                self._auto_lock_timer.start()
        return super().eventFilter(watched, event)

    def _on_vault_requested(self) -> None:
        if self._active_vault_service is not None and self._active_vault_service.is_unlocked():
            self._show_vault_tab()
            return

        selection_dialog = VaultSelectionDialog(self._context.vault_manager, self)
        if selection_dialog.exec() != selection_dialog.DialogCode.Accepted:
            return
        vault_name = selection_dialog.selected_vault_name
        if vault_name is None:
            return

        if self._context.vault_manager.vault_exists(vault_name):
            vault_service = self._context.vault_manager.get_vault_service(vault_name)
            unlock_dialog = VaultUnlockDialog(vault_service, self)
            if unlock_dialog.exec() != unlock_dialog.DialogCode.Accepted:
                return
        else:
            vault_service = self._context.vault_manager.create_vault_service(vault_name)
            setup_dialog = VaultSetupDialog(vault_service, self)
            if setup_dialog.exec() != setup_dialog.DialogCode.Accepted:
                return

        self._active_vault_service = vault_service
        self._active_vault_name = vault_name
        self._show_vault_tab()

    def _show_vault_tab(self) -> None:
        if self._vault_content_view is None:
            vault_item_service = VaultItemService(self._active_vault_service)
            self._vault_content_view = VaultContentView(vault_item_service)
            self._vault_content_view.vault_locked.connect(self._on_vault_locked)
            self._tabs.addTab(self._vault_content_view, f"Vault: {self._active_vault_name}")
        else:
            self._vault_content_view.refresh()
        self._tabs.setCurrentWidget(self._vault_content_view)
        if self._auto_lock_enabled:
            self._auto_lock_timer.start()

    def _on_vault_locked(self) -> None:
        if self._active_vault_service is not None:
            self._active_vault_service.lock_vault()
        self._auto_lock_timer.stop()
        if self._vault_content_view is not None:
            index = self._tabs.indexOf(self._vault_content_view)
            if index != -1:
                self._tabs.removeTab(index)
            self._vault_content_view.deleteLater()
            self._vault_content_view = None
        self._active_vault_service = None
        self._active_vault_name = None
        self._tabs.setCurrentWidget(self._content_view)

    def _on_auto_lock_timeout(self) -> None:
        if self._active_vault_service is not None and self._active_vault_service.is_unlocked():
            self._on_vault_locked()
            QMessageBox.information(
                self,
                "Vault Locked",
                "The Secure Vault was locked automatically due to inactivity.",
            )

    # ------------------------------------------------------------------
    # Automatic backup on close
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:
        self._perform_auto_backup_if_enabled()
        super().closeEvent(event)

    def _perform_auto_backup_if_enabled(self) -> None:
        """Silently create a timestamped backup in the configured folder
        when the app closes, if automatic backups are enabled. This is
        best-effort: if it fails, the app still closes normally rather
        than blocking shutdown."""
        settings = self._context.settings_service.get()
        if not settings.auto_backup_enabled:
            return

        folder_text = settings.auto_backup_folder.strip()
        if not folder_text:
            return

        folder = Path(folder_text)
        if not folder.exists() or not folder.is_dir():
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        destination = folder / f"research_vault_backup_{timestamp}.db"

        try:
            self._context.backup_service.create_backup(destination)
        except Exception:
            pass