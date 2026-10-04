from pathlib import Path

import pytest

from core.database.connection import create_connection
from core.database.migration_runner import run_migrations
from core.database.repositories.category_repository import CategoryRepository
from core.database.repositories.research_repository import ResearchRepository
from core.database.repositories.section_repository import SectionRepository
from core.database.repositories.note_repository import NoteRepository
from core.database.repositories.source_repository import SourceRepository
from core.models.category import Category
from core.models.research_project import ResearchProject
from core.models.section import Section
from core.models.note import Note
from core.models.source import Source

TIMESTAMP = "2025-01-01T00:00:00Z"


@pytest.fixture
def connection(tmp_path: Path):
    db_path = tmp_path / "test_research.db"
    run_migrations(db_path)
    conn = create_connection(db_path)
    yield conn
    conn.close()


def test_category_crud(connection) -> None:
    repo = CategoryRepository(connection)

    category = Category(
        id=None, name="Science", color="#3498db", position=0,
        created_at=TIMESTAMP, updated_at=TIMESTAMP,
    )
    created = repo.create(category)
    assert created.id is not None

    fetched = repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.name == "Science"

    fetched.name = "Natural Science"
    repo.update(fetched)
    updated = repo.get_by_id(created.id)
    assert updated.name == "Natural Science"

    repo.delete(created.id)
    assert repo.get_by_id(created.id) is None


def test_full_research_project_lifecycle(connection) -> None:
    research_repo = ResearchRepository(connection)
    section_repo = SectionRepository(connection)
    note_repo = NoteRepository(connection)
    source_repo = SourceRepository(connection)

    project = research_repo.create(
        ResearchProject(
            id=None,
            title="Artificial Intelligence",
            description="Overview of artificial intelligence...",
            category_id=None,
            is_favorite=False,
            position=0,
            created_at=TIMESTAMP,
            updated_at=TIMESTAMP,
        )
    )
    assert project.id is not None

    section_titles = [
        "History of Artificial Intelligence",
        "Machine Learning",
        "Neural Networks",
        "Large Language Models",
        "Future Developments",
    ]
    for index, title in enumerate(section_titles):
        section_repo.create(
            Section(
                id=None,
                research_id=project.id,
                title=title,
                content=f"Long information about {title}...",
                position=index,
                created_at=TIMESTAMP,
                updated_at=TIMESTAMP,
            )
        )

    sections = section_repo.list_by_research(project.id)
    assert [s.title for s in sections] == section_titles

    note_repo.create(
        Note(
            id=None,
            research_id=project.id,
            section_id=sections[0].id,
            content="Double check this date with another source.",
            created_at=TIMESTAMP,
            updated_at=TIMESTAMP,
        )
    )
    notes = note_repo.list_by_research(project.id)
    assert len(notes) == 1

    source_repo.create(
        Source(
            id=None,
            research_id=project.id,
            title="Wikipedia - Artificial Intelligence",
            url="https://en.wikipedia.org/wiki/Artificial_intelligence",
            author=None,
            publication_date=None,
            notes="General overview reference.",
            created_at=TIMESTAMP,
            updated_at=TIMESTAMP,
        )
    )
    sources = source_repo.list_by_research(project.id)
    assert len(sources) == 1

    # Deleting the research project must cascade-delete its sections,
    # notes, and sources (enforced by ON DELETE CASCADE in the schema).
    research_repo.delete(project.id)
    assert section_repo.list_by_research(project.id) == []
    assert note_repo.list_by_research(project.id) == []
    assert source_repo.list_by_research(project.id) == []


def test_section_reorder(connection) -> None:
    research_repo = ResearchRepository(connection)
    section_repo = SectionRepository(connection)

    project = research_repo.create(
        ResearchProject(
            id=None, title="Test Project", description="", category_id=None,
            is_favorite=False, position=0, created_at=TIMESTAMP, updated_at=TIMESTAMP,
        )
    )

    first = section_repo.create(
        Section(id=None, research_id=project.id, title="First", content="",
                position=0, created_at=TIMESTAMP, updated_at=TIMESTAMP)
    )
    second = section_repo.create(
        Section(id=None, research_id=project.id, title="Second", content="",
                position=1, created_at=TIMESTAMP, updated_at=TIMESTAMP)
    )

    section_repo.reorder(first.id, 1)
    section_repo.reorder(second.id, 0)

    reordered = section_repo.list_by_research(project.id)
    assert [s.title for s in reordered] == ["Second", "First"]
    