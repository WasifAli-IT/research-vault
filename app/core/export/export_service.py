"""
ExportService: builds Markdown, JSON, and plain-text representations of a
research project, and writes them to disk.
"""
from __future__ import annotations

import json
from pathlib import Path

from core.export.exceptions import ExportFileExistsError
from core.services.note_service import NoteService
from core.services.research_service import ResearchService
from core.services.section_service import SectionService
from core.services.source_service import SourceService

SUPPORTED_FORMATS = ("json", "markdown", "text")


class ExportService:
    """Builds and writes exports of a research project in multiple formats."""

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

    def build_export_data(self, research_id: int) -> dict:
        """Gather a project's full data into a plain dict, shared by all formats."""
        project = self._research_service.get_project(research_id)
        sections = self._section_service.list_sections(research_id)
        notes = self._note_service.list_notes(research_id)
        sources = self._source_service.list_sources(research_id)

        return {
            "title": project.title,
            "description": project.description,
            "sections": [
                {"title": section.title, "content": section.content}
                for section in sections
            ],
            "notes": [note.content for note in notes],
            "sources": [
                {
                    "title": source.title,
                    "url": source.url,
                    "author": source.author,
                    "publication_date": source.publication_date,
                    "notes": source.notes,
                }
                for source in sources
            ],
        }

    def to_json(self, research_id: int) -> str:
        """Return a JSON string representation of the project."""
        data = self.build_export_data(research_id)
        return json.dumps(data, indent=2)

    def to_markdown(self, research_id: int) -> str:
        """Return a Markdown string representation of the project."""
        data = self.build_export_data(research_id)
        lines: list[str] = [f"# {data['title']}", ""]
        if data["description"]:
            lines.append(data["description"])
            lines.append("")

        for section in data["sections"]:
            lines.append(f"## {section['title']}")
            lines.append("")
            if section["content"]:
                lines.append(section["content"])
                lines.append("")

        if data["notes"]:
            lines.append("## Notes")
            lines.append("")
            for note in data["notes"]:
                lines.append(f"- {note}")
            lines.append("")

        if data["sources"]:
            lines.append("## Sources")
            lines.append("")
            for source in data["sources"]:
                parts = [source["title"]]
                if source["author"]:
                    parts.append(f"by {source['author']}")
                if source["publication_date"]:
                    parts.append(f"({source['publication_date']})")
                if source["url"]:
                    parts.append(f"- {source['url']}")
                lines.append(f"- {' '.join(parts)}")
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    def to_text(self, research_id: int) -> str:
        """Return a plain-text (no Markdown symbols) representation of the project."""
        data = self.build_export_data(research_id)
        lines: list[str] = [data["title"], "=" * len(data["title"]), ""]
        if data["description"]:
            lines.append(data["description"])
            lines.append("")

        for section in data["sections"]:
            lines.append(section["title"])
            lines.append("-" * len(section["title"]))
            lines.append("")
            if section["content"]:
                lines.append(section["content"])
                lines.append("")

        if data["notes"]:
            lines.append("Notes")
            lines.append("-----")
            lines.append("")
            for note in data["notes"]:
                lines.append(f"* {note}")
            lines.append("")

        if data["sources"]:
            lines.append("Sources")
            lines.append("-------")
            lines.append("")
            for source in data["sources"]:
                parts = [source["title"]]
                if source["author"]:
                    parts.append(f"by {source['author']}")
                if source["publication_date"]:
                    parts.append(f"({source['publication_date']})")
                if source["url"]:
                    parts.append(f"- {source['url']}")
                lines.append(f"* {' '.join(parts)}")
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    def export_to_file(
        self, research_id: int, destination_path: Path, export_format: str
    ) -> None:
        """
        Write a project's export to destination_path in the given format.

        Args:
            export_format: one of "json", "markdown", "text".

        Raises:
            ValueError: export_format is not supported.
            ExportFileExistsError: destination_path already exists. Exports
                are never silently overwritten.
        """
        if export_format not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported export format: '{export_format}'")
        if destination_path.exists():
            raise ExportFileExistsError(
                f"A file already exists at '{destination_path}'. "
                "Choose a different location or delete it first."
            )

        if export_format == "json":
            content = self.to_json(research_id)
        elif export_format == "markdown":
            content = self.to_markdown(research_id)
        else:
            content = self.to_text(research_id)

        destination_path.parent.mkdir(parents=True, exist_ok=True)
        destination_path.write_text(content, encoding="utf-8")