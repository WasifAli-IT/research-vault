"""Business logic for managing research projects."""

from __future__ import annotations

import sqlite3

from core.database.repositories.research_repository import ResearchRepository
from core.models.research_project import ResearchProject
from core.services.exceptions import ValidationError
from core.utils.time_utils import utc_now_iso


class ResearchService:
    """Validates input and coordinates research project persistence."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._repository = ResearchRepository(connection)

    def create_project(
        self,
        title: str,
        description: str = "",
        category_id: int | None = None,
    ) -> ResearchProject:
        clean_title = title.strip()
        if not clean_title:
            raise ValidationError("Research title cannot be empty.")

        position = len(self._repository.list_all())
        now = utc_now_iso()

        project = ResearchProject(
            id=None,
            title=clean_title,
            description=description.strip(),
            category_id=category_id,
            is_favorite=False,
            position=position,
            created_at=now,
            updated_at=now,
        )
        return self._repository.create(project)

    def get_project(self, project_id: int) -> ResearchProject | None:
        return self._repository.get_by_id(project_id)

    def list_projects(self) -> list[ResearchProject]:
        return self._repository.list_all()

    def list_projects_by_category(self, category_id: int | None) -> list[ResearchProject]:
        return self._repository.list_by_category(category_id)

    def rename_project(self, project_id: int, new_title: str) -> ResearchProject:
        clean_title = new_title.strip()
        if not clean_title:
            raise ValidationError("Research title cannot be empty.")

        project = self._require_project(project_id)
        project.title = clean_title
        project.updated_at = utc_now_iso()
        self._repository.update(project)
        return project

    def update_description(self, project_id: int, new_description: str) -> ResearchProject:
        project = self._require_project(project_id)
        project.description = new_description.strip()
        project.updated_at = utc_now_iso()
        self._repository.update(project)
        return project

    def move_to_category(self, project_id: int, category_id: int | None) -> ResearchProject:
        project = self._require_project(project_id)
        project.category_id = category_id
        project.updated_at = utc_now_iso()
        self._repository.update(project)
        return project

    def delete_project(self, project_id: int) -> None:
        self._repository.delete(project_id)

    def _require_project(self, project_id: int) -> ResearchProject:
        project = self._repository.get_by_id(project_id)
        if project is None:
            raise ValidationError(f"Research project {project_id} does not exist.")
        return project
    