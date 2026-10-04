"""Dialog for creating or editing a source's fields."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QPlainTextEdit,
)


class SourceDialog(QDialog):
    """A small form dialog for entering a source's title, URL, author,
    publication date, and notes.
    """

    def __init__(
        self,
        title: str = "",
        url: str = "",
        author: str = "",
        publication_date: str = "",
        notes: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Source")

        self._title_edit = QLineEdit(title)
        self._url_edit = QLineEdit(url)
        self._author_edit = QLineEdit(author)
        self._date_edit = QLineEdit(publication_date)
        self._date_edit.setPlaceholderText("YYYY-MM-DD (optional)")
        self._notes_edit = QPlainTextEdit(notes)
        self._notes_edit.setFixedHeight(80)

        form = QFormLayout()
        form.addRow("Title:", self._title_edit)
        form.addRow("URL:", self._url_edit)
        form.addRow("Author:", self._author_edit)
        form.addRow("Publication date:", self._date_edit)
        form.addRow("Notes:", self._notes_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

        self.setLayout(form)

    def values(self) -> dict[str, str]:
        """Return the entered field values as a dictionary of strings."""
        return {
            "title": self._title_edit.text(),
            "url": self._url_edit.text(),
            "author": self._author_edit.text(),
            "publication_date": self._date_edit.text(),
            "notes": self._notes_edit.toPlainText(),
        }