"""
Tests for account creator use case
"""

import re

import pytest
from rich.console import Console
from tests.helpers import init_db_tables_w_entities

import nwtrack.entrypoints.cli.adapters.category_presenters
from nwtrack.application.services.fetch import FetchService
from nwtrack.application.use_cases.create_category import CreateCategoryInteractive
from nwtrack.bootstrap.container import Container
from nwtrack.entrypoints.cli.adapters.category_presenters import (
    RichCategoryCreationPresenter,
)


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
            lambda _: Console(record=True),
            lifetime=Lifetime.SINGLETON,
        )
        .register(
            FetchService,
            lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            RichCategoryCreationPresenter,
            lambda c: RichCategoryCreationPresenter(console=c.resolve(Console)),
        )
        .register(
            CreateCategoryInteractive,
            lambda c: CreateCategoryInteractive(
                uow=lambda: c.resolve(UnitOfWork),
                fetcher=c.resolve(FetchService),
                presenter=c.resolve(RichCategoryCreationPresenter),
            ),
        )
    )


def test_create_category_run(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    init_db_tables_w_entities(configured_container, sample_entities)

    # Patch the prompt functions in the presenter module
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.category_presenters,
        "prompt_for_category_name",
        lambda *args, **kwargs: "new_category_5",
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.category_presenters,
        "prompt_for_category_side",
        lambda *args, **kwargs: "asset",
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.category_presenters,
        "prompt_to_confirm_action",
        lambda *args, **kwargs: True,
    )

    service: CreateCategoryInteractive = configured_container.resolve(
        CreateCategoryInteractive
    )
    result = service.run()

    assert result.success
    assert result.data == "new_category_5"

    # Check console output
    console: Console = configured_container.resolve(Console)
    captured_output = console.export_text()
    # TODO: Enable assertions through direct database queries instead of output matching
    assert re.search(r"Category 'new_category_5' created successfully", captured_output)
    assert re.search(r"Category name: new_category_5", captured_output)
    assert re.search(r"Category side: asset", captured_output)
