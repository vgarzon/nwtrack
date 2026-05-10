"""Tests for listing tags."""

import pytest
from tests.helpers import init_db_tables_w_entities

from nwtrack.application.dto import TagListItem
from nwtrack.application.use_cases.list_tags import ListTags
from nwtrack.bootstrap.container import Container
from nwtrack.domain.models import Account, Status, Tag
from nwtrack.infra.config.settings import Settings


class MockTagListPresenter:
    """Mock presenter for testing tag list display."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.displayed_tags: list[TagListItem] = []

    def display_tags(self, tags: list[TagListItem]) -> None:
        self.calls.append("display_tags")
        self.displayed_tags = tags


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""
    from nwtrack.application.ports.schema import SchemaManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager
    from nwtrack.infra.persistence.schema import SchemaManager as SchemaManagerImpl

    mock_presenter = MockTagListPresenter()

    return (
        base_container.register(
            SchemaManager,
            lambda c: SchemaManagerImpl(engine=c.resolve(SQLiteSessionManager).engine),
        )
        .register(
            DBAdminService,
            lambda c: DBAdminService(c.resolve(Settings), c.resolve(SchemaManager)),
        )
        .register(
            MockTagListPresenter,
            lambda _: mock_presenter,
        )
        .register(
            ListTags,
            lambda c: ListTags(
                uow=lambda: c.resolve(UnitOfWork),
                presenter=c.resolve(MockTagListPresenter),
            ),
        )
    )


def test_list_tags_shows_usage_counts(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """Tag list should include linked-account counts."""
    from nwtrack.application.ports.uow import UnitOfWork

    init_db_tables_w_entities(configured_container, sample_entities)
    uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow:
        account_id = uow.accounts.insert(
            Account(
                name="cash_bucket",
                description="Cash bucket",
                category_name="checking",
                currency_code="USD",
                status=Status.ACTIVE,
            )
        )
        tag_id = uow.tags.insert(Tag(name="liquid", description="Quick access"))
        uow.tags.replace_for_account(account_id, [tag_id])

    service: ListTags = configured_container.resolve(ListTags)
    mock_presenter: MockTagListPresenter = configured_container.resolve(
        MockTagListPresenter
    )
    result = service.run()

    assert result.success
    assert "display_tags" in mock_presenter.calls
    assert mock_presenter.displayed_tags[0].tag.name == "liquid"
    assert mock_presenter.displayed_tags[0].account_count == 1
