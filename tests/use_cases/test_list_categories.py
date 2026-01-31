"""
Tests for list categories service
"""

import pytest
from tests.helpers import init_db_tables_w_entities

from nwtrack.application.use_cases.list_categories import (
    FetchService,
    ListCategories,
)
from nwtrack.bootstrap.container import Container
from nwtrack.domain.models import Category
from nwtrack.infra.config.settings import Settings


class MockCategoryListPresenter:
    """Mock presenter for testing that records calls and captures output."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.displayed_categories: list[Category] = []

    def display_categories(self, categories: list[Category]) -> None:
        """Capture display call and store data for assertions."""
        self.calls.append("display_categories")
        self.displayed_categories = categories


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""

    from nwtrack.application.ports.db import DBConnectionManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.db_admin import DBAdminService

    mock_presenter = MockCategoryListPresenter()

    return (
        base_container.register(
            DBAdminService,
            lambda c: DBAdminService(
                c.resolve(Settings), c.resolve(DBConnectionManager)
            ),
        )
        .register(
            FetchService,
            lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            MockCategoryListPresenter,
            lambda _: mock_presenter,
        )
        .register(
            ListCategories,
            lambda c: ListCategories(
                fetcher=c.resolve(FetchService),
                presenter=c.resolve(MockCategoryListPresenter),
            ),
        )
    )


def test_list_categories(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    init_db_tables_w_entities(configured_container, sample_entities)
    service: ListCategories = configured_container.resolve(ListCategories)
    mock_presenter: MockCategoryListPresenter = configured_container.resolve(
        MockCategoryListPresenter
    )

    result = service.run()

    assert result.success
    assert "display_categories" in mock_presenter.calls

    # Verify categories are displayed
    category_names = [cat.name for cat in mock_presenter.displayed_categories]
    assert "checking" in category_names
    assert "revolving_credit" in category_names
