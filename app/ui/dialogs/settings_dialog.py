"""Settings dialog: lets the user view and change persisted application
preferences (theme, font size, default locations, backup preferences,
vault auto-lock duration, window size, default export format), plus an
About section."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from core.services.exceptions import ValidationError
from core.settings.settings_service import (
    MAX_AUTO_LOCK_MINUTES,
    MAX_FONT_SIZE,
    MAX_WINDOW_HEIGHT,
    MAX_WINDOW_WIDTH,
    MIN_AUTO_LOCK_MINUTES,
    MIN_FONT_SIZE,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    SettingsService,
)

APP_VERSION = "0.1.0"

_THEME_LABELS = {"light": "Light", "dark": "Dark"}
_THEME_VALUES = {label: value for value, label in _THEME_LABELS.items()}

_EXPORT_FORMAT_LABELS = {
    "json": "JSON",
    "markdown": "Markdown",
    "text": "Plain Text",
}
_EXPORT_FORMAT_VALUES = {
    label: value for value, label in _EXPORT_FORMAT_LABELS.items()
}


class SettingsDialog(QDialog):
    """Lets the user view and change persisted application settings.

    Attributes:
        settings_changed: True if the user clicked Save and the settings
            were successfully persisted. Callers can check this after
            exec() to decide whether to apply the new settings live.
    """

    def __init__(self, settings_service: SettingsService, parent=None) -> None:
        super().__init__(parent)
        self._settings_service = settings_service
        self.settings_changed = False

        self.setWindowTitle("Settings")
        self.setMinimumWidth(420)

        current = self._settings_service.get()

        form = QFormLayout()

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(list(_THEME_LABELS.values()))
        self._theme_combo.setCurrentText(_THEME_LABELS[current.theme])
        form.addRow("Theme:", self._theme_combo)

        self._font_size_spin = QSpinBox()
        self._font_size_spin.setRange(MIN_FONT_SIZE, MAX_FONT_SIZE)
        self._font_size_spin.setValue(current.font_size)
        form.addRow("Font size:", self._font_size_spin)

        self._maximized_checkbox = QCheckBox("Start maximized (recommended)")
        self._maximized_checkbox.setChecked(current.window_maximized)
        self._maximized_checkbox.toggled.connect(self._on_maximized_toggled)
        form.addRow("Window:", self._maximized_checkbox)

        self._width_spin = QSpinBox()
        self._width_spin.setRange(MIN_WINDOW_WIDTH, MAX_WINDOW_WIDTH)
        self._width_spin.setValue(current.window_width)
        self._height_spin = QSpinBox()
        self._height_spin.setRange(MIN_WINDOW_HEIGHT, MAX_WINDOW_HEIGHT)
        self._height_spin.setValue(current.window_height)
        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Width:"))
        size_row.addWidget(self._width_spin)
        size_row.addWidget(QLabel("Height:"))
        size_row.addWidget(self._height_spin)
        form.addRow("Custom size:", size_row)
        self._width_spin.setEnabled(not current.window_maximized)
        self._height_spin.setEnabled(not current.window_maximized)

        self._save_location_edit = QLineEdit(current.default_save_location)
        save_location_browse = QPushButton("Browse...")
        save_location_browse.clicked.connect(self._on_browse_save_location)
        save_location_row = QHBoxLayout()
        save_location_row.addWidget(self._save_location_edit)
        save_location_row.addWidget(save_location_browse)
        form.addRow("Default save location:", save_location_row)

        self._auto_backup_checkbox = QCheckBox("Enable automatic backups")
        self._auto_backup_checkbox.setChecked(current.auto_backup_enabled)
        form.addRow("", self._auto_backup_checkbox)

        self._auto_backup_folder_edit = QLineEdit(current.auto_backup_folder)
        auto_backup_browse = QPushButton("Browse...")
        auto_backup_browse.clicked.connect(self._on_browse_backup_folder)
        auto_backup_row = QHBoxLayout()
        auto_backup_row.addWidget(self._auto_backup_folder_edit)
        auto_backup_row.addWidget(auto_backup_browse)
        form.addRow("Automatic backup folder:", auto_backup_row)

        self._auto_lock_spin = QSpinBox()
        self._auto_lock_spin.setRange(MIN_AUTO_LOCK_MINUTES, MAX_AUTO_LOCK_MINUTES)
        self._auto_lock_spin.setValue(current.vault_auto_lock_minutes)
        self._auto_lock_spin.setSpecialValueText("Never")
        self._auto_lock_spin.setSuffix(" minutes")
        form.addRow("Vault auto-lock:", self._auto_lock_spin)

        self._export_format_combo = QComboBox()
        self._export_format_combo.addItems(list(_EXPORT_FORMAT_LABELS.values()))
        self._export_format_combo.setCurrentText(
            _EXPORT_FORMAT_LABELS[current.default_export_format]
        )
        form.addRow("Default export format:", self._export_format_combo)

        button_row = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self._on_save_clicked)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_row.addStretch()
        button_row.addWidget(save_button)
        button_row.addWidget(cancel_button)

        layout = QVBoxLayout()
        layout.addLayout(form)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(separator)
        layout.addWidget(self._build_about_section())

        layout.addLayout(button_row)
        self.setLayout(layout)

    def _build_about_section(self) -> QFrame:
        about_frame = QFrame()
        about_layout = QVBoxLayout()

        title_label = QLabel("Research Vault")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        about_layout.addWidget(title_label)

        version_label = QLabel(f"Version {APP_VERSION}")
        about_layout.addWidget(version_label)

        description_label = QLabel(
            "A private, offline-first application for organizing research "
            "projects, sections, notes, and sources, with a secure "
            "encrypted vault for sensitive items."
        )
        description_label.setWordWrap(True)
        about_layout.addWidget(description_label)

        about_frame.setLayout(about_layout)
        return about_frame

    def _on_maximized_toggled(self, checked: bool) -> None:
        self._width_spin.setEnabled(not checked)
        self._height_spin.setEnabled(not checked)

    def _on_browse_save_location(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Choose Default Save Location", self._save_location_edit.text()
        )
        if folder:
            self._save_location_edit.setText(folder)

    def _on_browse_backup_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Choose Automatic Backup Folder", self._auto_backup_folder_edit.text()
        )
        if folder:
            self._auto_backup_folder_edit.setText(folder)

    def _on_save_clicked(self) -> None:
        theme = _THEME_VALUES[self._theme_combo.currentText()]
        export_format = _EXPORT_FORMAT_VALUES[self._export_format_combo.currentText()]

        try:
            self._settings_service.update(
                theme=theme,
                font_size=self._font_size_spin.value(),
                default_save_location=self._save_location_edit.text().strip(),
                auto_backup_enabled=self._auto_backup_checkbox.isChecked(),
                auto_backup_folder=self._auto_backup_folder_edit.text().strip(),
                vault_auto_lock_minutes=self._auto_lock_spin.value(),
                default_export_format=export_format,
                window_maximized=self._maximized_checkbox.isChecked(),
                window_width=self._width_spin.value(),
                window_height=self._height_spin.value(),
            )
        except ValidationError as error:
            QMessageBox.warning(self, "Cannot Save Settings", str(error))
            return

        self.settings_changed = True
        self.accept()