"""Sources panel widget: lists, adds, edits, and deletes sources for a project."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.services.exceptions import ValidationError
from core.services.source_service import SourceService
from ui.dialogs.source_dialog import SourceDialog


class SourcesPanel(QWidget):
    """Displays sources for the currently selected research project."""

    def __init__(
        self, source_service: SourceService, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._source_service = source_service
        self._current_research_id: int | None = None

        self._add_button = QPushButton("Add Source")
        self._edit_button = QPushButton("Edit")
        self._delete_button = QPushButton("Delete")

        toolbar = QHBoxLayout()
        toolbar.addWidget(self._add_button)
        toolbar.addWidget(self._edit_button)
        toolbar.addWidget(self._delete_button)
        toolbar.addStretch()

        self._list_widget = QListWidget()

        layout = QVBoxLayout()
        layout.addLayout(toolbar)
        layout.addWidget(self._list_widget)
        self.setLayout(layout)

        self._add_button.clicked.connect(self._on_add_clicked)
        self._edit_button.clicked.connect(self._on_edit_clicked)
        self._delete_button.clicked.connect(self._on_delete_clicked)

        self._set_enabled(False)

    def show_project(self, research_id: int) -> None:
        """Load and display sources for the given research project."""
        self._current_research_id = research_id
        self._set_enabled(True)
        self._reload_sources()

    def clear(self) -> None:
        """Reset to the empty state (no project selected)."""
        self._current_research_id = None
        self._list_widget.clear()
        self._set_enabled(False)

    def _reload_sources(self) -> None:
        self._list_widget.clear()
        sources = self._source_service.list_sources(self._current_research_id)
        for source in sources:
            item = QListWidgetItem(source.title)
            item.setData(Qt.ItemDataRole.UserRole, source.id)
            self._list_widget.addItem(item)

    def _on_add_clicked(self) -> None:
        if self._current_research_id is None:
            return

        dialog = SourceDialog(parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        values = dialog.values()
        try:
            self._source_service.add_source(
                self._current_research_id,
                title=values["title"],
                url=values["url"] or None,
                author=values["author"] or None,
                publication_date=values["publication_date"] or None,
                notes=values["notes"],
            )
        except ValidationError as error:
            QMessageBox.warning(self, "Cannot add source", str(error))
            return

        self._reload_sources()

    def _on_edit_clicked(self) -> None:
        current_item = self._list_widget.currentItem()
        if current_item is None:
            return

        source_id = current_item.data(Qt.ItemDataRole.UserRole)
        sources = self._source_service.list_sources(self._current_research_id)
        current_source = next((s for s in sources if s.id == source_id), None)
        if current_source is None:
            return

        dialog = SourceDialog(
            title=current_source.title,
            url=current_source.url or "",
            author=current_source.author or "",
            publication_date=current_source.publication_date or "",
            notes=current_source.notes or "",
            parent=self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        values = dialog.values()
        try:
            self._source_service.update_source(
                source_id,
                title=values["title"],
                url=values["url"] or None,
                author=values["author"] or None,
                publication_date=values["publication_date"] or None,
                notes=values["notes"],
            )
        except ValidationError as error:
            QMessageBox.warning(self, "Cannot update source", str(error))
            return

        self._reload_sources()

    def _on_delete_clicked(self) -> None:
        current_item = self._list_widget.currentItem()
        if current_item is None:
            return

        confirmation = QMessageBox.question(
            self,
            "Delete Source",
            "Are you sure you want to delete this source? This cannot be undone.",
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        source_id = current_item.data(Qt.ItemDataRole.UserRole)
        self._source_service.delete_source(source_id)
        self._reload_sources()

    def _set_enabled(self, enabled: bool) -> None:
        self._add_button.setEnabled(enabled)
        self._edit_button.setEnabled(enabled)
        self._delete_button.setEnabled(enabled)
        self._list_widget.setEnabled(enabled)