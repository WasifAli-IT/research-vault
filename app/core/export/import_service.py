"""
ImportService: recreates a research project from a previously exported
JSON file (see ExportService.to_json / export_to_file).
"""
from __future__ import annotations

import json
from pathlib import Path

from core.export.exceptions import ImportError_
from core.services.note_service import NoteService
from core.services.research_service import ResearchService
from core.services.section_service import SectionService
from core.services.source_service import SourceService


class ImportService:
    """Imports a research project from our JSON export format."""

    def __init__(
        self,
        research_service: ResearchService,
        section_service: SectionService,
        note_service: NoteService,
        source_service: SourceService,
    ) -> None:
        self._research_service = research_service
        self._section_service = section_service
        self._note_service = note_service
        self._source_service = source_service

    def import_from_file(self, source_path: Path) -> int:
        """
        Read a JSON export file and create a brand-new research project
        from it. Never modifies or overwrites an existing project.

        Returns:
            The id of the newly created research project.

        Raises:
            ImportError_: the file is missing, not valid JSON, or missing
                required fields.
        """
        if not source_path.exists():
            raise ImportError_(f"File not found: '{source_path}'")

        try:
            raw_text = source_path.read_text(encoding="utf-8")
            data = json.loads(raw_text)
        except (OSError, json.JSONDecodeError) as error:
            raise ImportError_(f"Could not read '{source_path}' as JSON: {error}") from error

        self._validate_shape(data)

        project = self._research_service.create_project(
            data["title"], data.get("description", "")
        )

        for section in data.get("sections", []):
            self._section_service.add_section(
                project.id, section["title"], section.get("content", "")
            )

        for note_content in data.get("notes", []):
            self._note_service.add_note(project.id, note_content)

        for source in data.get("sources", []):
            self._source_service.add_source(
                project.id,
                source["title"],
                url=source.get("url"),
                author=source.get("author"),
                publication_date=source.get("publication_date"),
                notes=source.get("notes", ""),
            )

        return project.id

    @staticmethod
    def _validate_shape(data: object) -> None:
        if not isinstance(data, dict):
            raise ImportError_("Import file must contain a JSON object.")
        if "title" not in data or not isinstance(data["title"], str) or not data["title"].strip():
            raise ImportError_("Import file is missing a valid 'title' field.")

        for section in data.get("sections", []):
            if not isinstance(section, dict) or "title" not in section:
                raise ImportError_("Import file has a malformed section entry.")

        for source in data.get("sources", []):
            if not isinstance(source, dict) or "title" not in source:
                raise ImportError_("Import file has a malformed source entry.")