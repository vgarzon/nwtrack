"""Tests for narrow fetch-service account workflow support."""

import pytest
from tests.helpers import init_db_tables_w_entities

from nwtrack.application.ports.schema import SchemaManager
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.data_loader import InitDataService
from nwtrack.application.services.db_admin import DBAdminService
from nwtrack.application.services.fetch import FetchService
from nwtrack.bootstrap.container import Container
from nwtrack.domain.models import Institution, Tag
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
    """Account workflows should be able to list institutions for selection."""
    init_db_tables_w_entities(configured_container, sample_entities)
    fetcher = FetchService(uow=lambda: configured_container.resolve(UnitOfWork))

    uow_manager: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow_manager as uow:
        uow.institutions.insert(Institution(name="Chase", description="Primary bank"))
        uow.institutions.insert(Institution(name="Fidelity", description="Brokerage"))

    institutions = fetcher.get_all_institutions()

    assert [institution.name for institution in institutions] == ["Chase", "Fidelity"]


def test_fetch_service_lists_tags_for_account_workflows(
    configured_container: Container, sample_entities
) -> None:
    """Account workflows should be able to list tags for selection."""
    init_db_tables_w_entities(configured_container, sample_entities)
    fetcher = FetchService(uow=lambda: configured_container.resolve(UnitOfWork))

    uow_manager: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow_manager as uow:
        uow.tags.insert(Tag(name="liquid", description="Quick access"))
        uow.tags.insert(Tag(name="core", description="Core holding"))

    tags = fetcher.get_all_tags()

    assert [tag.name for tag in tags] == ["liquid", "core"]


def test_fetch_service_populates_tags_for_account_by_id(
    configured_container: Container, sample_entities
) -> None:
    """Account update reads should include assigned tags for defaults."""
    init_db_tables_w_entities(configured_container, sample_entities)
    fetcher = FetchService(uow=lambda: configured_container.resolve(UnitOfWork))

    uow_manager: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow_manager as uow:
        liquid_id = uow.tags.insert(Tag(name="liquid", description="Quick access"))
        core_id = uow.tags.insert(Tag(name="core", description="Core holding"))
        uow.tags.replace_for_account(1, [core_id, liquid_id])

    account = fetcher.get_account_by_id(1)
    direct_tags = fetcher.get_tags_for_account(1)

    assert account is not None
    assert [tag.name for tag in account.tags] == ["liquid", "core"]
    assert [tag.name for tag in direct_tags] == ["liquid", "core"]


def test_fetch_service_populates_tags_for_account_lists(
    configured_container: Container, sample_entities
) -> None:
    """Account list reads should include assigned tags for presentation."""
    init_db_tables_w_entities(configured_container, sample_entities)
    fetcher = FetchService(uow=lambda: configured_container.resolve(UnitOfWork))

    uow_manager: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow_manager as uow:
        liquid_id = uow.tags.insert(Tag(name="liquid", description="Quick access"))
        uow.tags.replace_for_account(1, [liquid_id])

    accounts = fetcher.get_accounts(active_only=False)
    tagged_account = next(account for account in accounts if account.id == 1)

    assert [tag.name for tag in tagged_account.tags] == ["liquid"]
