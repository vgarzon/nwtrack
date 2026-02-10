"""
Tests for list accounts service
"""


import pytest
from tests.helpers import init_db_tables_w_entities

from nwtrack.application.use_cases.list_accounts import (
    FetchService,
    ListAccounts,
)
from nwtrack.bootstrap.container import Container
from nwtrack.domain.models import Account, Category
from nwtrack.infra.config.settings import Settings


class MockAccountListPresenter:
    """Mock presenter for testing that records calls and captures output."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.displayed_accounts: list[Account] = []
        self.displayed_categories: dict[int, Category | None] = {}
        self.active_only_flag: bool = True

    def display_accounts(
        self,
        accounts: list[Account],
        categories: dict[int, Category | None],
        active_only: bool = True,
    ) -> None:
        """Capture display call and store data for assertions."""
        self.calls.append("display_accounts")
        self.displayed_accounts = accounts
        self.displayed_categories = categories
        self.active_only_flag = active_only


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""

    from nwtrack.application.ports.schema import SchemaManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.infra.sqlite.sqlalchemy_manager import SQLAlchemySessionManager
    from nwtrack.infra.sqlite.sqlalchemy_schema_manager import SQLAlchemySchemaManager

    mock_presenter = MockAccountListPresenter()

    return (
        base_container.register(
            SchemaManager,
            lambda c: SQLAlchemySchemaManager(
                engine=c.resolve(SQLAlchemySessionManager).engine
            ),
        ).register(
            DBAdminService,
            lambda c: DBAdminService(c.resolve(Settings), c.resolve(SchemaManager)),
        )
        .register(
            FetchService,
            lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            MockAccountListPresenter,
            lambda _: mock_presenter,
        )
        .register(
            ListAccounts,
            lambda c: ListAccounts(
                fetcher=c.resolve(FetchService),
                presenter=c.resolve(MockAccountListPresenter),
            ),
        )
    )


def test_list_accounts_active_only(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    init_db_tables_w_entities(configured_container, sample_entities)
    service: ListAccounts = configured_container.resolve(ListAccounts)
    mock_presenter: MockAccountListPresenter = configured_container.resolve(
        MockAccountListPresenter
    )

    result = service.run(active_only=True)

    assert result.success
    assert "display_accounts" in mock_presenter.calls
    assert mock_presenter.active_only_flag is True

    # Verify only active accounts are displayed
    account_names = [acc.name for acc in mock_presenter.displayed_accounts]
    assert "credit_cards_1" in account_names
    assert "mortgage_1" not in account_names  # inactive account


def test_list_all_accounts(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    init_db_tables_w_entities(configured_container, sample_entities)
    service: ListAccounts = configured_container.resolve(ListAccounts)
    mock_presenter: MockAccountListPresenter = configured_container.resolve(
        MockAccountListPresenter
    )

    result = service.run(active_only=False)

    assert result.success
    assert "display_accounts" in mock_presenter.calls
    assert mock_presenter.active_only_flag is False

    # Verify all accounts are displayed
    account_names = [acc.name for acc in mock_presenter.displayed_accounts]
    assert "credit_cards_1" in account_names
    assert "mortgage_1" in account_names  # inactive account included
