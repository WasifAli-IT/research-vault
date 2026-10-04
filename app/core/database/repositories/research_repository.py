"""Repository for ResearchProject persistence."""

from __future__ import annotations

import sqlite3

from core.models.research_project import ResearchProject


class ResearchRepository:
    """Handles all database access for research projects."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create(self, project: ResearchProject) -> ResearchProject:
        cursor = self._connection.execute(
            """
            INSERT INTO research_projects
                (title, description, category_id, is_favorite, position, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                project.title,
                project.description,
                project.category_id,
                int(project.is_favorite),
                project.position,
                project.created_at,
                project.updated_at,
            ),
        )
        self._connection.commit()
        project.id = cursor.lastrowid
        return project

    def get_by_id(self, project_id: int) -> ResearchProject | None:
        row = self._connection.execute(
            "SELECT * FROM research_projects WHERE id = ?;", (project_id,)
        ).fetchone()
        return self._row_to_model(row) if row else None

    def list_all(self) -> list[ResearchProject]:
        rows = self._connection.execute(
            "SELECT * FROM research_projects ORDER BY position ASC, title ASC;"
        ).fetchall()
        return [self._row_to_model(row) for row in rows]

    def list_by_category(self, category_id: int | None) -> list[ResearchProject]:
        if category_id is None:
            rows = self._connection.execute(
                "SELECT * FROM research_projects WHERE category_id IS NULL "
                "ORDER BY position ASC, title ASC;"
            ).fetchall()
        else:
            rows = self._connection.execute(
                "SELECT * FROM research_projects WHERE category_id = ? "
                "ORDER BY position ASC, title ASC;",
                (category_id,),
            ).fetchall()
        return [self._row_to_model(row) for row in rows]

    def update(self, project: ResearchProject) -> None:
        self._connection.execute(
            """
            UPDATE research_projects
            SET title = ?, description = ?, category_id = ?, is_favorite = ?,
                position = ?, updated_at = ?
            WHERE id = ?;
            """,
            (
                project.title,
                project.description,
                project.category_id,
                int(project.is_favorite),
                project.position,
                project.updated_at,
                project.id,
            ),
        )
        self._connection.commit()

    def delete(self, project_id: int) -> None:
        self._connection.execute(
            "DELETE FROM research_projects WHERE id = ?;", (project_id,)
        )
        self._connection.commit()

    @staticmethod
    def _row_to_model(row: sqlite3.Row) -> ResearchProject:
        return ResearchProject(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            category_id=row["category_id"],
            is_favorite=bool(row["is_favorite"]),
            position=row["position"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    