"""Setup wizard dialog for creating a brand-new Secure Vault."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QGuiApplication

from core.security.exceptions import VaultAlreadySetUpError
from core.security.vault_service import VaultService

_MIN_PASSWORD_LENGTH = 8

_RECOVERY_WARNING = (
    "Save this recovery key somewhere safe (password manager, printed copy, "
    "USB drive). It is the ONLY backup for your password.\n\n"
    "If you lose BOTH your password AND this recovery key, your vault "
    "data is permanently and irreversibly unrecoverable. There is no "
    "'forgot password' option and no support bypass -- not even the "
    "developer of this app can recover it for you."
)


class VaultSetupDialog(QDialog):
    """Guides the user through creating a new vault: password, then recovery key."""

    def __init__(self, vault_service: VaultService, parent=None) -> None:
        super().__init__(parent)
        self._vault_service = vault_service
        self._recovery_key: str = ""

        self.setWindowTitle("Set Up Secure Vault")
        self.setMinimumWidth(480)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_password_page())
        self._stack.addWidget(self._build_recovery_page())

        layout = QVBoxLayout()
        layout.addWidget(self._stack)
        self.setLayout(layout)

    # ------------------------------------------------------------------
    # Page 1: choose password
    # ------------------------------------------------------------------

    def _build_password_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()

        intro = QLabel(
            "Create a password for your Secure Vault.\n"
            "This password will be required every time you unlock the vault."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        layout.addWidget(QLabel("Password:"))
        self._password_field = QLineEdit()
        self._password_field.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self._password_field)

        layout.addWidget(QLabel("Confirm password:"))
        self._confirm_field = QLineEdit()
        self._confirm_field.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self._confirm_field)

        self._password_error_label = QLabel("")
        self._password_error_label.setStyleSheet("color: red;")
        self._password_error_label.setWordWrap(True)
        layout.addWidget(self._password_error_label)

        button_row = QHBoxLayout()
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        create_button = QPushButton("Create Vault")
        create_button.clicked.connect(self._on_create_clicked)
        button_row.addStretch()
        button_row.addWidget(cancel_button)
        button_row.addWidget(create_button)
        layout.addLayout(button_row)

        page.setLayout(layout)
        return page

    def _on_create_clicked(self) -> None:
        password = self._password_field.text()
        confirm = self._confirm_field.text()

        if len(password) < _MIN_PASSWORD_LENGTH:
            self._password_error_label.setText(
                f"Password must be at least {_MIN_PASSWORD_LENGTH} characters."
            )
            return
        if password != confirm:
            self._password_error_label.setText("Passwords do not match.")
            return

        try:
            self._recovery_key = self._vault_service.setup_vault(password)
        except VaultAlreadySetUpError:
            self._password_error_label.setText("A vault already exists.")
            return

        self._recovery_key_display.setPlainText(self._recovery_key)
        self._stack.setCurrentIndex(1)

    # ------------------------------------------------------------------
    # Page 2: show recovery key
    # ------------------------------------------------------------------

    def _build_recovery_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()

        heading = QLabel("Your Recovery Key")
        heading.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(heading)

        warning = QLabel(_RECOVERY_WARNING)
        warning.setWordWrap(True)
        warning.setStyleSheet("color: #b00020;")
        layout.addWidget(warning)

        self._recovery_key_display = QTextEdit()
        self._recovery_key_display.setReadOnly(True)
        self._recovery_key_display.setFixedHeight(50)
        self._recovery_key_display.setStyleSheet(
            "font-family: monospace; font-size: 14px;"
        )
        layout.addWidget(self._recovery_key_display)

        action_row = QHBoxLayout()
        copy_button = QPushButton("Copy to Clipboard")
        copy_button.clicked.connect(self._on_copy_clicked)
        save_button = QPushButton("Save to File...")
        save_button.clicked.connect(self._on_save_clicked)
        action_row.addWidget(copy_button)
        action_row.addWidget(save_button)
        action_row.addStretch()
        layout.addLayout(action_row)

        self._confirm_checkbox = QCheckBox(
            "I have saved my recovery key in a safe place."
        )
        self._confirm_checkbox.stateChanged.connect(self._on_checkbox_changed)
        layout.addWidget(self._confirm_checkbox)

        button_row = QHBoxLayout()
        self._finish_button = QPushButton("Finish")
        self._finish_button.setEnabled(False)
        self._finish_button.clicked.connect(self.accept)
        button_row.addStretch()
        button_row.addWidget(self._finish_button)
        layout.addLayout(button_row)

        page.setLayout(layout)
        return page

    def _on_checkbox_changed(self) -> None:
        self._finish_button.setEnabled(self._confirm_checkbox.isChecked())

    def _on_copy_clicked(self) -> None:
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self._recovery_key)
        QMessageBox.information(self, "Copied", "Recovery key copied to clipboard.")

    def _on_save_clicked(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Recovery Key", "", "Text Files (*.txt)"
        )
        if not file_path:
            return

        from pathlib import Path

        target = Path(file_path)
        if target.exists():
            overwrite = QMessageBox.question(
                self,
                "File Already Exists",
                f"'{target.name}' already exists. Overwrite it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if overwrite != QMessageBox.StandardButton.Yes:
                return

        target.write_text(self._recovery_key, encoding="utf-8")
        QMessageBox.information(self, "Saved", f"Recovery key saved to {target}.")