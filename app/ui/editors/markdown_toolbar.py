"""Reusable toolbar that inserts Markdown syntax into a target text editor."""
from __future__ import annotations

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


def _fixed_size_button(text: str) -> QPushButton:
    """Create a QPushButton sized to fit its own text, which can never be
    compressed smaller by a surrounding layout (prevents text clipping)."""
    button = QPushButton(text)
    button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    return button


class MarkdownToolbar(QWidget):
    """A row of buttons that insert Markdown formatting into a QPlainTextEdit.

    Each button either wraps the current text selection with Markdown syntax
    (e.g. **bold**) or, if nothing is selected, inserts placeholder text that
    the user can immediately type over.

    The button row is placed inside a horizontally-scrollable area so that,
    even in a very narrow window, buttons keep their full readable text
    instead of being squeezed and clipped.
    """

    def __init__(
        self, target_editor: QPlainTextEdit, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._editor = target_editor

        self._bold_button = _fixed_size_button("Bold")
        self._italic_button = _fixed_size_button("Italic")
        self._bullet_button = _fixed_size_button("Bullet List")
        self._numbered_button = _fixed_size_button("Numbered List")
        self._quote_button = _fixed_size_button("Quote")
        self._link_button = _fixed_size_button("Link")
        self._code_button = _fixed_size_button("Code Block")

        self._buttons = [
            self._bold_button,
            self._italic_button,
            self._bullet_button,
            self._numbered_button,
            self._quote_button,
            self._link_button,
            self._code_button,
        ]

        button_row = QWidget()
        button_row_layout = QHBoxLayout()
        button_row_layout.setContentsMargins(0, 0, 0, 0)
        for button in self._buttons:
            button_row_layout.addWidget(button)
        button_row_layout.addStretch()
        button_row.setLayout(button_row_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidget(button_row)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(
            scroll_area.horizontalScrollBarPolicy().ScrollBarAsNeeded
        )
        scroll_area.setVerticalScrollBarPolicy(
            scroll_area.verticalScrollBarPolicy().ScrollBarAlwaysOff
        )
        scroll_area.setFixedHeight(button_row.sizeHint().height() + 4)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll_area)
        self.setLayout(outer_layout)

        self._bold_button.clicked.connect(
            lambda: self._wrap_selection("**", "**", "bold text")
        )
        self._italic_button.clicked.connect(
            lambda: self._wrap_selection("*", "*", "italic text")
        )
        self._bullet_button.clicked.connect(lambda: self._prefix_lines("- "))
        self._numbered_button.clicked.connect(self._insert_numbered_list)
        self._quote_button.clicked.connect(lambda: self._prefix_lines("> "))
        self._link_button.clicked.connect(self._insert_link)
        self._code_button.clicked.connect(self._insert_code_block)

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable every button in the toolbar."""
        for button in self._buttons:
            button.setEnabled(enabled)

    def _wrap_selection(self, prefix: str, suffix: str, placeholder: str) -> None:
        cursor = self._editor.textCursor()
        if cursor.hasSelection():
            selected = cursor.selectedText()
            cursor.insertText(f"{prefix}{selected}{suffix}")
        else:
            start = cursor.position()
            cursor.insertText(f"{prefix}{placeholder}{suffix}")
            cursor.setPosition(start + len(prefix))
            cursor.setPosition(
                start + len(prefix) + len(placeholder),
                QTextCursor.MoveMode.KeepAnchor,
            )
        self._editor.setTextCursor(cursor)
        self._editor.setFocus()

    def _prefix_lines(self, prefix: str) -> None:
        cursor = self._editor.textCursor()
        if not cursor.hasSelection():
            cursor.insertText(prefix)
            self._editor.setTextCursor(cursor)
            self._editor.setFocus()
            return

        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        cursor.movePosition(
            QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor
        )
        selected_text = cursor.selectedText()
        lines = selected_text.split("\u2029")
        new_text = "\n".join(f"{prefix}{line}" for line in lines)
        cursor.insertText(new_text)
        self._editor.setTextCursor(cursor)
        self._editor.setFocus()

    def _insert_numbered_list(self) -> None:
        cursor = self._editor.textCursor()
        if not cursor.hasSelection():
            cursor.insertText("1. ")
            self._editor.setTextCursor(cursor)
            self._editor.setFocus()
            return

        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        cursor.movePosition(
            QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor
        )
        selected_text = cursor.selectedText()
        lines = selected_text.split("\u2029")
        new_lines = [f"{index + 1}. {line}" for index, line in enumerate(lines)]
        cursor.insertText("\n".join(new_lines))
        self._editor.setTextCursor(cursor)
        self._editor.setFocus()

    def _insert_link(self) -> None:
        cursor = self._editor.textCursor()
        if cursor.hasSelection():
            selected = cursor.selectedText()
            cursor.insertText(f"[{selected}](https://)")
        else:
            cursor.insertText("[link text](https://)")
        self._editor.setTextCursor(cursor)
        self._editor.setFocus()

    def _insert_code_block(self) -> None:
        cursor = self._editor.textCursor()
        if cursor.hasSelection():
            selected = cursor.selectedText().replace("\u2029", "\n")
            cursor.insertText(f"```\n{selected}\n```")
        else:
            cursor.insertText("```\ncode\n```")
        self._editor.setTextCursor(cursor)
        self._editor.setFocus()