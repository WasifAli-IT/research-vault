"""Dialog for creating, renaming, and deleting categories."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core.services.category_service import CategoryService
from core.services.exceptions import ValidationError


class CategoryManagementDialog(QDialog):
    """Lets the user create, rename, and delete categories."""

    def __init__(self, category_service: CategoryService, parent=None) -> None:
        super().__init__(parent)
        self._category_service = category_service
        self.changed = False

        self.setWindowTitle("Manage Categories")
        self.setMinimumWidth(360)

        layout = QVBoxLayout()

        intro = QLabel("Create, rename, or delete categories:")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self._list_widget = QListWidget()
        layout.addWidget(self._list_widget)

        button_row = QHBoxLayout()
        add_button = QPushButton("Add")
        add_button.clicked.connect(self._on_add_clicked)
        rename_button = QPushButton("Rename")
        rename_button.clicked.connect(self._on_rename_clicked)
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self._on_delete_clicked)
        button_row.addWidget(add_button)
        button_row.addWidget(rename_button)
        button_row.addWidget(delete_button)
        button_row.addStretch()
        layout.addLayout(button_row)

        bottom_row = QHBoxLayout()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        bottom_row.addStretch()
        bottom_row.addWidget(close_button)
        layout.addLayout(bottom_row)

        self.setLayout(layout)
        self._refresh_list()

    def _refresh_list(self) -> None:
        self._list_widget.clear()
        for category in self._category_service.list_categories():
            item = QListWidgetItem(category.name)
            item.setData(1000, category.id)
            self._list_widget.addItem(item)

    def _selected_category_id(self) -> int | None:
        current = self._list_widget.currentItem()
        if current is None:
            return None
        return current.data(1000)

    def _on_add_clicked(self) -> None:
        name, ok = QInputDialog.getText(self, "Add Category", "Category name:")
        if not ok or not name.strip():
            return
        try:
            self._category_service.create_category(name)
        except ValidationError as error:
            QMessageBox.warning(self, "Cannot Add Category", str(error))
            return
        self.changed = True
        self._refresh_list()

    def _on_rename_clicked(self) -> None:
        category_id = self._selected_category_id()
        if category_id is None:
            QMessageBox.information(self, "No Selection", "Select a category to rename.")
            return
        current_item = self._list_widget.currentItem()
        new_name, ok = QInputDialog.getText(
            self, "Rename Category", "New name:", text=current_item.text()
        )
        if not ok or not new_name.strip():
            return
        try:
            self._category_service.rename_category(category_id, new_name)
        except ValidationError as error:
            QMessageBox.warning(self, "Cannot Rename Category", str(error))
            return
        self.changed = True
        self._refresh_list()

    def _on_delete_clicked(self) -> None:
        category_id = self._selected_category_id()
        if category_id is None:
            QMessageBox.information(self, "No Selection", "Select a category to delete.")
            return
        current_item = self._list_widget.currentItem()
        confirm = QMessageBox.question(
            self,
            "Delete Category",
            f"Delete the category '{current_item.text()}'?\n\n"
            "Projects in this category will become uncategorized; they "
            "will not be deleted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self._category_service.delete_category(category_id)
        self.changed = True
        self._refresh_list()