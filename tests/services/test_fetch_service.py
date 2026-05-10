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
