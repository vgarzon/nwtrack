"""Tests for narrow fetch-service account workflow support."""

import pytest
from tests.helpers import init_db_tables_w_entities

from nwtrack.application.dto import AccountStatusScope, AggregationDimension
from nwtrack.application.ports.schema import SchemaManager
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.data_loader import InitDataService
from nwtrack.application.services.db_admin import DBAdminService
from nwtrack.application.services.fetch import FetchService
from nwtrack.bootstrap.container import Container
from nwtrack.domain.models import Institution, Tag
from nwtrack.domain.value_objects import Month
from nwtrack.infra.config.settings import Settings
from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager
from nwtrack.infra.persistence.schema import SchemaManager as SchemaManagerImpl


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register the services needed to initialize test data."""
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
            InitDataService,
            lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
        )
    )


def test_fetch_service_lists_institutions_for_account_workflows(
    configured_container: Container, sample_entities
) -> None:
    """Account workflows should only need institution listing from FetchService."""
    init_db_tables_w_entities(configured_container, sample_entities)
    fetcher = FetchService(uow=lambda: configured_container.resolve(UnitOfWork))

    uow_manager: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow_manager as uow:
        uow.institutions.insert(Institution(name="Chase", description="Primary bank"))
        uow.institutions.insert(Institution(name="Fidelity", description="Brokerage"))

    institutions = fetcher.get_all_institutions()

    assert [institution.name for institution in institutions] == ["Chase", "Fidelity"]


def test_fetch_service_lists_tags_for_account_workflows_in_id_order(
    configured_container: Container, sample_entities
) -> None:
    """Account workflows should get tags in deterministic ID order."""
    init_db_tables_w_entities(configured_container, sample_entities)
    fetcher = FetchService(uow=lambda: configured_container.resolve(UnitOfWork))

    uow_manager: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow_manager as uow:
        uow.tags.insert(Tag(name="core", description="Core holding"))
        uow.tags.insert(Tag(name="liquid", description="Quick access"))

    tags = fetcher.get_all_tags()

    assert [tag.name for tag in tags] == ["core", "liquid"]


def test_fetch_service_get_account_by_id_exposes_assigned_tags(
    configured_container: Container, sample_entities
) -> None:
    """Account workflow reads should expose tags for preview and list rendering."""
    init_db_tables_w_entities(configured_container, sample_entities)
    fetcher = FetchService(uow=lambda: configured_container.resolve(UnitOfWork))

    uow_manager: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow_manager as uow:
        first_tag = uow.tags.insert(Tag(name="core", description="Core holding"))
        second_tag = uow.tags.insert(Tag(name="liquid", description="Quick access"))
        uow.tags.replace_for_account(1, [second_tag, first_tag])

    account = fetcher.get_account_by_id(1)

    assert account is not None
    assert [tag.name for tag in account.tags] == ["core", "liquid"]


def test_fetch_service_get_account_by_name_returns_matching_account(
    configured_container: Container, sample_entities
) -> None:
    """Account-name CLI selection should resolve through FetchService."""
    init_db_tables_w_entities(configured_container, sample_entities)
    fetcher = FetchService(uow=lambda: configured_container.resolve(UnitOfWork))

    account = fetcher.get_account_by_name("bank_1_checking")

    assert account is not None
    assert account.id == 1


def test_fetch_service_get_account_by_name_returns_none_for_unknown_name(
    configured_container: Container, sample_entities
) -> None:
    """Unknown account names should resolve to None rather than raise."""
    init_db_tables_w_entities(configured_container, sample_entities)
    fetcher = FetchService(uow=lambda: configured_container.resolve(UnitOfWork))

    assert fetcher.get_account_by_name("does-not-exist") is None


def test_fetch_service_get_balances_for_account_orders_by_month(
    configured_container: Container, sample_entities
) -> None:
    """Single-account balance history reads should come back ordered by month."""
    init_db_tables_w_entities(configured_container, sample_entities)
    fetcher = FetchService(uow=lambda: configured_container.resolve(UnitOfWork))

    balances = fetcher.get_balances_for_account(1)

    months = [str(balance.month) for balance in balances]
    assert months == sorted(months)
    assert all(balance.account_id == 1 for balance in balances)


def test_fetch_service_lists_available_aggregation_months(
    configured_container: Container, sample_entities
) -> None:
    """Compatibility workflows should be able to list months with shared report data."""
    init_db_tables_w_entities(configured_container, sample_entities)
    fetcher = FetchService(uow=lambda: configured_container.resolve(UnitOfWork))

    months = fetcher.get_available_aggregation_months(
        AggregationDimension.SIDE,
        currency_code="USD",
        status_scope=AccountStatusScope.ACTIVE,
    )

    assert months == sorted(months)
    assert months[0] == Month(2024, 6)
    assert months[-1] == Month(2025, 11)


def test_fetch_service_orders_by_display_order_and_filters_hidden(
    configured_container: Container, sample_entities
) -> None:
    """Accounts and month balances follow display order; hidden ones can be dropped."""
    init_db_tables_w_entities(configured_container, sample_entities)
    fetcher = FetchService(uow=lambda: configured_container.resolve(UnitOfWork))
    month = fetcher.get_recent_months(n_months=1)[0]

    accounts = fetcher.get_accounts(active_only=True)
    first, second = accounts[0], accounts[1]
    uow_manager: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow_manager as uow:
        uow.accounts.move(first.id, 1)  # swap first and second
        uow.accounts.set_hidden(accounts[-1].id, True)

    reordered = fetcher.get_accounts(active_only=True)
    assert [a.id for a in reordered[:2]] == [second.id, first.id]
    assert len(reordered) == len(accounts)

    visible = fetcher.get_accounts(active_only=True, include_hidden=False)
    assert accounts[-1].id not in {a.id for a in visible}

    balances_all = fetcher.get_month_balances(month, active_only=True)
    balances_visible = fetcher.get_month_balances(
        month, active_only=True, include_hidden=False
    )
    assert [b.account.id for b in balances_all[:2]] == [second.id, first.id]
    assert len(balances_visible) == len(balances_all) - 1

    # Hiding is cosmetic: net worth is unchanged by the flag.
    hidden_nw = fetcher.get_networth(month, "USD")
    unhide_manager: UnitOfWork = configured_container.resolve(UnitOfWork)
    with unhide_manager as uow:
        uow.accounts.set_hidden(accounts[-1].id, False)
    assert fetcher.get_networth(month, "USD") == hidden_nw
