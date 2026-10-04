"""Content view widget: displays and edits a research project's title,
description, sections (table of contents + content with Markdown editing
and live preview), notes, and sources."""
from __future__ import annotations

import markdown
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from core.services.category_service import CategoryService
from core.services.exceptions import ValidationError
from core.services.research_service import ResearchService
from core.services.section_service import SectionService
from ui.editors.markdown_toolbar import MarkdownToolbar


def _fixed_size_button(text: str) -> QPushButton:
    """Create a QPushButton that sizes itself to its text and never
    stretches to fill extra layout space."""
    button = QPushButton(text)
    button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    return button


class ContentView(QWidget):
    """Shows and edits the currently selected research project's details.

    Signals:
        project_updated: Emitted after the title, description, or category
            is successfully saved, so other widgets (like the sidebar) can
            refresh themselves.
        project_deleted: Emitted after the current project has been
            permanently deleted, so other widgets can clear/refresh
            themselves.
    """

    project_updated = Signal()
    project_deleted = Signal()

    def __init__(
        self,
        research_service: ResearchService,
        section_service: SectionService,
        category_service: CategoryService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._research_service = research_service
        self._section_service = section_service
        self._category_service = category_service
        self._current_research_id: int | None = None
        self._current_section_id: int | None = None
        self._original_title: str = ""
        self._original_description: str = ""
        self._original_section_content: str = ""

        # --- Title / description ---
        self._title_edit = QLineEdit()
        self._title_edit.setStyleSheet("font-size: 20px; font-weight: bold;")

        self._description_edit = QPlainTextEdit()
        self._description_edit.setPlaceholderText("Description...")
        self._description_edit.setFixedHeight(80)

        # --- Category assignment ---
        self._category_combo = QComboBox()
        self._category_combo.setMinimumWidth(160)
        self._category_combo.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        category_row = QHBoxLayout()
        category_row.addWidget(QLabel("Category:"))
        category_row.addWidget(self._category_combo)
        category_row.addStretch()

        self._save_button = _fixed_size_button("Save")
        self._cancel_button = _fixed_size_button("Cancel")
        self._delete_button = _fixed_size_button("Delete Research")

        project_button_row = QHBoxLayout()
        project_button_row.addWidget(self._save_button)
        project_button_row.addWidget(self._cancel_button)
        project_button_row.addStretch()
        project_button_row.addWidget(self._delete_button)

        # --- Section toolbar (add/rename/delete/reorder) ---
        self._add_section_button = _fixed_size_button("Add Section")
        self._rename_section_button = _fixed_size_button("Rename")
        self._delete_section_button = _fixed_size_button("Delete")
        self._move_up_button = _fixed_size_button("Move Up")
        self._move_down_button = _fixed_size_button("Move Down")

        section_toolbar = QHBoxLayout()
        section_toolbar.addWidget(self._add_section_button)
        section_toolbar.addWidget(self._rename_section_button)
        section_toolbar.addWidget(self._delete_section_button)
        section_toolbar.addWidget(self._move_up_button)
        section_toolbar.addWidget(self._move_down_button)
        section_toolbar.addStretch()

        self._toc_list = QListWidget()

        toc_container = QVBoxLayout()
        toc_container.addLayout(section_toolbar)
        toc_container.addWidget(self._toc_list)
        toc_widget = QWidget()
        toc_widget.setLayout(toc_container)

        # --- Section content editing: Markdown toolbar + editor + live preview ---
        self._section_content_edit = QPlainTextEdit()
        self._markdown_toolbar = MarkdownToolbar(self._section_content_edit)
        self._section_preview = QTextBrowser()
        self._section_preview.setOpenExternalLinks(True)

        editor_splitter = QSplitter(Qt.Orientation.Horizontal)
        editor_splitter.addWidget(self._section_content_edit)
        editor_splitter.addWidget(self._section_preview)
        editor_splitter.setStretchFactor(0, 1)
        editor_splitter.setStretchFactor(1, 1)

        self._section_save_button = _fixed_size_button("Save Section")
        self._section_cancel_button = _fixed_size_button("Cancel Section")

        section_button_row = QHBoxLayout()
        section_button_row.addWidget(self._section_save_button)
        section_button_row.addWidget(self._section_cancel_button)
        section_button_row.addStretch()

        section_content_container = QVBoxLayout()
        section_content_container.addWidget(self._markdown_toolbar)
        section_content_container.addWidget(editor_splitter)
        section_content_container.addLayout(section_button_row)
        section_content_widget = QWidget()
        section_content_widget.setLayout(section_content_container)

        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(toc_widget)
        main_splitter.addWidget(section_content_widget)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 3)

        layout = QVBoxLayout()
        layout.addWidget(self._title_edit)
        layout.addWidget(self._description_edit)
        layout.addLayout(category_row)
        layout.addLayout(project_button_row)
        layout.addWidget(main_splitter)
        self.setLayout(layout)

        self._toc_list.itemClicked.connect(self._on_section_clicked)
        self._save_button.clicked.connect(self._on_save_clicked)
        self._cancel_button.clicked.connect(self._on_cancel_clicked)
        self._delete_button.clicked.connect(self._on_delete_project_clicked)
        self._category_combo.currentIndexChanged.connect(self._on_category_changed)
        self._add_section_button.clicked.connect(self._on_add_section_clicked)
        self._rename_section_button.clicked.connect(self._on_rename_section_clicked)
        self._delete_section_button.clicked.connect(self._on_delete_section_clicked)
        self._move_up_button.clicked.connect(self._on_move_up_clicked)
        self._move_down_button.clicked.connect(self._on_move_down_clicked)
        self._section_save_button.clicked.connect(self._on_save_section_clicked)
        self._section_cancel_button.clicked.connect(self._on_cancel_section_clicked)
        self._section_content_edit.textChanged.connect(self._update_preview)

        self._show_empty_state()

    def show_project(self, research_id: int) -> None:
        """Load and display the given research project."""
        project = self._research_service.get_project(research_id)
        if project is None:
            self._show_empty_state()
            return

        self._current_research_id = research_id
        self._original_title = project.title
        self._original_description = project.description or ""

        self._title_edit.setText(self._original_title)
        self._description_edit.setPlainText(self._original_description)
        self._reload_category_combo(project.category_id)
        self._set_project_editing_enabled(True)
        self._set_section_toolbar_enabled(True)

        self._reload_sections(select_section_id=None)

    def _reload_category_combo(self, selected_category_id: int | None) -> None:
        """Repopulate the category dropdown, selecting the project's category."""
        self._category_combo.blockSignals(True)
        self._category_combo.clear()
        self._category_combo.addItem("Uncategorized", None)

        selected_index = 0
        for index, category in enumerate(
            self._category_service.list_categories(), start=1
        ):
            self._category_combo.addItem(category.name, category.id)
            if (
                selected_category_id is not None
                and category.id == selected_category_id
            ):
                selected_index = index

        self._category_combo.setCurrentIndex(selected_index)
        self._category_combo.blockSignals(False)

    def _on_category_changed(self, index: int) -> None:
        if self._current_research_id is None:
            return
        category_id = self._category_combo.itemData(index)
        self._research_service.move_to_category(
            self._current_research_id, category_id
        )
        self.project_updated.emit()

    def _reload_sections(self, select_section_id: int | None) -> None:
        """Rebuild the table of contents, optionally re-selecting a section."""
        self._toc_list.clear()
        sections = self._section_service.list_sections(self._current_research_id)

        row_to_select = 0
        for index, section in enumerate(sections):
            item = QListWidgetItem(section.title)
            item.setData(Qt.ItemDataRole.UserRole, section.id)
            self._toc_list.addItem(item)
            if select_section_id is not None and section.id == select_section_id:
                row_to_select = index

        if sections:
            self._toc_list.setCurrentRow(row_to_select)
            self._load_section_into_editor(sections[row_to_select])
        else:
            self._current_section_id = None
            self._original_section_content = ""
            self._section_content_edit.setPlainText("")
            self._set_section_content_editing_enabled(False)

    def _load_section_into_editor(self, section) -> None:
        self._current_section_id = section.id
        self._original_section_content = section.content
        self._section_content_edit.setPlainText(section.content)
        self._set_section_content_editing_enabled(True)
        self._update_preview()

    def select_section(self, section_id: int) -> None:
        """Select and load the given section, if it exists in the current TOC."""
        for index in range(self._toc_list.count()):
            item = self._toc_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == section_id:
                self._toc_list.setCurrentRow(index)
                break

        sections = self._section_service.list_sections(self._current_research_id)
        for section in sections:
            if section.id == section_id:
                self._load_section_into_editor(section)
                return

    def _on_section_clicked(self, item: QListWidgetItem) -> None:
        section_id = item.data(Qt.ItemDataRole.UserRole)
        sections = self._section_service.list_sections(self._current_research_id)
        for section in sections:
            if section.id == section_id:
                self._load_section_into_editor(section)
                return

    def _on_save_clicked(self) -> None:
        if self._current_research_id is None:
            return

        new_title = self._title_edit.text()
        new_description = self._description_edit.toPlainText()

        try:
            self._research_service.rename_project(
                self._current_research_id, new_title
            )
            self._research_service.update_description(
                self._current_research_id, new_description
            )
        except ValidationError as error:
            QMessageBox.warning(self, "Cannot save", str(error))
            return

        self._original_title = new_title
        self._original_description = new_description
        self.project_updated.emit()

    def _on_cancel_clicked(self) -> None:
        self._title_edit.setText(self._original_title)
        self._description_edit.setPlainText(self._original_description)

    def _on_delete_project_clicked(self) -> None:
        if self._current_research_id is None:
            return

        confirmation = QMessageBox.question(
            self,
            "Delete Research",
            f"Are you sure you want to permanently delete "
            f"'{self._original_title}'?\n\n"
            "This will also delete all of its sections, notes, and "
            "sources. This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        self._research_service.delete_project(self._current_research_id)
        self._show_empty_state()
        self.project_deleted.emit()

    def _on_add_section_clicked(self) -> None:
        if self._current_research_id is None:
            return

        title, ok = QInputDialog.getText(self, "Add Section", "Section title:")
        if not ok:
            return

        try:
            section = self._section_service.add_section(
                self._current_research_id, title
            )
        except ValidationError as error:
            QMessageBox.warning(self, "Cannot add section", str(error))
            return

        self._reload_sections(select_section_id=section.id)

    def _on_rename_section_clicked(self) -> None:
        if self._current_section_id is None:
            return

        current_item = self._toc_list.currentItem()
        current_title = current_item.text() if current_item else ""

        new_title, ok = QInputDialog.getText(
            self, "Rename Section", "New title:", text=current_title
        )
        if not ok:
            return

        try:
            self._section_service.rename_section(
                self._current_section_id, new_title
            )
        except ValidationError as error:
            QMessageBox.warning(self, "Cannot rename section", str(error))
            return

        self._reload_sections(select_section_id=self._current_section_id)

    def _on_delete_section_clicked(self) -> None:
        if self._current_section_id is None:
            return

        confirmation = QMessageBox.question(
            self,
            "Delete Section",
            "Are you sure you want to delete this section? This cannot be undone.",
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        self._section_service.delete_section(self._current_section_id)
        self._reload_sections(select_section_id=None)

    def _on_move_up_clicked(self) -> None:
        self._move_current_section(offset=-1)

    def _on_move_down_clicked(self) -> None:
        self._move_current_section(offset=1)

    def _move_current_section(self, offset: int) -> None:
        if self._current_research_id is None or self._current_section_id is None:
            return

        sections = self._section_service.list_sections(self._current_research_id)
        ids = [section.id for section in sections]
        current_index = ids.index(self._current_section_id)
        new_index = current_index + offset

        if new_index < 0 or new_index >= len(ids):
            return

        ids[current_index], ids[new_index] = ids[new_index], ids[current_index]
        self._section_service.reorder_sections(self._current_research_id, ids)
        self._reload_sections(select_section_id=self._current_section_id)

    def _on_save_section_clicked(self) -> None:
        if self._current_section_id is None:
            return

        new_content = self._section_content_edit.toPlainText()
        self._section_service.update_content(self._current_section_id, new_content)
        self._original_section_content = new_content

    def _on_cancel_section_clicked(self) -> None:
        self._section_content_edit.setPlainText(self._original_section_content)

    def _update_preview(self) -> None:
        """Re-render the Markdown preview from the current editor text."""
        text = self._section_content_edit.toPlainText()
        html = markdown.markdown(text, extensions=["fenced_code", "tables"])
        self._section_preview.setHtml(html)

    def _set_project_editing_enabled(self, enabled: bool) -> None:
        self._title_edit.setEnabled(enabled)
        self._description_edit.setEnabled(enabled)
        self._save_button.setEnabled(enabled)
        self._cancel_button.setEnabled(enabled)
        self._delete_button.setEnabled(enabled)
        self._category_combo.setEnabled(enabled)

    def _set_section_toolbar_enabled(self, enabled: bool) -> None:
        self._add_section_button.setEnabled(enabled)
        self._rename_section_button.setEnabled(enabled)
        self._delete_section_button.setEnabled(enabled)
        self._move_up_button.setEnabled(enabled)
        self._move_down_button.setEnabled(enabled)

    def _set_section_content_editing_enabled(self, enabled: bool) -> None:
        self._section_content_edit.setEnabled(enabled)
        self._section_save_button.setEnabled(enabled)
        self._section_cancel_button.setEnabled(enabled)
        self._markdown_toolbar.set_enabled(enabled)

    def _show_empty_state(self) -> None:
        self._current_research_id = None
        self._current_section_id = None
        self._original_title = ""
        self._original_description = ""
        self._original_section_content = ""
        self._title_edit.setText("No research selected")
        self._description_edit.setPlainText(
            "Select a research project from the sidebar, or create a new one."
        )
        self._category_combo.blockSignals(True)
        self._category_combo.clear()
        self._category_combo.addItem("Uncategorized", None)
        self._category_combo.blockSignals(False)
        self._set_project_editing_enabled(False)
        self._set_section_toolbar_enabled(False)
        self._toc_list.clear()
        self._section_content_edit.setPlainText("")
        self._section_preview.setHtml("")
        self._set_section_content_editing_enabled(False)