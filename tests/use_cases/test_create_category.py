"""
Tests for account creator use case
"""

import re

import pytest

import nwtrack.application.use_cases.create_category
from nwtrack.application.use_cases.create_category import CreateCategoryInteractive
from nwtrack.bootstrap.container import Container
from tests.helpers import init_db_tables_w_entities


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""
    from nwtrack.application.ports.db import DBConnectionManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.application.use_cases.create_category import (
        ConsoleFactory,
        FetchService,
    )
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.infra.config.settings import Settings
    from nwtrack.entrypoints.cli.ui.console import ConsoleSettings

    console_defaults = ConsoleSettings(record=True)

    return (
        base_container.register(
            DBAdminService,
            lambda c: DBAdminService(
                c.resolve(Settings), c.resolve(DBConnectionManager)
            ),
        )
        .register(
            ConsoleFactory,
            lambda _: ConsoleFactory(default_settings=console_defaults),
            lifetime=Lifetime.SINGLETON,
        )
        .register(
            FetchService,
            lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            CreateCategoryInteractive,
            lambda c: CreateCategoryInteractive(
                uow=lambda: c.resolve(UnitOfWork),
                fetcher=FetchService(uow=lambda: c.resolve(UnitOfWork)),
                console_factory=c.resolve(ConsoleFactory),
            ),
        )
    )


def test_create_category_run(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    init_db_tables_w_entities(configured_container, sample_entities)

    monkeypatch.setattr(
        nwtrack.application.use_cases.create_category,
        "prompt_for_category_name",
        lambda *args, **kwargs: "new_category_5",
    )
    monkeypatch.setattr(
        nwtrack.application.use_cases.create_category,
        "prompt_for_category_side",
        lambda *args, **kwargs: "asset",
    )
    monkeypatch.setattr(
        nwtrack.application.use_cases.create_category,
        "prompt_to_confirm_action",
        lambda *args, **kwargs: True,
    )

    service: CreateCategoryInteractive = configured_container.resolve(
        CreateCategoryInteractive
    )
    service.run()
    captured_output = service._console.export_text()
    # TODO: Enable assertions through direct database queries instead of output matching
    assert re.search(r"Category 'new_category_5' created successfully", captured_output)
    assert re.search(r"Category name: new_category_5", captured_output)
    assert re.search(r"Category side: asset", captured_output)
