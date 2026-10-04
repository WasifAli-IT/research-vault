"""Tests for ImportService: recreating a project from a JSON export file."""
from __future__ import annotations

import json

import pytest

from core.database.connection import create_connection
from core.database.migration_runner import run_migrations
from core.export.exceptions import ImportError_
from core.export.export_service import ExportService
from core.export.import_service import ImportService
from core.services.note_service import NoteService
from core.services.research_service import ResearchService
from core.services.section_service import SectionService
from core.services.source_service import SourceService


@pytest.fixture
def services(tmp_path):
    database_path = tmp_path / "research.db"
    run_migrations(database_path)
    connection = create_connection(database_path)

    research_service = ResearchService(connection)
    section_service = SectionService(connection)
    note_service = NoteService(connection)
    source_service = SourceService(connection)

    export_service = ExportService(
        research_service, section_service, note_service, source_service
    )
    import_service = ImportService(
        research_service, section_service, note_service, source_service
    )
    return research_service, section_service, note_service, source_service, export_service, import_service


def test_import_round_trip_recreates_project(services, tmp_path):
    research_service, section_service, note_service, source_service, export_service, import_service = services

    project = research_service.create_project("Original", "Description here.")
    section_service.add_section(project.id, "Intro", "Intro content.")
    note_service.add_note(project.id, "A note.")
    source_service.add_source(project.id, "A Source", url="https://example.com")

    export_path = tmp_path / "export.json"
    export_service.export_to_file(project.id, export_path, "json")

    new_project_id = import_service.import_from_file(export_path)

    assert new_project_id != project.id
    new_project = research_service.get_project(new_project_id)
    assert new_project.title == "Original"
    assert new_project.description == "Description here."

    sections = section_service.list_sections(new_project_id)
    assert len(sections) == 1
    assert sections[0].title == "Intro"

    notes = note_service.list_notes(new_project_id)
    assert len(notes) == 1
    assert notes[0].content == "A note."

    sources = source_service.list_sources(new_project_id)
    assert len(sources) == 1
    assert sources[0].title == "A Source"


def test_import_missing_file_raises(services, tmp_path):
    *_, import_service = services
    missing_path = tmp_path / "does_not_exist.json"

    with pytest.raises(ImportError_):
        import_service.import_from_file(missing_path)


def test_import_invalid_json_raises(services, tmp_path):
    *_, import_service = services
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("not valid json {{{")

    with pytest.raises(ImportError_):
        import_service.import_from_file(bad_file)


def test_import_missing_title_raises(services, tmp_path):
    *_, import_service = services
    bad_file = tmp_path / "bad.json"
    bad_file.write_text(json.dumps({"description": "no title here"}))

    with pytest.raises(ImportError_):
        import_service.import_from_file(bad_file)


def test_import_malformed_section_raises(services, tmp_path):
    *_, import_service = services
    bad_file = tmp_path / "bad.json"
    bad_file.write_text(json.dumps({"title": "Ok", "sections": [{"content": "no title"}]}))

    with pytest.raises(ImportError_):
        import_service.import_from_file(bad_file)