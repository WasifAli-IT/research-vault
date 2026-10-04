"""Dialog for choosing, creating, or deleting a named Secure Vault."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core.security.vault_manager import VaultManager
from core.services.exceptions import ValidationError


class VaultSelectionDialog(QDialog):
    """Lets the user pick an existing vault, create a new one, or delete one."""

    def __init__(self, vault_manager: VaultManager, parent=None) -> None:
        super().__init__(parent)
        self._vault_manager = vault_manager
        self.selected_vault_name: str | None = None

        self.setWindowTitle("Secure Vault")
        self.setMinimumWidth(400)

        layout = QVBoxLayout()

        intro = QLabel("Choose a vault to open, or create a new one:")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self._list_widget = QListWidget()
        self._list_widget.itemDoubleClicked.connect(self._on_open_clicked)
        layout.addWidget(self._list_widget)

        button_row = QHBoxLayout()
        new_button = QPushButton("New Vault...")
        new_button.clicked.connect(self._on_new_clicked)
        delete_button = QPushButton("Delete Vault...")
        delete_button.clicked.connect(self._on_delete_clicked)
        button_row.addWidget(new_button)
        button_row.addWidget(delete_button)
        button_row.addStretch()
        layout.addLayout(button_row)

        bottom_row = QHBoxLayout()
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        open_button = QPushButton("Open")
        open_button.clicked.connect(self._on_open_clicked)
        bottom_row.addStretch()
        bottom_row.addWidget(cancel_button)
        bottom_row.addWidget(open_button)
        layout.addLayout(bottom_row)

        self.setLayout(layout)
        self._refresh_list()

    def _refresh_list(self) -> None:
        self._list_widget.clear()
        self._list_widget.addItems(self._vault_manager.list_vault_names())

    def _on_open_clicked(self) -> None:
        current = self._list_widget.currentItem()
        if current is None:
            QMessageBox.information(self, "No Selection", "Select a vault to open.")
            return
        self.selected_vault_name = current.text()
        self.accept()

    def _on_new_clicked(self) -> None:
        name, ok = QInputDialog.getText(self, "New Vault", "Vault name:")
        if not ok or not name.strip():
            return
        try:
            self._vault_manager.create_vault_service(name)
        except ValidationError as error:
            QMessageBox.warning(self, "Cannot Create Vault", str(error))
            return
        self.selected_vault_name = name.strip()
        self.accept()

    def _on_delete_clicked(self) -> None:
        current = self._list_widget.currentItem()
        if current is None:
            QMessageBox.information(self, "No Selection", "Select a vault to delete.")
            return
        name = current.text()
        confirm = QMessageBox.question(
            self,
            "Delete Vault",
            f"Permanently delete the vault '{name}' and everything inside it?\n\n"
            "This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self._vault_manager.delete_vault(name)
        self._refresh_list()