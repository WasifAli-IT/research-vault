from core.services.research_service import ResearchService
from core.services.section_service import SectionService
from core.search.like_fallback_backend import LikeFallbackSearchBackend


def test_like_backend_finds_research_match(connection) -> None:
    research_service = ResearchService(connection)
    research_service.create_project("Artificial Intelligence", "Overview of AI")

    backend = LikeFallbackSearchBackend(connection)
    results = backend.search("Artificial")

    assert any(r.entity_type == "research" for r in results)


def test_like_backend_finds_section_match(connection) -> None:
    research_service = ResearchService(connection)
    section_service = SectionService(connection)

    project = research_service.create_project("AI")
    section_service.add_section(project.id, "Neural Networks", "Inspired by the brain.")

    backend = LikeFallbackSearchBackend(connection)
    results = backend.search("brain")

    assert any(r.entity_type == "section" for r in results)


def test_like_backend_returns_empty_for_no_match(connection) -> None:
    backend = LikeFallbackSearchBackend(connection)
    assert backend.search("nonexistentxyz123") == []
    