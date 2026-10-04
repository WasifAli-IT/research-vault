"""Sidebar widget: search, lists research projects, and navigation buttons."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.search.search_service import SearchService
from core.services.category_service import CategoryService
from core.services.research_service import ResearchService
from ui.dialogs.category_management_dialog import CategoryManagementDialog


class ProjectListWidget(QWidget):
    """Displays search, project list, creation button, and navigation buttons.

    Signals:
        project_selected: Emitted with a research project's id whenever
            the user selects it (by clicking it, or by creating it).
        search_result_selected: Emitted with (entity_type, entity_id,
            research_id) when the user clicks a search result.
        vault_requested: Emitted when the user clicks the "Secure Vault"
            button.
        settings_requested: Emitted when the user clicks the "Settings"
            button.
    """

    project_selected = Signal(int)
    search_result_selected = Signal(str, int, int)
    vault_requested = Signal()
    settings_requested = Signal()

    def __init__(
        self,
        research_service: ResearchService,
        search_service: SearchService,
        category_service: CategoryService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._research_service = research_service
        self._search_service = search_service
        self._category_service = category_service
        self.setMinimumWidth(220)

        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Search... (press Enter)")

        self._new_button = QPushButton("New Research")

        self._category_filter_combo = QComboBox()
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filter:"))
        filter_row.addWidget(self._category_filter_combo)

        self._list_widget = QListWidget()

        self._results_list = QListWidget()
        self._results_list.setWordWrap(True)
        self._clear_search_button = QPushButton("Clear Search")

        self._categories_button = QPushButton("Categories")
        self._vault_button = QPushButton("Secure Vault")
        self._settings_button = QPushButton("Settings")

        layout = QVBoxLayout()
        layout.addWidget(self._search_box)
        layout.addWidget(self._new_button)
        layout.addLayout(filter_row)
        layout.addWidget(self._list_widget)
        layout.addWidget(self._results_list)
        layout.addWidget(self._clear_search_button)
        layout.addWidget(self._categories_button)
        layout.addWidget(self._vault_button)
        layout.addWidget(self._settings_button)
        self.setLayout(layout)

        self._search_box.returnPressed.connect(self._on_search_triggered)
        self._new_button.clicked.connect(self._on_new_research_clicked)
        self._category_filter_combo.currentIndexChanged.connect(
            self._on_category_filter_changed
        )
        self._list_widget.itemClicked.connect(self._on_item_clicked)
        self._results_list.itemClicked.connect(self._on_result_clicked)
        self._clear_search_button.clicked.connect(self._on_clear_search_clicked)
        self._categories_button.clicked.connect(self._on_categories_clicked)
        self._vault_button.clicked.connect(self.vault_requested.emit)
        self._settings_button.clicked.connect(self.settings_requested.emit)

        self._show_search_mode(False)
        self.refresh()

    def refresh(self) -> None:
        """Reload the category filter options and the project list."""
        self._reload_category_filter()
        self._reload_project_list()

    def _reload_category_filter(self) -> None:
        """Repopulate the category filter dropdown, preserving the current
        selection if that category still exists."""
        previously_selected = (
            self._category_filter_combo.currentData()
            if self._category_filter_combo.count() > 0
            else None
        )

        self._category_filter_combo.blockSignals(True)
        self._category_filter_combo.clear()
        self._category_filter_combo.addItem("All Categories", None)

        selected_index = 0
        for index, category in enumerate(
            self._category_service.list_categories(), start=1
        ):
            self._category_filter_combo.addItem(category.name, category.id)
            if (
                previously_selected is not None
                and category.id == previously_selected
            ):
                selected_index = index

        self._category_filter_combo.setCurrentIndex(selected_index)
        self._category_filter_combo.blockSignals(False)

    def _reload_project_list(self) -> None:
        """Reload the project list using the currently selected category filter."""
        self._list_widget.clear()
        category_id = self._category_filter_combo.currentData()

        if category_id is None:
            projects = self._research_service.list_projects()
        else:
            projects = self._research_service.list_projects_by_category(category_id)

        for project in projects:
            item = QListWidgetItem(project.title)
            item.setData(Qt.ItemDataRole.UserRole, project.id)
            self._list_widget.addItem(item)

    def _on_category_filter_changed(self, index: int) -> None:
        self._reload_project_list()

    def select_project(self, research_id: int) -> None:
        """Highlight the list entry matching the given research id, if present."""
        for index in range(self._list_widget.count()):
            item = self._list_widget.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == research_id:
                self._list_widget.setCurrentItem(item)
                return

    def clear_search(self) -> None:
        """Return to the normal project list view, discarding search results."""
        self._search_box.clear()
        self._results_list.clear()
        self._show_search_mode(False)

    def _on_new_research_clicked(self) -> None:
        project = self._research_service.create_project("Untitled Research")
        self.refresh()
        self.select_project(project.id)
        self.project_selected.emit(project.id)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        research_id = item.data(Qt.ItemDataRole.UserRole)
        self.project_selected.emit(research_id)

    def _on_search_triggered(self) -> None:
        query = self._search_box.text().strip()
        if not query:
            return

        results = self._search_service.search(query)

        self._results_list.clear()
        if not results:
            placeholder = QListWidgetItem("No matches found.")
            placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
            self._results_list.addItem(placeholder)
        else:
            for result in results:
                label = f"[{result.entity_type}] {result.title}\n{result.snippet}"
                item = QListWidgetItem(label)
                item.setData(
                    Qt.ItemDataRole.UserRole,
                    (result.entity_type, result.entity_id, result.research_id),
                )
                self._results_list.addItem(item)

        self._show_search_mode(True)

    def _on_result_clicked(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if data is None:
            return
        entity_type, entity_id, research_id = data
        self.search_result_selected.emit(entity_type, entity_id, research_id)

    def _on_clear_search_clicked(self) -> None:
        self.clear_search()

    def _on_categories_clicked(self) -> None:
        dialog = CategoryManagementDialog(self._category_service, self)
        dialog.exec()
        if dialog.changed:
            self.refresh()

    def _show_search_mode(self, is_search: bool) -> None:
        self._new_button.setVisible(not is_search)
        self._list_widget.setVisible(not is_search)
        self._results_list.setVisible(is_search)
        self._clear_search_button.setVisible(is_search)