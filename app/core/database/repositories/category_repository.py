"""Repository for Category persistence."""

from __future__ import annotations

import sqlite3

from core.models.category import Category


class CategoryRepository:
    """Handles all database access for categories."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create(self, category: Category) -> Category:
        cursor = self._connection.execute(
            """
            INSERT INTO categories (name, color, position, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                category.name,
                category.color,
                category.position,
                category.created_at,
                category.updated_at,
            ),
        )
        self._connection.commit()
        category.id = cursor.lastrowid
        return category

    def get_by_id(self, category_id: int) -> Category | None:
        row = self._connection.execute(
            "SELECT * FROM categories WHERE id = ?;", (category_id,)
        ).fetchone()
        return self._row_to_model(row) if row else None

    def list_all(self) -> list[Category]:
        rows = self._connection.execute(
            "SELECT * FROM categories ORDER BY position ASC, name ASC;"
        ).fetchall()
        return [self._row_to_model(row) for row in rows]

    def update(self, category: Category) -> None:
        self._connection.execute(
            """
            UPDATE categories
            SET name = ?, color = ?, position = ?, updated_at = ?
            WHERE id = ?;
            """,
            (
                category.name,
                category.color,
                category.position,
                category.updated_at,
                category.id,
            ),
        )
        self._connection.commit()

    def delete(self, category_id: int) -> None:
        self._connection.execute(
            "DELETE FROM categories WHERE id = ?;", (category_id,)
        )
        self._connection.commit()

    @staticmethod
    def _row_to_model(row: sqlite3.Row) -> Category:
        return Category(
            id=row["id"],
            name=row["name"],
            color=row["color"],
            position=row["position"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    