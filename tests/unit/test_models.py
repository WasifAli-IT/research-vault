from core.models.category import Category
from core.models.research_project import ResearchProject
from core.models.section import Section
from core.models.note import Note
from core.models.source import Source


def test_category_can_be_constructed() -> None:
    category = Category(
        id=None,
        name="Science",
        color="#3498db",
        position=0,
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )
    assert category.name == "Science"


def test_research_project_can_be_constructed() -> None:
    project = ResearchProject(
        id=None,
        title="Artificial Intelligence",
        description="Overview of AI",
        category_id=None,
        is_favorite=False,
        position=0,
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )
    assert project.title == "Artificial Intelligence"


def test_section_can_be_constructed() -> None:
    section = Section(
        id=None,
        research_id=1,
        title="History of AI",
        content="Long text here...",
        position=0,
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )
    assert section.title == "History of AI"


def test_note_can_be_constructed() -> None:
    note = Note(
        id=None,
        research_id=1,
        section_id=None,
        content="Remember to check this later",
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )
    assert note.content.startswith("Remember")


def test_source_can_be_constructed() -> None:
    source = Source(
        id=None,
        research_id=1,
        title="Wikipedia - AI",
        url="https://en.wikipedia.org/wiki/Artificial_intelligence",
        author=None,
        publication_date=None,
        notes="",
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )
    assert source.url is not None
    