"""Tests for CategoryService business logic."""
import pytest

from core.services.category_service import CategoryService
from core.services.exceptions import ValidationError


@pytest.fixture
def category_service(connection):
    return CategoryService(connection)


def test_create_category(category_service):
    category = category_service.create_category("Science", color="#FF0000")

    assert category.id is not None
    assert category.name == "Science"
    assert category.color == "#FF0000"


def test_create_category_rejects_empty_name(category_service):
    with pytest.raises(ValidationError):
        category_service.create_category("   ")


def test_rename_category(category_service):
    category = category_service.create_category("History")

    renamed = category_service.rename_category(category.id, "World History")

    assert renamed.name == "World History"


def test_delete_category(category_service):
    category = category_service.create_category("Temporary")

    category_service.delete_category(category.id)

    remaining = category_service.list_categories()
    assert all(c.id != category.id for c in remaining)


def test_list_categories_returns_all_created(category_service):
    category_service.create_category("Alpha")
    category_service.create_category("Beta")

    categories = category_service.list_categories()

    names = [c.name for c in categories]
    assert "Alpha" in names
    assert "Beta" in names
