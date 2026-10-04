"""Notes panel widget: lists, adds, edits, and deletes notes for a project."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.services.exceptions import ValidationError
from core.services.note_service import NoteService


class NotesPanel(QWidget):
    """Displays notes for the currently selected research project."""

    def __init__(self, note_service: NoteService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._note_service = note_service
        self._current_research_id: int | None = None

        self._add_button = QPushButton("Add Note")
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
        """Load and display notes for the given research project."""
        self._current_research_id = research_id
        self._set_enabled(True)
        self._reload_notes()

    def clear(self) -> None:
        """Reset to the empty state (no project selected)."""
        self._current_research_id = None
        self._list_widget.clear()
        self._set_enabled(False)

    def _reload_notes(self) -> None:
        self._list_widget.clear()
        notes = self._note_service.list_notes(self._current_research_id)
        for note in notes:
            preview = note.content if len(note.content) <= 60 else note.content[:60] + "..."
            item = QListWidgetItem(preview)
            item.setData(Qt.ItemDataRole.UserRole, note.id)
            self._list_widget.addItem(item)

    def _on_add_clicked(self) -> None:
        if self._current_research_id is None:
            return

        content, ok = QInputDialog.getMultiLineText(self, "Add Note", "Note content:")
        if not ok:
            return

        try:
            self._note_service.add_note(self._current_research_id, content)
        except ValidationError as error:
            QMessageBox.warning(self, "Cannot add note", str(error))
            return

        self._reload_notes()

    def _on_edit_clicked(self) -> None:
        current_item = self._list_widget.currentItem()
        if current_item is None:
            return

        note_id = current_item.data(Qt.ItemDataRole.UserRole)
        notes = self._note_service.list_notes(self._current_research_id)
        current_note = next((note for note in notes if note.id == note_id), None)
        if current_note is None:
            return

        new_content, ok = QInputDialog.getMultiLineText(
            self, "Edit Note", "Note content:", current_note.content
        )
        if not ok:
            return

        try:
            self._note_service.update_note(note_id, new_content)
        except ValidationError as error:
            QMessageBox.warning(self, "Cannot update note", str(error))
            return

        self._reload_notes()

    def _on_delete_clicked(self) -> None:
        current_item = self._list_widget.currentItem()
        if current_item is None:
            return

        confirmation = QMessageBox.question(
            self,
            "Delete Note",
            "Are you sure you want to delete this note? This cannot be undone.",
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        note_id = current_item.data(Qt.ItemDataRole.UserRole)
        self._note_service.delete_note(note_id)
        self._reload_notes()

    def _set_enabled(self, enabled: bool) -> None:
        self._add_button.setEnabled(enabled)
        self._edit_button.setEnabled(enabled)
        self._delete_button.setEnabled(enabled)
        self._list_widget.setEnabled(enabled)