"""Unlock dialog for an existing, locked Secure Vault."""
from __future__ import annotations

import math

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from core.security.exceptions import IncorrectCredentialError, VaultThrottledError
from core.security.vault_service import VaultService


class VaultUnlockDialog(QDialog):
    """Prompts for a password or recovery key to unlock an existing vault."""

    def __init__(self, vault_service: VaultService, parent=None) -> None:
        super().__init__(parent)
        self._vault_service = vault_service
        self._remaining_seconds = 0

        self.setWindowTitle("Unlock Secure Vault")
        self.setMinimumWidth(400)

        layout = QVBoxLayout()

        intro = QLabel("Enter your vault password or recovery key:")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self._secret_field = QLineEdit()
        self._secret_field.setEchoMode(QLineEdit.EchoMode.Password)
        self._secret_field.returnPressed.connect(self._on_unlock_clicked)
        layout.addWidget(self._secret_field)

        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: red;")
        self._error_label.setWordWrap(True)
        layout.addWidget(self._error_label)

        button_row = QHBoxLayout()
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        self._unlock_button = QPushButton("Unlock")
        self._unlock_button.clicked.connect(self._on_unlock_clicked)
        button_row.addStretch()
        button_row.addWidget(cancel_button)
        button_row.addWidget(self._unlock_button)
        layout.addLayout(button_row)

        self.setLayout(layout)

        self._countdown_timer = QTimer(self)
        self._countdown_timer.setInterval(1000)
        self._countdown_timer.timeout.connect(self._on_countdown_tick)

    def _on_unlock_clicked(self) -> None:
        secret = self._secret_field.text()
        if not secret:
            self._error_label.setText("Please enter your password or recovery key.")
            return

        try:
            self._vault_service.unlock_vault(secret)
        except VaultThrottledError as error:
            self._start_throttle_countdown(error.retry_after_seconds)
            return
        except IncorrectCredentialError:
            self._error_label.setText("Incorrect password or recovery key.")
            self._secret_field.clear()
            return

        self.accept()

    def _start_throttle_countdown(self, seconds: float) -> None:
        self._remaining_seconds = math.ceil(seconds)
        self._secret_field.setEnabled(False)
        self._unlock_button.setEnabled(False)
        self._update_countdown_label()
        self._countdown_timer.start()

    def _on_countdown_tick(self) -> None:
        self._remaining_seconds -= 1
        if self._remaining_seconds <= 0:
            self._countdown_timer.stop()
            self._secret_field.setEnabled(True)
            self._unlock_button.setEnabled(True)
            self._error_label.setText("")
            self._secret_field.setFocus()
        else:
            self._update_countdown_label()

    def _update_countdown_label(self) -> None:
        self._error_label.setText(
            f"Too many failed attempts. Try again in {self._remaining_seconds} seconds."
        )