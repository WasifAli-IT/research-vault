"""Theme and font application: applies the user-selected theme (light or
dark) and font size to the whole running application."""
from __future__ import annotations

from PySide6.QtWidgets import QApplication

_DARK_STYLESHEET = """
QWidget {
    background-color: #2b2b2b;
    color: #e0e0e0;
}
QLineEdit, QPlainTextEdit, QTextBrowser, QListWidget, QComboBox, QSpinBox {
    background-color: #3c3c3c;
    color: #e0e0e0;
    border: 1px solid #555555;
}
QPushButton {
    background-color: #454545;
    color: #e0e0e0;
    border: 1px solid #5a5a5a;
    padding: 4px 8px;
}
QPushButton:hover {
    background-color: #555555;
}
QPushButton:disabled {
    color: #888888;
}
QMenuBar, QMenu {
    background-color: #2b2b2b;
    color: #e0e0e0;
}
QMenuBar::item:selected, QMenu::item:selected {
    background-color: #555555;
}
QTabWidget::pane {
    border: 1px solid #555555;
}
QTabBar::tab {
    background: #3c3c3c;
    color: #e0e0e0;
    padding: 6px 12px;
}
QTabBar::tab:selected {
    background: #555555;
}
QSplitter::handle {
    background-color: #444444;
}
"""


def apply_theme(app: QApplication, theme: str) -> None:
    """Apply the given theme ('light' or 'dark') to the whole application.

    'light' clears any custom stylesheet, restoring the operating
    system's default look.
    """
    if theme == "dark":
        app.setStyleSheet(_DARK_STYLESHEET)
    else:
        app.setStyleSheet("")


def apply_font_size(app: QApplication, font_size: int) -> None:
    """Apply the given base font point size to the whole application."""
    font = app.font()
    font.setPointSize(font_size)
    app.setFont(font)