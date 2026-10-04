"""Dialog for creating or editing a single Secure Vault item (title + body)."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QTextEdit,
)


class VaultItemDialog(QDialog):
    """A simple title + multi-line body form, used for both add and edit."""

    def __init__(self, title: str = "", body: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Vault Item")
        self.setMinimumWidth(420)

        self._title_field = QLineEdit(title)
        self._body_field = QTextEdit(body)

        form = QFormLayout()
        form.addRow("Title:", self._title_field)
        form.addRow("Body:", self._body_field)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

        self.setLayout(form)

    def values(self) -> dict[str, str]:
        """Return the entered title and body as a dict."""
        return {
            "title": self._title_field.text().strip(),
            "body": self._body_field.toPlainText(),
        }