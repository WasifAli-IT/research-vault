"""Tests for ExportService: building and writing Markdown/JSON/text exports."""
from __future__ import annotations

import json

import pytest

from core.database.connection import create_connection
from core.database.migration_runner import run_migrations
from core.export.export_service import ExportService
from core.export.exceptions import ExportFileExistsError
from core.services.note_service import NoteService
from core.services.research_service import ResearchService
from core.services.section_service import SectionService
from core.services.source_service import SourceService


@pytest.fixture
def export_service(tmp_path):
    database_path = tmp_path / "research.db"
    run_migrations(database_path)
    connection = create_connection(database_path)

    research_service = ResearchService(connection)
    section_service = SectionService(connection)
    note_service = NoteService(connection)
    source_service = SourceService(connection)

    return ExportService(research_service, section_service, note_service, source_service)


@pytest.fixture
def sample_research_id(export_service):
    project = export_service._research_service.create_project(
        "My Project", "A description."
    )
    export_service._section_service.add_section(project.id, "Intro", "Intro content.")
    export_service._note_service.add_note(project.id, "A quick note.")
    export_service._source_service.add_source(
        project.id, "Some Source", url="https://example.com", author="Jane Doe"
    )
    return project.id


def test_to_json_contains_all_data(export_service, sample_research_id):
    result = json.loads(export_service.to_json(sample_research_id))

    assert result["title"] == "My Project"
    assert result["description"] == "A description."
    assert result["sections"] == [{"title": "Intro", "content": "Intro content."}]
    assert result["notes"] == ["A quick note."]
    assert result["sources"][0]["title"] == "Some Source"
    assert result["sources"][0]["url"] == "https://example.com"


def test_to_markdown_contains_headings_and_content(export_service, sample_research_id):
    result = export_service.to_markdown(sample_research_id)

    assert "# My Project" in result
    assert "A description." in result
    assert "## Intro" in result
    assert "Intro content." in result
    assert "## Notes" in result
    assert "A quick note." in result
    assert "## Sources" in result
    assert "Some Source" in result


def test_to_text_contains_no_markdown_symbols(export_service, sample_research_id):
    result = export_service.to_text(sample_research_id)

    assert "My Project" in result
    assert "# My Project" not in result
    assert "Intro content." in result


def test_export_to_file_writes_content(export_service, sample_research_id, tmp_path):
    destination = tmp_path / "export.json"

    export_service.export_to_file(sample_research_id, destination, "json")

    assert destination.exists()
    content = json.loads(destination.read_text(encoding="utf-8"))
    assert content["title"] == "My Project"


def test_export_to_file_never_overwrites_existing_file(
    export_service, sample_research_id, tmp_path
):
    destination = tmp_path / "export.json"
    destination.write_text("already here")

    with pytest.raises(ExportFileExistsError):
        export_service.export_to_file(sample_research_id, destination, "json")


def test_export_to_file_rejects_unsupported_format(
    export_service, sample_research_id, tmp_path
):
    destination = tmp_path / "export.xyz"

    with pytest.raises(ValueError):
        export_service.export_to_file(sample_research_id, destination, "xyz")