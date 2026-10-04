"""Business logic for managing categories."""

from __future__ import annotations

import sqlite3

from core.database.repositories.category_repository import CategoryRepository
from core.models.category import Category
from core.services.exceptions import ValidationError
from core.utils.time_utils import utc_now_iso


class CategoryService:
    """Validates input and coordinates category persistence."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._repository = CategoryRepository(connection)

    def create_category(self, name: str, color: str | None = None) -> Category:
        clean_name = name.strip()
        if not clean_name:
            raise ValidationError("Category name cannot be empty.")

        position = len(self._repository.list_all())
        now = utc_now_iso()

        category = Category(
            id=None,
            name=clean_name,
            color=color,
            position=position,
            created_at=now,
            updated_at=now,
        )
        return self._repository.create(category)

    def rename_category(self, category_id: int, new_name: str) -> Category:
        clean_name = new_name.strip()
        if not clean_name:
            raise ValidationError("Category name cannot be empty.")

        category = self._require_category(category_id)
        category.name = clean_name
        category.updated_at = utc_now_iso()
        self._repository.update(category)
        return category

    def delete_category(self, category_id: int) -> None:
        self._repository.delete(category_id)

    def list_categories(self) -> list[Category]:
        return self._repository.list_all()

    def _require_category(self, category_id: int) -> Category:
        category = self._repository.get_by_id(category_id)
        if category is None:
            raise ValidationError(f"Category {category_id} does not exist.")
        return category
    