import pytest

from core.services.research_service import ResearchService
from core.services.section_service import SectionService
from core.services.note_service import NoteService
from core.services.source_service import SourceService
from core.services.exceptions import ValidationError


def test_create_project(connection) -> None:
    service = ResearchService(connection)
    project = service.create_project("Artificial Intelligence", "Overview of AI")
    assert project.id is not None
    assert project.title == "Artificial Intelligence"


def test_create_project_rejects_empty_title(connection) -> None:
    service = ResearchService(connection)
    with pytest.raises(ValidationError):
        service.create_project("   ")


def test_rename_and_update_description(connection) -> None:
    service = ResearchService(connection)
    project = service.create_project("AI")

    renamed = service.rename_project(project.id, "Artificial Intelligence")
    assert renamed.title == "Artificial Intelligence"

    updated = service.update_description(project.id, "New description")
    assert updated.description == "New description"


def test_add_sections_and_reorder(connection) -> None:
    research_service = ResearchService(connection)
    section_service = SectionService(connection)

    project = research_service.create_project("AI")
    first = section_service.add_section(project.id, "History")
    second = section_service.add_section(project.id, "Machine Learning")

    sections = section_service.list_sections(project.id)
    assert [s.title for s in sections] == ["History", "Machine Learning"]

    section_service.reorder_sections(project.id, [second.id, first.id])
    reordered = section_service.list_sections(project.id)
    assert [s.title for s in reordered] == ["Machine Learning", "History"]


def test_reorder_rejects_mismatched_ids(connection) -> None:
    research_service = ResearchService(connection)
    section_service = SectionService(connection)

    project = research_service.create_project("AI")
    section_service.add_section(project.id, "History")

    with pytest.raises(ValidationError):
        section_service.reorder_sections(project.id, [9999])


def test_add_note_and_source(connection) -> None:
    research_service = ResearchService(connection)
    note_service = NoteService(connection)
    source_service = SourceService(connection)

    project = research_service.create_project("AI")

    note = note_service.add_note(project.id, "Remember to verify this.")
    assert note.id is not None

    source = source_service.add_source(
        project.id,
        title="Wikipedia",
        url="https://en.wikipedia.org/wiki/Artificial_intelligence",
    )
    assert source.id is not None

    assert len(note_service.list_notes(project.id)) == 1
    assert len(source_service.list_sources(project.id)) == 1


def test_delete_project_cascades(connection) -> None:
    research_service = ResearchService(connection)
    section_service = SectionService(connection)

    project = research_service.create_project("AI")
    section_service.add_section(project.id, "History")

    research_service.delete_project(project.id)

    assert research_service.get_project(project.id) is None
    assert section_service.list_sections(project.id) == []
    