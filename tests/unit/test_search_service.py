from core.services.research_service import ResearchService
from core.services.section_service import SectionService
from core.services.note_service import NoteService
from core.search.search_service import SearchService


def test_search_finds_research_by_title(connection) -> None:
    research_service = ResearchService(connection)
    research_service.create_project("Artificial Intelligence", "Overview of AI")

    search_service = SearchService(connection)
    results = search_service.search("Artificial")

    assert any(r.entity_type == "research" and "Artificial" in r.title for r in results)


def test_search_finds_section_content(connection) -> None:
    research_service = ResearchService(connection)
    section_service = SectionService(connection)

    project = research_service.create_project("AI")
    section_service.add_section(
        project.id, "Neural Networks", "Neural networks are inspired by the brain."
    )

    search_service = SearchService(connection)
    results = search_service.search("brain")

    assert any(r.entity_type == "section" for r in results)


def test_search_finds_notes(connection) -> None:
    research_service = ResearchService(connection)
    note_service = NoteService(connection)

    project = research_service.create_project("AI")
    note_service.add_note(project.id, "Double check the Turing test date.")

    search_service = SearchService(connection)
    results = search_service.search("Turing")

    assert any(r.entity_type == "note" for r in results)


def test_search_returns_empty_for_blank_query(connection) -> None:
    search_service = SearchService(connection)
    assert search_service.search("   ") == []


def test_search_returns_empty_for_no_matches(connection) -> None:
    research_service = ResearchService(connection)
    research_service.create_project("Artificial Intelligence")

    search_service = SearchService(connection)
    results = search_service.search("nonexistentxyz123")
    assert results == []
    