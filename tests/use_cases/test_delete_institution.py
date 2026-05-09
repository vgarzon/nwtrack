"""Tests for institution delete use case."""

import re

import pytest
from rich.console import Console
from tests.helpers import init_db_tables_w_entities

import nwtrack.entrypoints.cli.adapters.institution_presenters
from nwtrack.application.use_cases.delete_institution import (
    DeleteInstitutionInteractive,
)
from nwtrack.bootstrap.container import Container
from nwtrack.entrypoints.cli.adapters.institution_presenters import (
    RichInstitutionDeletePresenter,
)
from nwtrack.entrypoints.cli.ui.console import ConsoleSettings, build_console


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""
    from nwtrack.application.ports.schema import SchemaManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.infra.config.settings import Settings
    from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager
    from nwtrack.infra.persistence.schema import SchemaManager as SchemaManagerImpl

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
            Console,
            lambda _: build_console(ConsoleSettings(record=True)),
            lifetime=Lifetime.SINGLETON,
        )
        .register(
            RichInstitutionDeletePresenter,
            lambda c: RichInstitutionDeletePresenter(console=c.resolve(Console)),
        )
        .register(
            DeleteInstitutionInteractive,
            lambda c: DeleteInstitutionInteractive(
                uow=lambda: c.resolve(UnitOfWork),
                presenter=c.resolve(RichInstitutionDeletePresenter),
            ),
        )
    )


def test_delete_institution_run(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Institution delete workflow should succeed when no accounts are linked."""
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.domain.models import Institution

    init_db_tables_w_entities(configured_container, sample_entities)
    uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow:
        uow.institutions.insert(Institution(name="Chase", description="Primary bank"))

    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.institution_presenters,
        "prompt_for_institution_id",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.institution_presenters.Confirm,
        "ask",
        lambda *args, **kwargs: True,
    )

    service: DeleteInstitutionInteractive = configured_container.resolve(
        DeleteInstitutionInteractive
    )
    result = service.run()

    assert result.success
    console: Console = configured_container.resolve(Console)
    captured_output = console.export_text()
    assert re.search(r"Institution deleted successfully", captured_output)
